from __future__ import annotations

from pathlib import Path
from typing import cast

import h5py
import numpy as np
import pytest
from molmass import Formula

from app.database import LipidDB, LipidSpecies
from app.dataprocess import ImageType, SampleCollection, SectionMsiImage
from app.export import CardinalExportError, export_cardinal_hdf5


class DummySection:
    def __init__(
        self, images: dict[str, np.ndarray], pixel_size_um: tuple[float, float] | None = None
    ):
        self.quant = images
        self.isotope = images
        self.raw = images
        first_image = next(iter(images.values()))
        self._shape: tuple[int, int] = cast(tuple[int, int], first_image.shape)
        self.coordinates = np.array(
            [
                [1, 1, 1],
                [2, 1, 1],
                [1, 2, 1],
                [2, 2, 1],
            ],
            dtype=np.int32,
        )
        self.pixel_size_um = pixel_size_um

    @property
    def shape(self) -> tuple[int, int]:
        return self._shape


@pytest.fixture()
def sample_collection() -> SampleCollection:
    images = {
        "A [M+H]+": np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        "B [M+H]+": np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32),
    }
    section = DummySection(images, pixel_size_um=(45.0, 50.0))
    samples = cast(dict[str, SectionMsiImage], {"sample": cast(SectionMsiImage, section)})
    return SampleCollection(samples)


@pytest.fixture()
def database() -> LipidDB:
    species = {
        "A [M+H]+": LipidSpecies(
            id="A",
            adduct="[M+H]+",
            lipid_class="ClassA",
            neutral_formula=Formula("CH4"),
            formula=Formula("CH5"),
            mz=100.0,
            m2_isotope=None,
            m2_rel_abundance=0.0,
            m4_isotope=None,
            m4_rel_abundance=0.0,
            na_isotope=None,
            standard=None,
        ),
        "B [M+H]+": LipidSpecies(
            id="B",
            adduct="[M+H]+",
            lipid_class="ClassB",
            neutral_formula=Formula("C2H6"),
            formula=Formula("C2H7"),
            mz=200.0,
            m2_isotope=None,
            m2_rel_abundance=0.0,
            m4_isotope=None,
            m4_rel_abundance=0.0,
            na_isotope=None,
            standard=None,
        ),
    }
    return LipidDB(species)


@pytest.fixture()
def output_path(tmp_path: Path) -> Path:
    return tmp_path / "cardinal_export.h5"


