import copy
import timeit
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Callable

import numpy as np
import numpy.typing as npt
from numba import njit

from app.config import Config
from app.database import DatabaseFactory, IonMode, LipidDB
from app.pyimzml_mod import ImzMLParser, get_calibration_offsets, get_ion_images

# start_time = timeit.default_timer()
# print(timeit.default_timer() - start_time)


class ImageType(str, Enum):
    """
    Enum for specifying image types.
    """

    raw = "raw"
    isotope = "isotope"
    quant = "quant"


class SampleImageCollection:
    """
    Class for handling collections of sample images with different types (raw, isotope, quant).

    Attributes:
        ion_mode (IonMode): Ionization mode of the sample.
        raw (dict[str, npt.NDArray]): Dictionary of raw images.
        isotope (dict[str, npt.NDArray]): Dictionary of isotope corrected images.
        quant (dict[str, npt.NDArray]): Dictionary of quantitated images.
        raw_filtered (dict[str, npt.NDArray]): Dictionary of filtered raw images.
        isotope_filtered (dict[str, npt.NDArray]): Dictionary of filtered isotope images.
        quant_filtered (dict[str, npt.NDArray]): Dictionary of filtered quantitated images.
        shape (tuple[int, int]): Shape of the images.
    """

    def __init__(
        self,
        progress_file_callback,
        database: LipidDB,
        imzml_path: str,
        ion_mode: IonMode,
        config: Config,
    ) -> None:
        """
        Initialize the SampleImageCollection.

        Args:
            progress_file_callback: Callback for updating progress.
            database (LipidDB): Database object containing lipid information.
            imzml_path (str): Path to the imzML file.
            ion_mode (IonMode): Ionization mode of the sample.
            config (Config): Configuration settings.
        """
        self.ion_mode = ion_mode
        self.raw: dict[str, npt.NDArray]
        self.isotope: dict[str, npt.NDArray]
        self.quant: dict[str, npt.NDArray | None]
        self.raw_filtered: dict[str, npt.NDArray | None]
        self.isotope_filtered: dict[str, npt.NDArray | None]
        self.quant_filtered: dict[str, npt.NDArray | None]
        self.load_data(
            progress_file_callback, database=database, imzml_path=imzml_path, config=config
        )
        self.filter_data(progress_file_callback, config=config)

    def load_data(self, progress_file_callback, database: LipidDB, imzml_path: str, config: Config):
        """
        Load raw images from the imzML file and calculate isotope and quantitative images.

        Args:
            progress_file_callback: Callback for updating progress.
            database (LipidDB): Database object containing lipid information.
            imzml_path (str): Path to the imzML file.
            config (Config): Configuration settings.
        """
        imzml_parser = ImzMLParser(imzml_path)

        # self.shape = (
        #    int(imzml_parser.imzmldict["max count of pixels x"]),
        #    int(imzml_parser.imzmldict["max count of pixels y"]),
        # )
        progress_file_callback.emit(20)

        start_time = timeit.default_timer()
        self.raw = load_ion_images(
            database=database,
            imzml=imzml_parser,
            ion_mode=self.ion_mode,
            config=config,
        )
        print(timeit.default_timer() - start_time)
        self.isotope = dict()
        if config.settings.processing_settings.na_isotope_correction:
            self.isotope = na_isotope_correction(database=database, images=self.raw)
        if config.settings.processing_settings.m2_isotope_correction:
            if self.isotope:
                self.isotope = m2_isotope_correction(database=database, images=self.isotope)
            else:
                self.isotope = m2_isotope_correction(database=database, images=self.raw)
        progress_file_callback.emit(65)
        if self.isotope:
            self.quant = quantitaton(database=database, images=self.isotope)
        else:
            self.quant = quantitaton(database=database, images=self.raw)
        progress_file_callback.emit(70)

    def filter_data(self, progress_file_callback, config: Config):
        """
        Apply winsorize filtering to raw, isotope, and quant images and replace nan
        values in the quant images.

        Args:
            progress_file_callback: Callback for updating progress.
            config (Config): Configuration settings.
        """
        n1 = config.settings.filter_settings.raw_image_winsorizing_percentile
        n2 = config.settings.filter_settings.quant_image_winsorizing_percentile
        self.raw_filtered = {k: winsorize_image(v, n1) for (k, v) in self.raw.items()}
        progress_file_callback.emit(75)
        self.isotope_filtered = {k: winsorize_image(v, n1) for (k, v) in self.isotope.items()}
        progress_file_callback.emit(80)
        self.quant_filtered = {k: replace_nan_with_median(v) for (k, v) in self.quant.items()}
        progress_file_callback.emit(95)
        self.quant_filtered = {k: winsorize_image(v, n2) for (k, v) in self.quant_filtered.items()}
        progress_file_callback.emit(100)

    def get(self, image_type: ImageType, species_id: str) -> npt.NDArray | None:
        """
        Get a specific image by type and species ID.

        Args:
            image_type (ImageType): Type of the image (raw, isotope, quant).
            species_id (str): ID of the species.

        Returns:
            npt.NDArray | None: The requested image or None if not found.
        """
        match image_type:
            case ImageType.raw:
                return self.raw_filtered.get(species_id)
            case ImageType.isotope:
                return self.isotope_filtered.get(species_id)
            case ImageType.quant:
                return self.quant_filtered.get(species_id)
            case _:
                return None

    @cache
    def get_mean(self, image_type: ImageType, species_id: str) -> int:
        """
        Get the mean intensity of a specific image by type and species ID.

        Args:
            image_type (ImageType): Type of the image (raw, isotope, quant).
            species_id (str): ID of the species.

        Returns:
            int: The mean of the requested image or zero if not found.
        """
        match image_type:
            case ImageType.raw:
                image = self.raw_filtered.get(species_id)
                if image is None:
                    return 0
                return np.nanmean(image, axis=(0, 1))
            case ImageType.isotope:
                image = self.isotope_filtered.get(species_id)
                if image is None:
                    return 0
                return np.nanmean(image, axis=(0, 1))
            case ImageType.quant:
                image = self.quant_filtered.get(species_id)
                if image is None:
                    return 0
                return np.nanmean(image, axis=(0, 1))
            case _:
                return 0

    def transform(self, transformation: str) -> None:
        """
        Applies a specified transformation to the images.

        Parameters:
        transformation : str
            The transformation to apply. Supported values are:
            - "rotate_left": Rotates the image 90 degrees counterclockwise.
            - "rotate_right": Rotates the image 90 degrees clockwise.
            - "reflect_horizontal": Reflects the image horizontally (left-right flip).
            - "reflect_vertical": Reflects the image vertically (up-down flip).

        Returns:
            None
                The function modifies the images in place and does not return any value.
        """

        func: Callable
        param: int

        match transformation:
            case "rotate_left":
                func = np.rot90
                param = -1
            case "rotate_right":
                func = np.rot90
                param = 1
                pass
            case "reflect_horizontal":
                func = np.flip
                param = 1
            case "reflect_vertical":
                func = np.flip
                param = 0
            case _:
                return

        self.raw = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.raw.items()
        }
        self.raw_filtered = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.raw_filtered.items()
        }
        self.isotope = {key: func(value, param) for (key, value) in self.isotope.items()}
        self.isotope_filtered = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.isotope_filtered.items()
        }
        self.quant = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.quant.items()
        }
        self.quant_filtered = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.quant_filtered.items()
        }

    @property
    def shape(self) -> tuple[int, int]:
        x, y = self.raw[next(iter(self.raw))].shape
        return (x, y)


