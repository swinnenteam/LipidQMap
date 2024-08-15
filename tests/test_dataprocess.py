import numpy as np
import numpy.testing as nptest
import numpy.typing as npt
import pytest

from app.database import DatabaseFactory, IonMode, LipidDB
from app.dataprocess import (
    m2_isotope_correction,
    na_isotope_correction,
    ppm_to_tolerance,
    replace_nan_with_median,
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


def test_winsorize_image(image: npt.NDArray) -> None:
    win_image = winsorize_image(image, upper_percentile=99)
    nptest.assert_array_equal(
        win_image,
        np.array([[10.0, 12.0, 14.92], [14.0, 12.0, 12.0], [11.0, 6.0, 8.0]]),
        strict=True,
    )


def test_winsorize_image_nan(nan_image: npt.NDArray) -> None:
    win_image = winsorize_image(nan_image, upper_percentile=99)
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


def test_ppm_to_tolerance() -> None:
    assert pytest.approx(0.008, rel=1e-6) == ppm_to_tolerance(ppm=10, mz=800)


def test_m2_isotope_correction(database: LipidDB, images: dict[str, npt.NDArray]) -> None:
    result = m2_isotope_correction(database=database, images=images)
    expected_output = {
        "PC 33:1 d7 [M+H]+": np.array([[80], [1200]]),
        "PC 32:0 [M+H]+": np.array([[75.93041423], [1138.956213]]),
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
        "PC 32:0 [M+Na]+": np.array([[31.89053337], [478.3580006]]),
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
    for id, result_image in result.items():
        nptest.assert_allclose(
            result_image,
            expected_output[id],
        )
