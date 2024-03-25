import copy
from pathlib import Path
from typing import Callable

import numpy as np
import numpy.typing as npt
from pyimzml.ImzMLParser import ImzMLParser, _bisect_spectrum

from app.config import config
from app.database import IonMode, LipidDB


class SampleImageCollection:
    def __init__(self, progress_callback, database: LipidDB, imzml_path: Path) -> None:
        self.raw: dict[str, npt.NDArray]
        self.isotope: dict[str, npt.NDArray]
        self.quant: dict[str, npt.NDArray]
        self.raw_filtered: dict[str, npt.NDArray]
        self.isotope_filtered: dict[str, npt.NDArray]
        self.quant_filtered: dict[str, npt.NDArray]
        self.load_data(progress_callback, database=database, imzml_path=imzml_path)
        self.filter_data(progress_callback)

    def load_data(self, progress_callback, database: LipidDB, imzml_path: Path):
        imzml_parser = ImzMLParser(imzml_path)
        progress_callback.emit(10)
        self.raw = load_ion_images(progress_callback, database=database, imzml=imzml_parser)
        self.isotope = isotope_correction(database=database, images=self.raw)
        progress_callback.emit(65)
        self.quant = quantitaton(database=database, images=self.isotope)
        progress_callback.emit(70)

    def filter_data(self, progress_callback):
        n1 = config.settings.filter_settings.raw_image_winsorizing_percentile
        n2 = config.settings.filter_settings.quant_image_winsorizing_percentile
        self.raw_filtered = {k: winsorize_image(v, n1) for (k, v) in self.raw.items()}
        progress_callback.emit(75)
        self.isotope_filtered = {k: winsorize_image(v, n1) for (k, v) in self.isotope.items()}
        progress_callback.emit(80)
        self.quant_filtered = {k: replace_nan_with_median(v) for (k, v) in self.quant.items()}
        progress_callback.emit(95)
        self.quant_filtered = {k: winsorize_image(v, n2) for (k, v) in self.quant_filtered.items()}
        progress_callback.emit(100)


def load_database_image_collection(
    progress_callback, database_path: Path, ion_mode: IonMode, imzml_path: Path
) -> tuple[LipidDB, SampleImageCollection]:
    database = LipidDB(database_path, ion_mode)
    progress_callback.emit(5)
    image_collection = SampleImageCollection(
        progress_callback, database=database, imzml_path=imzml_path
    )
    return database, image_collection


def getionimage(
    p, mz_value: float, tol: float = 0.1, z: int = 1, reduce_func: Callable = sum
) -> npt.NDArray:
    """
    Get an image representation of the intensity distribution
    of the ion with specified m/z value.

    By default, the intensity values within the tolerance region are summed.

    :param p:
        the ImzMLParser (or anything else with similar attributes) for the desired dataset
    :param mz_value:
        m/z value for which the ion image shall be returned
    :param tol:
        Absolute tolerance for the m/z value, such that all ions with values
        mz_value-|tol| <= x <= mz_value+|tol| are included. Defaults to 0.1
    :param z:
        z Value if spectrogram is 3-dimensional.
    :param reduce_func:
        the bahaviour for reducing the intensities between mz_value-|tol| and mz_value+|tol| to a single value. Must
        be a function that takes a sequence as input and outputs a number. By default, the values are summed.

    :return:
        numpy matrix with each element representing the ion intensity in this
        pixel. Can be easily plotted with matplotlib
    """
    tol = abs(tol)
    im = np.full(
        [p.imzmldict["max count of pixels y"], p.imzmldict["max count of pixels x"]], np.nan
    )
    for i, (x, y, z_) in enumerate(p.coordinates):
        if z_ == 0:
            UserWarning(
                "z coordinate = 0 present, if you're getting blank images set getionimage(.., .., z=0)"
            )
        if z_ == z:
            mzs, ints = map(lambda x: np.asarray(x), p.getspectrum(i))
            min_i, max_i = _bisect_spectrum(mzs, mz_value, tol)
            values = ints[min_i : max_i + 1]
            values = np.zeros(1) if values.size == 0 else values
            im[y - 1, x - 1] = reduce_func(values)
    return im


def load_ion_images(
    progress_callback,
    database: LipidDB,
    imzml: ImzMLParser,
    classes: list[str] | None = None,
) -> dict[str, npt.NDArray]:
    images: dict[str, npt.NDArray] = dict()
    species = database.get_all_species(classes)
    species_count = len(species)
    progress_start = 10
    progress_end = 60
    progress_slope = (progress_end - progress_start) / (species_count - 1)
    ppm = config.settings.processing_settings.ppm
    for count, (id, mz) in enumerate(species):
        progress_callback.emit(int(progress_slope * count + progress_start))
        tolerance = ppm_to_tolerance(ppm=ppm, mz=mz)
        images[id] = getionimage(imzml, mz_value=mz, tol=tolerance, reduce_func=np.max)
    return images


def ppm_to_tolerance(ppm: float, mz: float) -> float:
    return abs(ppm / 10e6 * mz)


def isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray], classes: list[str] | None = None
) -> dict[str, npt.NDArray]:
    corrected_images: dict[str, npt.NDArray] = copy.deepcopy(images)
    for species_id in database.get_ids_sorted_for_isotope(classes=classes):
        m2_isotope = database.get_M2_isotope_ID(id=species_id)
        if m2_isotope:
            corrected_images[species_id] = (
                images[species_id]
                - database.get_M2_isotope_percent(id=m2_isotope) * corrected_images[m2_isotope]
            ).clip(min=0)
        else:
            corrected_images[species_id] = np.copy(images[species_id])

    return corrected_images


def quantitaton(
    database: LipidDB, images: dict[str, npt.NDArray], classes: list[str] | None = None
) -> dict[str, npt.NDArray]:
    quant_images: dict[str, npt.NDArray] = dict()
    for species_id in database.get_ids_non_standards(classes=classes):
        standard_id, standard_amount = database.get_standard(id=species_id)
        quant_image = np.divide(images[species_id], images[standard_id]) * standard_amount
        quant_image[quant_image == np.inf] = np.nan
        quant_images[species_id] = quant_image

    return quant_images


def replace_nan_with_median(arr: npt.NDArray) -> npt.NDArray:
    """
    Replaces nan values with mean of surrounding window of 3 by 3 pixels, excluding any nan in the window
    """
    # Pad the array with NaNs to handle edge cases
    padded_arr = np.pad(arr, pad_width=1, mode="constant", constant_values=np.nan)
    nan_mask = np.isnan(arr)
    indices = np.argwhere(nan_mask)
    result = np.copy(arr)
    for i, j in indices:
        # Extract surrounding 3x3 window, taking into account offset by 1
        window = padded_arr[i : i + 3, j : j + 3]
        result[i, j] = np.nanmedian(window)
    return result


def winsorize_image(image: npt.NDArray, upper_percentile: float = 99) -> npt.NDArray:
    """
    Set extreme high values to some percentile of the data
    """
    upper_bound = np.nanpercentile(image, upper_percentile)
    winsorized_image = np.copy(image)
    winsorized_image[winsorized_image > upper_bound] = upper_bound

    return winsorized_image