def load_database_image_collection(
    progress_file_callback,
    progress_overall_callback,
    database_path: str,
    ion_mode: IonMode,
    imzml_paths: list[str],
    config: Config,
) -> tuple[LipidDB, dict[str, SampleImageCollection]]:
    """
    Load a collection of sample images from multiple imzML files.
    """
    samples: dict[str, SampleImageCollection] = dict()
    database = DatabaseFactory(database_path, ion_mode).create_database()
    for idx, path in enumerate(imzml_paths):
        progress_overall_callback.emit(int(idx / len(imzml_paths) * 100))
        progress_file_callback.emit(5)
        image_collection = SampleImageCollection(
            progress_file_callback,
            database=database,
            imzml_path=path,
            ion_mode=ion_mode,
            config=config,
        )
        samples[Path(path).stem] = image_collection
    progress_overall_callback.emit(100)
    return database, samples


def load_ion_images(
    database: LipidDB,
    imzml: ImzMLParser,
    ion_mode: IonMode,
    config: Config,
) -> dict[str, npt.NDArray]:
    """
    Load ion images from the imzML file based on the species in the database.

    Args:
        database (LipidDB): Database object containing lipid information.
        imzml (ImzMLParser): Parser for the imzML file.
        ion_mode (IonMode): Ionization mode for the sample images.
        config (Config): Configuration settings.

    Returns:
        dict[str, npt.NDArray]: Dictionary of loaded ion images.
    """
    images: dict[str, npt.NDArray] = dict()
    species_ids, species_mzs = database.get_all_species()

    cal_ppm = config.settings.processing_settings.calibration_ppm
    calibrant_mz = (
        config.settings.processing_settings.pos_calibrant
        if ion_mode.value == IonMode.positive
        else config.settings.processing_settings.neg_calibrant
    )
    tolerance = ppm_to_tolerance(ppm=cal_ppm, mz=calibrant_mz)
    offsets = (
        get_calibration_offsets(imzml, mz=calibrant_mz, tol=tolerance)
        if config.settings.processing_settings.online_calibration
        else None
    )

    ppm = config.settings.processing_settings.ppm
    tolerances = [ppm_to_tolerance(ppm=ppm, mz=mz) for mz in species_mzs]
    image_stack = get_ion_images(p=imzml, mzs=species_mzs, tolerances=tolerances, offsets=offsets)
    images = dict(zip(species_ids, list(image_stack)))

    return images


