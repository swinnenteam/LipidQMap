import copy
from concurrent import futures
from enum import Enum
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import numpy.typing as npt

from app.config import Config
from app.database import IonMode, LipidDB
from app.pyimzml_mod import ImzMLParser, get_calibration_offsets, getionimages


class ImageType(str, Enum):
    raw = "raw"
    isotope = "isotope"
    quant = "quant"


class SampleImageCollection:
    """todo"""

    def __init__(
        self,
        progress_callback,
        database: LipidDB,
        imzml_path: str,
        ion_mode: IonMode,
        config: Config,
    ) -> None:
        self.ion_mode = ion_mode
        self.raw: dict[str, npt.NDArray]
        self.isotope: dict[str, npt.NDArray]
        self.quant: dict[str, npt.NDArray]
        self.raw_filtered: dict[str, npt.NDArray]
        self.isotope_filtered: dict[str, npt.NDArray]
        self.quant_filtered: dict[str, npt.NDArray]
        self.shape: tuple[int, int]
        self.load_data(progress_callback, database=database, imzml_path=imzml_path, config=config)
        self.filter_data(progress_callback, config=config)

    def load_data(self, progress_callback, database: LipidDB, imzml_path: str, config: Config):
        imzml_parser = ImzMLParser(imzml_path)
        self.shape = (
            int(imzml_parser.imzmldict["max count of pixels x"]),
            int(imzml_parser.imzmldict["max count of pixels y"]),
        )
        progress_callback.emit(20)
        self.raw = load_ion_images(
            database=database,
            imzml=imzml_parser,
            ion_mode=self.ion_mode,
            config=config,
        )
        self.isotope = dict()
        if config.settings.processing_settings.na_isotope_correction:
            self.isotope = na_isotope_correction(database=database, images=self.raw)
        if config.settings.processing_settings.m2_isotope_correction:
            if self.isotope:
                self.isotope = m2_isotope_correction(database=database, images=self.isotope)
            else:
                self.isotope = m2_isotope_correction(database=database, images=self.raw)
        progress_callback.emit(65)
        if self.isotope:
            self.quant = quantitaton(database=database, images=self.isotope)
        else:
            self.quant = quantitaton(database=database, images=self.raw)
        progress_callback.emit(70)

    def filter_data(self, progress_callback, config: Config):
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

    def get(self, image_type: ImageType, species_id: str) -> npt.NDArray | None:
        match image_type:
            case ImageType.raw:
                return self.raw_filtered.get(species_id)
            case ImageType.isotope:
                return self.isotope_filtered.get(species_id)
            case ImageType.quant:
                return self.quant_filtered.get(species_id)
            case _:
                return None


def load_database_image_collection(
    progress_callback, database_path: str, ion_mode: IonMode, imzml_paths: list[str], config: Config
) -> tuple[LipidDB, dict[str, SampleImageCollection]]:
    """todo"""
    samples: dict[str, SampleImageCollection] = dict()
    database = LipidDB(database_path, ion_mode)
    for path in imzml_paths:
        progress_callback.emit(5)
        image_collection = SampleImageCollection(
            progress_callback,
            database=database,
            imzml_path=path,
            ion_mode=ion_mode,
            config=config,
        )
        samples[Path(path).stem] = image_collection

    return database, samples


def load_ion_images(
    database: LipidDB,
    imzml: ImzMLParser,
    ion_mode: IonMode,
    config: Config,
    classes: list[str] | None = None,
) -> dict[str, npt.NDArray]:
    """Load the ion images"""
    images: dict[str, npt.NDArray] = dict()
    species_ids, species_mzs = database.get_all_species(classes)

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

    """
    items = [(imzml, mz, ppm_to_tolerance(ppm=ppm, mz=mz), offsets) for (_, mz) in species]
    with Pool(processes=4) as pool:
        for idx, result in enumerate(pool.starmap(getionimage, items)):
            progress_callback.emit(int(progress_slope * idx + progress_start))
            id, _ = species[idx]
            images[id] = result
    """

    ppm = config.settings.processing_settings.ppm
    tolerances = [ppm_to_tolerance(ppm=ppm, mz=mz) for mz in species_mzs]
    image_stack = getionimages(imzml, mzs=species_mzs, tolerances=tolerances, offsets=offsets)
    images = dict(zip(species_ids, list(image_stack)))

    return images


def ppm_to_tolerance(ppm: float, mz: float) -> float:
    """Convert ppm mass accuracy to atomic units."""
    return abs(ppm / 1e6 * mz)


def m2_isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray], classes: list[str] | None = None
) -> dict[str, npt.NDArray]:
    """
    Isotopic correction for species withing same class between the M+2 (two 13C) of a species
    and a corresponding monoisotopic species with one less double bond (two extra H).
    """
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


def na_isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray], classes: list[str] | None = None
) -> dict[str, npt.NDArray]:
    """
    Isotopic correction for [M+H]+ species with overlap from [M+Na]+ species.
    According to Höring et al. Anal. Chem. 2020, 92, 16, 10966–10970
    https://pubs.acs.org/doi/10.1021/acs.analchem.0c02408
    """
    corrected_images: dict[str, npt.NDArray] = copy.deepcopy(images)
    h_na_ratio_ims = dict()

    for key, value in database.get_sodium_coef_mzs().items():
        h_id = value[0]
        na_id = value[1]
        ratio_image = np.divide(images[na_id], images[h_id])
        ratio_image[ratio_image == np.inf] = np.nan
        ratio_image = replace_nan_with_median(ratio_image)
        h_na_ratio_ims[key] = ratio_image

    for species_id in database.get_ids_sorted_for_isotope(classes=classes):
        if "[M+H]+" not in species_id:
            continue
        lipid_class = database.get_class(id=species_id)
        na_isotope = database.get_Na_isotope_ID(id=species_id)
        if na_isotope:
            corrected_images[species_id] = (
                images[species_id] - h_na_ratio_ims[lipid_class] * corrected_images[na_isotope]
            ).clip(min=0)
        else:
            corrected_images[species_id] = np.copy(images[species_id])

    return corrected_images


def quantitaton(
    database: LipidDB, images: dict[str, npt.NDArray], classes: list[str] | None = None
) -> dict[str, npt.NDArray]:
    """
    Quantify by dividing the ion images by the ion image of the standard (1 standard per class)
    and multiplying by a user provided factor (standard amount)
    """
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
