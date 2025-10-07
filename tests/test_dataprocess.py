from unittest.mock import Mock

import numpy as np
import numpy.testing as nptest
import numpy.typing as npt
import pytest

from app.config import Config, Configuration, FilterSettings, ProcessingSettings, SelectionSettings
from app.database import DatabaseFactory, IonMode, LipidDB
from app.dataprocess import (
    ImageType,
    SampleCollection,
    SectionMsiImage,
    _add_padding,
    db_isotope_correction,
    load_database_image_collection,
    na_isotope_correction,
    ppm_to_tolerance,
    replace_nan_with_median,
    threshold_check,
    winsorize_image,
)


@pytest.fixture(name="database")
def fixture_database() -> LipidDB:
    database = DatabaseFactory(
        "tests/database/test_database.xlsx", ion_mode=IonMode.positive
    ).create_database()
    return database


@pytest.fixture(name="nan_image")
def fixture_nan_image() -> npt.NDArray:
    return np.array([[10.0, 12.0, np.nan], [14.0, np.nan, 12.0], [11.0, 6.0, 8.0]])


@pytest.fixture(name="image")
def fixture_image() -> npt.NDArray:
    return np.array([[10.0, 12.0, 15.0], [14.0, 12.0, 12.0], [11.0, 6.0, 8.0]])


@pytest.fixture(name="images")
def fixture_images() -> dict[str, npt.NDArray]:
    return {
        "PC 33:1 d7 [M+H]+": np.array([[80], [1200]]),
        "PC 32:0 [M+H]+": np.array([[85], [1275]]),
        "PC 32:1 [M+H]+": np.array([[90], [1350]]),
        "PC 34:1 [M+H]+": np.array([[65], [975]]),
        "PC 36:1 [M+H]+": np.array([[50], [750]]),
        "PC 32:2 [M+H]+": np.array([[95], [1425]]),
        "PC 34:2 [M+H]+": np.array([[70], [1050]]),
        "PC 36:2 [M+H]+": np.array([[55], [825]]),
        "PC 32:4 [M+H]+": np.array([[100], [1500]]),
        "PC 34:4 [M+H]+": np.array([[75], [1125]]),
        "PC 36:4 [M+H]+": np.array([[60], [900]]),
        "PC 38:4 [M+H]+": np.array([[45], [675]]),
        "PC 33:1 d7 [M+Na]+": np.array([[40], [600]]),
        "PC 32:0 [M+Na]+": np.array([[35], [525]]),
        "PC 32:1 [M+Na]+": np.array([[30], [450]]),
        "PC 34:1 [M+Na]+": np.array([[55], [825]]),
        "PC 36:1 [M+Na]+": np.array([[70], [1050]]),
        "PC 32:2 [M+Na]+": np.array([[25], [375]]),
        "PC 34:2 [M+Na]+": np.array([[50], [750]]),
        "PC 36:2 [M+Na]+": np.array([[65], [975]]),
        "PC 32:4 [M+Na]+": np.array([[20], [300]]),
        "PC 34:4 [M+Na]+": np.array([[45], [675]]),
        "PC 36:4 [M+Na]+": np.array([[60], [900]]),
        "PC 38:4 [M+Na]+": np.array([[75], [1125]]),
    }


@pytest.fixture
def mock_config() -> Config:
    """Fixture for a mock Config object."""
    mock = Mock(spec=Config)

    # Create individual mocks for each nested settings class
    mock_processing_settings = Mock(spec=ProcessingSettings)
    mock_selection_settings = Mock(spec=SelectionSettings)
    mock_filter_settings = Mock(spec=FilterSettings)

    # Set up the attributes on the processing settings mock
    mock_processing_settings.calibration_ppm = 30.0
    mock_processing_settings.pos_calibrant = 798.5410
    mock_processing_settings.neg_calibrant = 798.5410
    mock_processing_settings.calibration_min_intensity = 10000
    mock_processing_settings.online_calibration = True
    mock_processing_settings.ppm = 15.0
    mock_processing_settings.bin_size = 5.0
    mock_processing_settings.na_isotope_correction = True
    mock_processing_settings.db_isotope_correction = True
    mock_processing_settings.imputation = True

    # Set up the attributes on the selection settings mock
    mock_selection_settings.minimum_intensity = 1000
    mock_selection_settings.minimum_pixels = 100

    # Set up the attributes on the filter settings mock
    mock_filter_settings.raw_image_winsorizing_percentile = 99.0
    mock_filter_settings.quant_image_winsorizing_percentile = 99.0

    # Create a mock Configuration and assign the nested mocks
    mock_settings = Mock(spec=Configuration)
    mock_settings.processing_settings = mock_processing_settings
    mock_settings.selection_settings = mock_selection_settings
    mock_settings.filter_settings = mock_filter_settings

    # Assign the mock settings to the Config mock
    mock.settings = mock_settings

    return mock