def ppm_to_tolerance(ppm: float, mz: float) -> float:
    """Convert ppm mass accuracy to atomic units."""
    return abs(ppm / 1e6 * mz)


def m2_isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray]
) -> dict[str, npt.NDArray]:
    """
    Isotopic correction for species withing same class between the M+2 (two 13C) of a species
    and a corresponding monoisotopic species with one less double bond (two extra H).
    """
    corrected_images: dict[str, npt.NDArray] = copy.deepcopy(images)
    for species_id in database.get_ids_sorted_for_isotope():
        m2_isotope = database.get_M2_isotope_ID(id=species_id)
        if m2_isotope:
            corrected_images[species_id] = (
                images[species_id]
                - database.get_M2_isotope_percent(id=m2_isotope) * corrected_images[m2_isotope]
            ).clip(min=0)
        else:
            corrected_images[species_id] = np.copy(images[species_id])

    return corrected_images


def na_isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray]
) -> dict[str, npt.NDArray]:
    """
    Isotopic correction for [M+H]+ species with overlap from [M+Na]+ species.
    According to Höring et al. Anal. Chem. 2020, 92, 16, 10966–10970
    https://pubs.acs.org/doi/10.1021/acs.analchem.0c02408
    """
    corrected_images: dict[str, npt.NDArray] = copy.deepcopy(images)
    h_na_ratio_ims = dict()

    for h_id, na_id in database.get_hydrogen_sodium_std_pairs():
        ratio_image = np.divide(images[na_id], images[h_id])
        ratio_image[ratio_image == np.inf] = np.nan
        h_na_ratio_ims[h_id] = replace_nan_with_median(ratio_image)

    for species_id in database.get_ids_sorted_for_isotope():
        if "[M+H]+" not in species_id:
            continue
        standard, _ = database.get_standard(id=species_id)
        na_isotope = database.get_Na_isotope_ID(id=species_id)
        if na_isotope is not None and standard is not None:
            corrected_images[species_id] = (
                images[species_id] - h_na_ratio_ims[standard] * corrected_images[na_isotope]
            ).clip(min=0)
        else:
            corrected_images[species_id] = np.copy(images[species_id])

    return corrected_images


def quantitaton(database: LipidDB, images: dict[str, npt.NDArray]) -> dict[str, npt.NDArray | None]:
    """
    Quantify by dividing the ion images by the ion image of the standard (1 standard per class)
    and multiplying by a user provided factor (standard amount)
    """
    quant_images: dict[str, npt.NDArray | None] = dict()
    for species_id in database.get_ids_non_standards():
        standard_id, standard_amount = database.get_standard(id=species_id)
        if standard_id is not None and standard_amount is not None:
            quant_image = np.divide(images[species_id], images[standard_id]) * standard_amount
            quant_image[quant_image == np.inf] = np.nan
            quant_images[species_id] = quant_image
        else:
            quant_images[species_id] = None

    return quant_images


@njit
def _add_padding(arr, pad_width):
    """
    Pads the array with NaNs to handle edge cases.
    """
    padded_shape = (arr.shape[0] + 2 * pad_width, arr.shape[1] + 2 * pad_width)
    padded_arr = np.full(padded_shape, np.nan)
    padded_arr[pad_width:-pad_width, pad_width:-pad_width] = arr
    return padded_arr


@njit
def replace_nan_with_median(arr: npt.NDArray | None) -> npt.NDArray | None:
    """
    Replaces nan values with mean of surrounding window of 3 by 3 pixels, excluding any nan in the window
    """
    if arr is None:
        return None
    # Pad the array with NaNs to handle edge cases
    padded_arr = _add_padding(arr, 1)
    nan_mask = np.isnan(arr)
    indices = np.argwhere(nan_mask)
    result = np.copy(arr)
    for i, j in indices:
        # Extract surrounding 3x3 window, taking into account offset by 1
        window = padded_arr[i : i + 3, j : j + 3]
        result[i, j] = np.nanmedian(window)
    return result


def winsorize_image(image: npt.NDArray | None, upper_percentile: float = 99) -> npt.NDArray | None:
    """
    Set extreme high values to some percentile of the data
    """
    if image is None:
        return None
    upper_bound = np.nanpercentile(image, upper_percentile)
    winsorized_image = np.copy(image)
    winsorized_image[winsorized_image > upper_bound] = upper_bound

    return winsorized_image
