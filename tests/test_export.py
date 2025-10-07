from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pytest
from molmass import Formula

from app.database import LipidDB, LipidSpecies
from app.dataprocess import ImageType, SampleCollection
from app.export import CardinalExportError, export_cardinal_hdf5


class DummySection:
    def __init__(self, images: dict[str, np.ndarray]):
        self.quant = images
        self.isotope = images
        self.raw = images
        first_image = next(iter(images.values()))
        self._shape = first_image.shape
        self.coordinates = np.array(
            [
                [1, 1, 1],
                [2, 1, 1],
                [1, 2, 1],
                [2, 2, 1],
            ],
            dtype=np.int32,
        )

    @property
    def shape(self) -> tuple[int, int]:
        return self._shape


@pytest.fixture()
def sample_collection() -> SampleCollection:
    images = {
        "A [M+H]+": np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
        "B [M+H]+": np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32),
    }
    section = DummySection(images)
    return SampleCollection({"sample": section})


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

        intensity = h5["spectraData"]["intensity"][:]
        np.testing.assert_array_equal(intensity[0], np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32))
        np.testing.assert_array_equal(intensity[1], np.array([5.0, 6.0, 7.0, 8.0], dtype=np.float32))

        pixel_group = h5["pixelData"]
        assert set(pixel_group.attrs["columns"]) == {
            "pixel_index",
            "x",
            "y",
            "sample_index",
            "run",
            "sample_id",
        }
        assert pixel_group["pixel_index"].shape[0] == 4

        feature_group = h5["featureData"]
        mz_values = feature_group["mz"][:]
        np.testing.assert_allclose(mz_values, np.array([100.0, 200.0], dtype=np.float32))
        assert feature_group["is_standard"].dtype == np.bool_

        sample_group = h5["samples"]["1"]
        assert sample_group.attrs["sample_id"] == "sample"
        assert sample_group.attrs["n_pixels"] == 4


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
