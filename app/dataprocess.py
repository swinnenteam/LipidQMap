from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import numpy.typing as npt
from pyimzml.ImzMLParser import ImzMLParser, _bisect_spectrum

from app.database import LipidDB


@dataclass
class SampleImageCollection:
    raw: dict[str, npt.NDArray] = field(default_factory=dict)
    isotope: dict[str, npt.NDArray] = field(default_factory=dict)
    quant: dict[str, npt.NDArray] = field(default_factory=dict)


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
    database: LipidDB, imzml: ImzMLParser, classes: list[str] | None = None, tolerance=0.005
) -> dict[str, npt.NDArray]:
    images: dict[str, npt.NDArray] = dict()
    for id, mz in database.get_all_species(classes):
        images[id] = getionimage(imzml, mz_value=mz, tol=tolerance, reduce_func=np.max)
    return images


def isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray], classes: list[str] | None = None
) -> dict[str, npt.NDArray]:
    corrected_images: dict[str, npt.NDArray] = dict()
    for species_id in database.get_ids_sorted_for_isotope(classes=classes):
        m2_isotope = database.get_M2_isotope_ID(id=species_id)
        if m2_isotope:
            corrected_images[species_id] = (
                images[species_id]
                - database.get_M2_isotope_percent(id=m2_isotope) * images[m2_isotope]
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


def median_filter(image: npt.NDArray, size: int = 3) -> npt.NDArray:
    if size % 2 == 0 or size < 3:
        raise ValueError(
            "The median filter kernel size should be an odd number higher or equal than 3."
        )
    padding_width = int((size - 1) / 2)
    # Pad the image with zeros to handle edge cases
    padded_image = np.pad(image, pad_width=padding_width, mode="constant", constant_values=np.nan)
    filtered_image = np.zeros_like(image)

    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            # Extract the n x n neighborhood around the current pixel
            neighborhood = padded_image[i : i + size, j : j + size]
            median_value = np.nanmedian(neighborhood)
            filtered_image[i, j] = median_value

    return_image = np.copy(image)
    return_image[np.isnan(image)] = filtered_image[np.isnan(image)]

    return filtered_image


def fill_image_nan(image_to_fill: npt.NDArray, filler_image: npt.NDArray) -> npt.NDArray:
    """
    Puts corresponsing pixel values from the filler_image in the pixel locations where the image_to_fill is Nan
    """
    return_image = np.copy(image_to_fill)
    return_image[np.isnan(return_image)] = filler_image[np.isnan(return_image)]
    return return_image


def winsorize_image(image: npt.NDArray, upper_percentile: float = 99) -> npt.NDArray:
    """
    Set extreme high values to some percentile of the data
    """
    upper_bound = np.nanpercentile(image, upper_percentile)
    winsorized_image = np.copy(image)
    winsorized_image[winsorized_image > upper_bound] = upper_bound

    return winsorized_image