@pytest.fixture
def section_msi_image(mock_config, database) -> SectionMsiImage:
    """Fixture for initializing a SectionMsiImage object."""
    return SectionMsiImage(
        progress_file_callback=Mock(),
        database=database,
        imzml_path="tests/data/example.imzML",
        ion_mode=IonMode.positive,
        config=mock_config,
    )


def test_load_data(section_msi_image) -> None:
    """Test load_data method."""
    assert section_msi_image.raw is not None
    assert section_msi_image.isotope is not None
    assert section_msi_image.quant is not None
    assert section_msi_image.average_spectrum is not None


def test_image_shape(section_msi_image) -> None:
    """Test shape if the image."""
    assert section_msi_image.shape == (3, 3)


def test_get_image(section_msi_image) -> None:
    """Test the get method."""
    image = section_msi_image.get(ImageType.raw, "PC 32:0 [M+H]+")
    assert isinstance(image, np.ndarray)

    image = section_msi_image.get(ImageType.isotope, "PC 32:0 [M+H]+")
    assert isinstance(image, np.ndarray)

    image = section_msi_image.get(ImageType.quant, "PC 32:0 [M+H]+")
    assert isinstance(image, np.ndarray)


def test_get_mean(section_msi_image) -> None:
    """Test the get_mean method."""
    mean = section_msi_image.get_mean(ImageType.raw, "PC 32:0 [M+H]+")
    assert isinstance(mean, (int, float))
    mean = section_msi_image.get_mean(ImageType.isotope, "PC 32:0 [M+H]+")
    assert isinstance(mean, (int, float))
    mean = section_msi_image.get_mean(ImageType.quant, "PC 32:0 [M+H]+")
    assert isinstance(mean, (int, float))

    mean = section_msi_image.get_mean(ImageType.raw, "not_present_id")
    assert mean == 0
    mean = section_msi_image.get_mean(ImageType.isotope, "not_present_id")
    assert mean == 0
    mean = section_msi_image.get_mean(ImageType.quant, "not_present_id")
    assert mean == 0


def test_transform(section_msi_image) -> None:
    """Test the transform method."""
    section_msi_image.transform("rotate_left")
    section_msi_image.transform("rotate_right")
    section_msi_image.transform("reflect_horizontal")
    section_msi_image.transform("reflect_vertical")
    section_msi_image.transform("unimplemented")

    assert isinstance(section_msi_image.raw, dict)
    assert isinstance(section_msi_image.isotope, dict)
    assert isinstance(section_msi_image.quant, dict)


def test_criteria_check(section_msi_image) -> None:
    """Test the criteria_check method."""
    checks = section_msi_image.criteria_check()
    assert isinstance(checks, list)
    assert all(isinstance(check, bool) for check in checks)


def test_threshold_check(image) -> None:
    """Test the threshold_check method."""
    np.array([[10.0, 12.0, 15.0], [14.0, 12.0, 12.0], [11.0, 6.0, 8.0]])
    assert threshold_check(image=image, min_intensity=10, min_pixels=5)
    assert not threshold_check(image=image, min_intensity=15, min_pixels=2)


def test_sample_collection(mock_config, database) -> None:
    """Test SampleCollection methods."""
    sample = SectionMsiImage(
        progress_file_callback=Mock(),
        database=database,
        imzml_path="tests/data/example.imzML",
        ion_mode=IonMode.positive,
        config=mock_config,
    )

    sample_collection = SampleCollection(samples={"sample_1": sample})

    # test __len__ method
    assert len(sample_collection) == 1

    # test __getitem__ method
    assert (sample_collection["sample_1"]) == sample

    # test __iter__ method
    assert next(iter(sample_collection)) == "sample_1"

    # test items method
    assert len(sample_collection.items()) == 1

    # test dimensions
    assert sample_collection.dimensions() == [(3, 3)]

    # test get_spectrum
    spectrum = sample_collection.get_spectrum("sample_1")
    assert isinstance(spectrum, np.ndarray)

    # test get_max_intensity
    max_intensity = sample_collection.get_max_intensity(ImageType.raw, "species_1")
    assert isinstance(max_intensity, (int, type(None)))

    # test criteria_check
    criteria = sample_collection.criteria_check()
    assert isinstance(criteria, list)
    assert all(isinstance(criterion, bool) for criterion in criteria)