def test_export_cardinal_hdf5_writes_expected_structure(
    sample_collection: SampleCollection,
    database: LipidDB,
    output_path: Path,
) -> None:
    species_ids = ["A [M+H]+", "B [M+H]+"]

    written_path = export_cardinal_hdf5(
        output_path,
        samples=sample_collection,
        database=database,
        species_ids=species_ids,
        image_type=ImageType.quant,
    )

    assert written_path.exists()

    with h5py.File(written_path, "r") as h5:
        assert h5.attrs["format"] == "Cardinal::HDF5"
        assert h5.attrs["image_type"] == ImageType.quant.value

        spectra_group = cast(h5py.Group, h5["spectraData"])
        intensity_dataset = cast(h5py.Dataset, spectra_group["intensity"])
        intensity = intensity_dataset[:]
        assert intensity.shape == (2, 4)
        np.testing.assert_array_equal(
            intensity[0], np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        )
        np.testing.assert_array_equal(
            intensity[1], np.array([5.0, 6.0, 7.0, 8.0], dtype=np.float32)
        )
        layout_attr = intensity_dataset.attrs["layout"]
        if isinstance(layout_attr, bytes):
            layout_attr = layout_attr.decode()
        assert layout_attr == "feature_by_pixel"
        feature_dim = intensity_dataset.dims[0]
        assert len(feature_dim) == 1
        feature_scale = feature_dim[0]
        feature_scale_name = getattr(feature_scale, "name", feature_scale)
        assert isinstance(feature_scale_name, str)
        assert feature_scale_name.endswith("/featureData/feature_id")
        assert intensity_dataset.dims[0].label == "feature_id"
        pixel_dim = intensity_dataset.dims[1]
        assert len(pixel_dim) == 1
        pixel_scale = pixel_dim[0]
        pixel_scale_name = getattr(pixel_scale, "name", pixel_scale)
        assert isinstance(pixel_scale_name, str)
        assert pixel_scale_name.endswith("/pixelData/pixel_index")
        assert intensity_dataset.dims[1].label == "pixel_index"
        pixel_group = cast(h5py.Group, h5["pixelData"])
        columns_attr = pixel_group.attrs["columns"]
        columns_array = cast(np.ndarray, columns_attr)
        columns: set[str] = set()
        for column in columns_array.tolist():
            if isinstance(column, bytes):
                columns.add(column.decode())
            else:
                columns.add(str(column))
        assert columns == {
            "pixel_index",
            "x",
            "y",
            "sample_index",
            "run",
            "sample_id",
        }
        pixel_index_dataset = cast(h5py.Dataset, pixel_group["pixel_index"])
        np.testing.assert_array_equal(
            np.asarray(pixel_index_dataset[:], dtype=np.int64),
            np.array([1, 2, 3, 4], dtype=np.int64),
        )
        coord_dataset = cast(h5py.Dataset, pixel_group["coord"])
        assert coord_dataset.shape == (4, 2)
        np.testing.assert_array_equal(
            coord_dataset[:, 0],
            pixel_group["x"][:],
        )
        np.testing.assert_array_equal(
            coord_dataset[:, 1],
            pixel_group["y"][:],
        )
        coord_columns_attr = coord_dataset.attrs["columns"]
        coord_columns_array = cast(np.ndarray, coord_columns_attr)
        coord_columns: set[str] = set()
        for column in coord_columns_array.tolist():
            if isinstance(column, bytes):
                coord_columns.add(column.decode())
            else:
                coord_columns.add(str(column))
        assert coord_columns == {"x", "y"}
        coord_pixel_dim = coord_dataset.dims[0]
        assert len(coord_pixel_dim) == 1
        coord_pixel_scale = coord_pixel_dim[0]
        coord_pixel_scale_name = getattr(coord_pixel_scale, "name", coord_pixel_scale)
        assert isinstance(coord_pixel_scale_name, str)
        assert coord_pixel_scale_name.endswith("/pixelData/pixel_index")
        assert coord_dataset.dims[0].label == "pixel_index"

        feature_group = cast(h5py.Group, h5["featureData"])
        feature_ids_dataset = cast(h5py.Dataset, feature_group["feature_id"])
        feature_ids = [
            fid.decode() if isinstance(fid, bytes) else str(fid) for fid in feature_ids_dataset[:]
        ]
        assert feature_ids == ["A [M+H]+", "B [M+H]+"]
        mz_dataset = cast(h5py.Dataset, feature_group["mz"])
        mz_values = np.asarray(mz_dataset[:], dtype=np.float32)
        np.testing.assert_allclose(mz_values, np.array([100.0, 200.0], dtype=np.float32))
        is_standard_dataset = cast(h5py.Dataset, feature_group["is_standard"])
        assert is_standard_dataset.dtype == np.bool_

        samples_group = cast(h5py.Group, h5["samples"])
        sample_group = cast(h5py.Group, samples_group["1"])
        assert sample_group.attrs["sample_id"] == "sample"
        assert sample_group.attrs["n_pixels"] == 4
        assert sample_group.attrs["pixel_size_um_x"] == pytest.approx(45.0)
        assert sample_group.attrs["pixel_size_um_y"] == pytest.approx(50.0)


def test_export_cardinal_hdf5_requires_species(
    sample_collection: SampleCollection,
    database: LipidDB,
    output_path: Path,
) -> None:
    with pytest.raises(CardinalExportError):
        export_cardinal_hdf5(
            output_path,
            samples=sample_collection,
            database=database,
            species_ids=[],
        )
