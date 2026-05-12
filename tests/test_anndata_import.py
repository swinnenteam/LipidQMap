import os
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import anndata as ad
import numpy as np
import numpy.testing as nptest
import pytest
from PySide6.QtWidgets import QApplication, QComboBox

from app.config import Config
from app.database import LipidDB
from app.dataprocess import (
    AnnDataMatrixChoice,
    SampleCollection,
    SampleIonMode,
    get_anndata_matrix_choices,
    load_database_anndata_collection,
)
from app.views.anndata_import_window import AnndataImportWindow


@pytest.fixture
def anndata_config() -> Config:
    mock = Mock(spec=Config)
    mock.settings = SimpleNamespace(
        processing_settings=SimpleNamespace(
            ppm=15.0,
            bin_size=5.0,
            na_isotope_correction=False,
            db_isotope_correction=False,
            imputation=True,
        ),
        selection_settings=SimpleNamespace(minimum_intensity=1, minimum_pixels=1),
        filter_settings=SimpleNamespace(
            raw_image_winsorizing_percentile=99.0,
            quant_image_winsorizing_percentile=99.0,
        ),
    )
    return mock


def _load_example(choice: AnnDataMatrixChoice, config: Config) -> tuple[LipidDB, SampleCollection]:
    return load_database_anndata_collection(
        progress_file_callback=Mock(),
        progress_overall_callback=Mock(),
        database_path="tests/database/test_database.xlsx",
        anndata_path="tests/data/example_anndata.h5ad",
        matrix_choice=choice,
        config=config,
    )


def test_get_anndata_matrix_choices_detects_batch_layer() -> None:
    choices = get_anndata_matrix_choices("tests/data/example_anndata.h5ad")

    assert choices == [AnnDataMatrixChoice.raw, AnnDataMatrixChoice.batch_corrected]


def test_anndata_import_window_populates_matrix_dropdown() -> None:
    app = QApplication.instance() or QApplication([])
    _ = app
    window = SimpleNamespace(matrix_combo_box=QComboBox())

    AnndataImportWindow._populate_matrix_choices(
        window, [AnnDataMatrixChoice.raw, AnnDataMatrixChoice.batch_corrected]
    )

    assert window.matrix_combo_box.count() == 2
    assert window.matrix_combo_box.itemText(0) == "Raw"
    assert window.matrix_combo_box.itemData(1) == AnnDataMatrixChoice.batch_corrected.value


def test_load_anndata_raw_layer_splits_samples_and_masks_background(anndata_config) -> None:
    database, sample_collection = _load_example(AnnDataMatrixChoice.raw, anndata_config)

    assert isinstance(database, LipidDB)
    assert isinstance(sample_collection, SampleCollection)
    assert set(sample_collection.samples) == {"sample_A", "sample_B"}
    assert "PC 32:0 [M+H]+" in database.species
    assert "PE 32:1 [M-H]-" in database.species
    assert "PC 38:4 [M+H]+" not in database.species
    assert any(species.endswith("(+)") for species in database.index)
    assert any(species.endswith("(-)") for species in database.index)

    sample_a = sample_collection.samples["sample_A"]
    assert sample_a.ion_mode == SampleIonMode.combined
    nptest.assert_allclose(
        sample_a.raw["PC 32:0 [M+H]+"],
        np.array([[1.0, 2.0], [3.0, np.nan]], dtype=np.float32),
        equal_nan=True,
    )
    assert sample_a.pixel_size_um == (50.0, 50.0)
    assert (
        sample_a.get_average_spectrum_for_mode(database.species["PC 32:0 [M+H]+"].ion_mode).shape[1]
        > 0
    )


def test_load_anndata_batch_corrected_matrix(anndata_config) -> None:
    _, sample_collection = _load_example(AnnDataMatrixChoice.batch_corrected, anndata_config)

    sample_b = sample_collection.samples["sample_B"]
    nptest.assert_allclose(
        sample_b.raw["PC 32:0 [M+H]+"],
        np.array([[105.0, np.nan], [107.0, 108.0]], dtype=np.float32),
        equal_nan=True,
    )


def test_load_anndata_raw_choice_falls_back_to_x_without_raw_layer(
    tmp_path, anndata_config
) -> None:
    adata = ad.read_h5ad("tests/data/example_anndata.h5ad")
    del adata.layers["raw"]
    fallback_path = tmp_path / "fallback.h5ad"
    adata.write_h5ad(fallback_path)

    _, sample_collection = load_database_anndata_collection(
        progress_file_callback=Mock(),
        progress_overall_callback=Mock(),
        database_path="tests/database/test_database.xlsx",
        anndata_path=str(fallback_path),
        matrix_choice=AnnDataMatrixChoice.raw,
        config=anndata_config,
    )

    sample_a = sample_collection.samples["sample_A"]
    nptest.assert_allclose(
        sample_a.raw["PC 32:0 [M+H]+"],
        np.array([[0.1, 0.2], [0.3, np.nan]], dtype=np.float32),
        equal_nan=True,
    )


def test_load_anndata_rejects_duplicate_spatial_coordinates(tmp_path, anndata_config) -> None:
    adata = ad.read_h5ad("tests/data/example_anndata.h5ad")
    adata.obsm["spatial"][1] = adata.obsm["spatial"][0]
    duplicate_path = tmp_path / "duplicate.h5ad"
    adata.write_h5ad(duplicate_path)

    with pytest.raises(ValueError, match="duplicate spatial coordinates"):
        load_database_anndata_collection(
            progress_file_callback=Mock(),
            progress_overall_callback=Mock(),
            database_path="tests/database/test_database.xlsx",
            anndata_path=str(duplicate_path),
            matrix_choice=AnnDataMatrixChoice.raw,
            config=anndata_config,
        )