def test_sample_collection_no_isotope_no_quant(mock_config, database) -> None:
    """Test SampleCollection methods."""
    mock_config.settings.processing_settings.db_isotope_correction = False
    mock_config.settings.processing_settings.na_isotope_correction = False

    sample = SectionMsiImage(
        progress_file_callback=Mock(),
        database=database,
        imzml_path="tests/data/example.imzML",
        ion_mode=IonMode.positive,
        config=mock_config,
    )
    raw = sample.get(image_type=ImageType.raw, species_id="PC 34:1 [M+H]+")
    assert raw is not None
    iso = sample.get(image_type=ImageType.isotope, species_id="PC 34:1 [M+H]+")
    assert iso is None


def test_sample_collection_db_isotope_no_na_isotope(mock_config, database) -> None:
    """Test SampleCollection methods."""
    mock_config.settings.processing_settings.db_isotope_correction = True
    mock_config.settings.processing_settings.na_isotope_correction = False

    sample = SectionMsiImage(
        progress_file_callback=Mock(),
        database=database,
        imzml_path="tests/data/example.imzML",
        ion_mode=IonMode.positive,
        config=mock_config,
    )
    raw = sample.get(image_type=ImageType.raw, species_id="PC 34:1 [M+H]+")
    assert raw is not None
    iso = sample.get(image_type=ImageType.isotope, species_id="PC 34:1 [M+H]+")
    assert iso is not None


def test_load_database_image_collection(mock_config) -> None:
    """Test for the load_database_image_collection function."""
    progress_file_callback, progress_overall_callback = Mock(), Mock()

    # Setup test data
    database_path = "tests/database/test_database.xlsx"
    ion_mode = IonMode.positive
    imzml_paths = ["tests/data/example.imzML"]

    # Run the function under test
    database, sample_collection = load_database_image_collection(
        progress_file_callback=progress_file_callback,
        progress_overall_callback=progress_overall_callback,
        database_path=database_path,
        ion_mode=ion_mode,
        imzml_paths=imzml_paths,
        config=mock_config,
    )

    # Assertions
    assert isinstance(database, LipidDB)
    assert isinstance(sample_collection, SampleCollection)
    assert len(sample_collection.samples) == len(imzml_paths)


def test_add_padding() -> None:
    nptest.assert_array_equal(
        _add_padding(
            np.array(
                [
                    [1],
                ]
            ),
            pad_width=1,
        ),
        np.array([[np.nan, np.nan, np.nan], [np.nan, 1, np.nan], [np.nan, np.nan, np.nan]]),
        strict=True,
    )


def test_winsorize_image(image: npt.NDArray) -> None:
    win_image = winsorize_image(image, upper_percentile=99)
    assert win_image is not None
    nptest.assert_array_equal(
        win_image,
        np.array([[10.0, 12.0, 14.92], [14.0, 12.0, 12.0], [11.0, 6.0, 8.0]]),
        strict=True,
    )


def test_winsorize_image_none() -> None:
    assert winsorize_image(None, upper_percentile=99) is None


def test_winsorize_image_nan(nan_image: npt.NDArray) -> None:
    win_image = winsorize_image(nan_image, upper_percentile=99)
    assert win_image is not None
    nptest.assert_allclose(
        win_image,
        np.array([[10.0, 12.0, np.nan], [13.88, np.nan, 12.0], [11.0, 6.0, 8.0]]),
    )


def test_replace_nan_with_median(nan_image: npt.NDArray) -> None:
    median_filled_image = replace_nan_with_median(nan_image)
    nptest.assert_allclose(
        median_filled_image,
        np.array([[10.0, 12.0, 12.0], [14.0, 11.0, 12.0], [11.0, 6.0, 8.0]]),
    )


def test_replace_nan_with_median_zero_block() -> None:
    zero_block = np.zeros((3, 3))
    median_filled_image = replace_nan_with_median(zero_block)
    nptest.assert_allclose(median_filled_image, zero_block)


def test_replace_nan_with_median_nan_block() -> None:
    nan_block = np.full((3, 3), np.nan)
    median_filled_image = replace_nan_with_median(nan_block)
    assert np.isnan(median_filled_image).all()


