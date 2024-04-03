import numpy as np
import numpy.testing as nptest
import numpy.typing as npt
import pytest

from app.dataprocess import ppm_to_tolerance, replace_nan_with_median, winsorize_image


@pytest.fixture(name="nan_image")
def fixture_nan_image() -> npt.NDArray:
    return np.array([[10.0, 12.0, np.nan], [14.0, np.nan, 12.0], [11.0, 6.0, 8.0]])


@pytest.fixture(name="image")
def fixture_image() -> npt.NDArray:
    return np.array([[10.0, 12.0, 15.0], [14.0, 12.0, 12.0], [11.0, 6.0, 8.0]])


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