def test_ppm_to_tolerance() -> None:
    assert pytest.approx(0.008, rel=1e-6) == ppm_to_tolerance(ppm=10, mz=800)


def test_db_isotope_correction(database: LipidDB, images: dict[str, npt.NDArray]) -> None:
    result = db_isotope_correction(database=database, images=images)
    expected_output = {
        "PC 33:1 d7 [M+H]+": np.array([[80], [1200]]),
        "PC 32:0 [M+H]+": np.array([[75.62796874], [1134.419531]]),
        "PC 32:1 [M+H]+": np.array([[79.11985272], [1186.797791]]),
        "PC 34:1 [M+H]+": np.array([[56.28108146], [844.216222]]),
        "PC 36:1 [M+H]+": np.array([[42.57103302], [638.5654953]]),
        "PC 32:2 [M+H]+": np.array([[95], [1425]]),
        "PC 34:2 [M+H]+": np.array([[70], [1050]]),
        "PC 36:2 [M+H]+": np.array([[55], [825]]),
        "PC 32:4 [M+H]+": np.array([[100], [1500]]),
        "PC 34:4 [M+H]+": np.array([[75], [1125]]),
        "PC 36:4 [M+H]+": np.array([[60], [900]]),
        "PC 38:4 [M+H]+": np.array([[45], [675]]),
        "PC 33:1 d7 [M+Na]+": np.array([[40], [600]]),
        "PC 32:0 [M+Na]+": np.array([[31.811004], [477.165057]]),
        "PC 32:1 [M+Na]+": np.array([[27.1380917], [407.0713755]]),
        "PC 34:1 [M+Na]+": np.array([[48.77490479], [731.6235719]]),
        "PC 36:1 [M+Na]+": np.array([[61.22399177], [918.3598766]]),
        "PC 32:2 [M+Na]+": np.array([[25], [375]]),
        "PC 34:2 [M+Na]+": np.array([[50], [750]]),
        "PC 36:2 [M+Na]+": np.array([[65], [975]]),
        "PC 32:4 [M+Na]+": np.array([[20], [300]]),
        "PC 34:4 [M+Na]+": np.array([[45], [675]]),
        "PC 36:4 [M+Na]+": np.array([[60], [900]]),
        "PC 38:4 [M+Na]+": np.array([[75], [1125]]),
    }
    for id, result_image in result.items():
        nptest.assert_allclose(
            result_image,
            expected_output[id],
        )


def test_na_isotope_correction(database: LipidDB, images: dict[str, npt.NDArray]) -> None:
    result = na_isotope_correction(database=database, images=images)
    expected_output = {
        "PC 33:1 d7 [M+H]+": np.array([[80], [1200]]),
        "PC 32:0 [M+H]+": np.array([[85], [1275]]),
        "PC 32:1 [M+H]+": np.array([[90], [1350]]),
        "PC 34:1 [M+H]+": np.array([[65], [975]]),
        "PC 36:1 [M+H]+": np.array([[50], [750]]),
        "PC 32:2 [M+H]+": np.array([[95], [1425]]),
        "PC 34:2 [M+H]+": np.array([[70], [1050]]),
        "PC 36:2 [M+H]+": np.array([[55], [825]]),
        "PC 32:4 [M+H]+": np.array([[100], [1500]]),
        "PC 34:4 [M+H]+": np.array([[30], [450]]),
        "PC 36:4 [M+H]+": np.array([[27.5], [412.5]]),
        "PC 38:4 [M+H]+": np.array([[20], [300]]),
        "PC 33:1 d7 [M+Na]+": np.array([[40], [600]]),
        "PC 32:0 [M+Na]+": np.array([[35], [525]]),
        "PC 32:1 [M+Na]+": np.array([[0], [0]]),
        "PC 34:1 [M+Na]+": np.array([[27.5], [412.5]]),
        "PC 36:1 [M+Na]+": np.array([[50], [750]]),
        "PC 32:2 [M+Na]+": np.array([[25], [375]]),
        "PC 34:2 [M+Na]+": np.array([[50], [750]]),
        "PC 36:2 [M+Na]+": np.array([[65], [975]]),
        "PC 32:4 [M+Na]+": np.array([[20], [300]]),
        "PC 34:4 [M+Na]+": np.array([[45], [675]]),
        "PC 36:4 [M+Na]+": np.array([[60], [900]]),
        "PC 38:4 [M+Na]+": np.array([[75], [1125]]),
    }
    for id, result_image in result.items():
        nptest.assert_allclose(
            result_image,
            expected_output[id],
        )
