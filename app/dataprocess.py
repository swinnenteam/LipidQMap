import copy
import math
import os
import pickle
import statistics
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Callable, ItemsView

import numpy as np
import numpy.typing as npt
from numba import njit

from app.config import Config
from app.database import DatabaseFactory, IonMode, LipidDB
from app.pyimzml_mod import ImzMLParser, get_average_spectrum, get_ion_images

# start_time = timeit.default_timer()
# print(timeit.default_timer() - start_time)


class ImageType(str, Enum):
    """
    Enum for specifying image types.
    """

    raw = "raw"
    isotope = "isotope"
    quant = "quant"


class SectionMsiImage:
    """
    Class for handling collections of sample images with different types (raw, isotope, quant).

    Attributes:
        ion_mode (IonMode): Ionization mode of the sample.
        raw (dict[str, npt.NDArray]): Dictionary of raw images.
        isotope (dict[str, npt.NDArray]): Dictionary of isotope corrected images.
        quant (dict[str, npt.NDArray]): Dictionary of quantitated images.
        average_spectrum (npt.NDArray): [0,:] the mz array and [1,:] intensity array of the spectrum
        shape (tuple[int, int]): Shape of the images.
        pixel_size_um (tuple[float, float] | None): Pixel size in micrometers along (x, y).
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
        Initialize the SectionMsiImage.

        Args:
            progress_file_callback: Callback for updating progress.
            database (LipidDB): Database object containing lipid information.
            imzml_path (str): Path to the imzML file.
            ion_mode (IonMode): Ionization mode of the sample.
            config (Config): Configuration settings.
        """
        self.ion_mode = ion_mode
        self.config = config
        self.raw: dict[str, npt.NDArray]
        self.isotope: dict[str, npt.NDArray]
        self.quant: dict[str, npt.NDArray | None]
        self.average_spectrum: npt.NDArray
        self.num_spectra: int = 0
        self.coordinates: npt.NDArray = np.empty((0, 3), dtype=int)
        self.pixel_size_um: tuple[float, float] | None = None
        self.load_data(progress_file_callback, database=database, imzml_path=imzml_path)

    def load_data(self, progress_file_callback, database: LipidDB, imzml_path: str) -> None:
        """
        Load raw images from the imzML file and calculate isotope and quantitative images.

        Args:
            progress_file_callback: Callback for updating progress.
            database (LipidDB): Database object containing lipid information.
            imzml_path (str): Path to the imzML file.
        """
        # create imzml parser
        imzml_parser = ImzMLParser(imzml_path)
        self.coordinates = np.asarray(imzml_parser.coordinates, dtype=np.int32)
        self.pixel_size_um = self._extract_pixel_size(imzml_parser)
        progress_file_callback.emit(20)

        # internal calibration
        cal_ppm = self.config.settings.processing_settings.calibration_ppm
        calibrant_mz = (
            self.config.settings.processing_settings.pos_calibrant
            if self.ion_mode.value == IonMode.positive
            else self.config.settings.processing_settings.neg_calibrant
        )
        min_intensity = self.config.settings.processing_settings.calibration_min_intensity
        tolerance = ppm_to_tolerance(ppm=cal_ppm, mz=calibrant_mz)
        if self.config.settings.processing_settings.online_calibration:
            imzml_parser.recallibrate(mz=calibrant_mz, tol=tolerance, min_intensity=min_intensity)
        progress_file_callback.emit(25)

        # load raw ion images from parser
        self.raw = dict()
        species_ids, species_mzs = database.get_all_species()
        ppm = self.config.settings.processing_settings.ppm
        tolerances = [ppm_to_tolerance(ppm=ppm, mz=mz) for mz in species_mzs]
        image_stack = get_ion_images(p=imzml_parser, mzs=species_mzs, tolerances=tolerances)
        self.raw = dict(zip(species_ids, list(image_stack)))
        progress_file_callback.emit(60)

        # calculate average spectrum
        bin_size = self.config.settings.processing_settings.bin_size
        self.average_spectrum = get_average_spectrum(
            p=imzml_parser, bin_size=bin_size, n_pixels=1000
        )
        self.num_spectra = len(imzml_parser.coordinates)

        # perform isotope correction
        self.isotope = dict()
        if self.config.settings.processing_settings.na_isotope_correction:
            self.isotope = na_isotope_correction(database=database, images=self.raw)
        if self.config.settings.processing_settings.db_isotope_correction:
            if self.isotope:
                self.isotope = db_isotope_correction(database=database, images=self.isotope)
            else:
                self.isotope = db_isotope_correction(database=database, images=self.raw)
        progress_file_callback.emit(70)

        # perform quantitation
        if self.isotope:
            self.quant = quantitaton(database=database, images=self.isotope)
        else:
            self.quant = quantitaton(database=database, images=self.raw)
        progress_file_callback.emit(75)

        # replace nan with median of surrounding pixels
        if self.config.settings.processing_settings.imputation:
            self.raw = {k: replace_nan_with_median(v) for (k, v) in self.raw.items()}
            progress_file_callback.emit(80)
            self.isotope = {k: replace_nan_with_median(v) for (k, v) in self.isotope.items()}
            progress_file_callback.emit(85)
            self.quant = {
                k: replace_nan_with_median(v) if v is not None else None
                for k, v in self.quant.items()
            }
        progress_file_callback.emit(90)

        # sum the different adduct forms of the same species
        self.raw = sum_adducts(database=database, images=self.raw)  # type: ignore
        self.isotope = sum_adducts(database=database, images=self.isotope)  # type: ignore
        self.quant = sum_adducts(database=database, images=self.quant)
        progress_file_callback.emit(100)

    @staticmethod
    def _extract_pixel_size(parser: ImzMLParser) -> tuple[float, float] | None:
        """Return the pixel size in micrometers if present in the imzML metadata."""
        try:
            pixel_size_x = parser.imzmldict.get("pixel size x")
            pixel_size_y = parser.imzmldict.get("pixel size y")
        except AttributeError:
            return None

        if pixel_size_x is None or pixel_size_y is None:
            return None

        try:
            pixel_size_tuple = (float(pixel_size_x), float(pixel_size_y))
        except (TypeError, ValueError):
            return None

        px, py = pixel_size_tuple
        if px <= 0 or py <= 0:
            return None
        return px, py

    def get(self, image_type: ImageType, species_id: str) -> npt.NDArray | None:
        """
        Get a specific image by type and species ID.

        Args:
            image_type (ImageType): Type of the image (raw, isotope, quant).
            species_id (str): ID of the species.

        Returns:
            npt.NDArray | None: The requested image or None if not found.
        """
        n1 = self.config.settings.filter_settings.raw_image_winsorizing_percentile
        n2 = self.config.settings.filter_settings.quant_image_winsorizing_percentile
        match image_type:
            case ImageType.raw:
                return winsorize_image(self.raw.get(species_id), n1)
            case ImageType.isotope:
                return winsorize_image(self.isotope.get(species_id), n1)
            case ImageType.quant:
                return winsorize_image(self.quant.get(species_id), n2)

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
                image = self.raw.get(species_id)
                if image is None:
                    return 0
                return np.nanmean(image, axis=(0, 1))
            case ImageType.isotope:
                image = self.isotope.get(species_id)
                if image is None:
                    return 0
                return np.nanmean(image, axis=(0, 1))
            case ImageType.quant:
                image = self.quant.get(species_id)
                if image is None:
                    return 0
                return np.nanmean(image, axis=(0, 1))

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
                param = 1
            case "rotate_right":
                func = np.rot90
                param = -1
            case "reflect_horizontal":
                func = np.flip
                param = 1
            case "reflect_vertical":
                func = np.flip
                param = 0
            case _:
                return

        if self.coordinates.size > 0:
            self.coordinates = self._transform_coordinates(self.coordinates, transformation)

        if self.pixel_size_um is not None and transformation in {"rotate_left", "rotate_right"}:
            self.pixel_size_um = (self.pixel_size_um[1], self.pixel_size_um[0])

        self.raw = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.raw.items()
        }
        self.isotope = {key: func(value, param) for (key, value) in self.isotope.items()}
        self.quant = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.quant.items()
        }

    def criteria_check(self) -> list[bool]:
        """
        Check if the ion images meet the criteria to be selected for export.
        """
        min_intensity = self.config.settings.selection_settings.minimum_intensity
        min_pixels = self.config.settings.selection_settings.minimum_pixels
        winsor = self.config.settings.filter_settings.raw_image_winsorizing_percentile
        result = []
        for id, image in self.raw.items():
            result.append(
                threshold_check(winsorize_image(image, winsor), min_intensity, min_pixels)
            )
        return result

    @property
    def shape(self) -> tuple[int, int]:
        x, y = self.raw[next(iter(self.raw))].shape
        return (x, y)

    @staticmethod
    def _transform_coordinates(
        coords: npt.NDArray[np.int32], transformation: str
    ) -> npt.NDArray[np.int32]:
        """Todo: refactor to avoid handling rotation in 2 places. (self.transform() and here)"""
        if coords.size == 0:
            return coords

        transformed = coords.copy()
        x = transformed[:, 0].astype(np.int64)
        y = transformed[:, 1].astype(np.int64)

        x_min = x.min()
        y_min = y.min()
        width = x.max() - x_min + 1
        height = y.max() - y_min + 1

        x_rel = x - x_min
        y_rel = y - y_min

        match transformation:
            case "rotate_left":  # np.rot90(..., 1) counter-clockwise
                new_x_rel = y_rel
                new_y_rel = (width - 1) - x_rel
            case "rotate_right":  # np.rot90(..., -1) clockwise
                new_x_rel = (height - 1) - y_rel
                new_y_rel = x_rel
            case "reflect_horizontal":  # flip LR
                new_x_rel = (width - 1) - x_rel
                new_y_rel = y_rel
            case "reflect_vertical":  # flip UD
                new_x_rel = x_rel
                new_y_rel = (height - 1) - y_rel
            case _:
                return transformed

        new_x = new_x_rel + 1
        new_y = new_y_rel + 1

        transformed[:, 0] = new_x.astype(np.int32)
        transformed[:, 1] = new_y.astype(np.int32)
        return transformed

    def width_um(self) -> float | None:
        """Return the physical width of the MSI image in micrometers if metadata is available."""
        if self.pixel_size_um is None:
            return None
        _, width_px = self.shape
        return self.pixel_size_um[0] * width_px

    def height_um(self) -> float | None:
        """Return the physical height of the MSI image in micrometers if metadata is available."""
        if self.pixel_size_um is None:
            return None
        height_px, _ = self.shape
        return self.pixel_size_um[1] * height_px


@njit
def threshold_check(image: npt.NDArray, min_intensity: int, min_pixels: int) -> bool:
    return (image > min_intensity).sum() > min_pixels


class SampleCollection:
    """
    Class that manages all the loaded samples.
    """

    def __init__(self, samples: dict[str, SectionMsiImage]):
        self.samples = samples
        self.index: list[str] = list(samples.keys())

    def items(self) -> ItemsView[str, SectionMsiImage]:
        return self.samples.items()

    def dimensions(self):
        return [sample.shape for sample in self.samples.values()]

    def _scalebar_widths_um(self) -> list[float]:
        widths: list[float] = []
        for sample in self.samples.values():
            width = sample.width_um()
            if width is not None:
                widths.append(width)
        return widths

    @staticmethod
    def _max_scalebar_length(widths: list[float]) -> int | None:
        if not widths:
            return None
        min_width = min(widths)
        max_length = int(math.floor(min_width))
        if max_length < 10:
            return None
        return max_length

    @staticmethod
    def _auto_scalebar_length(widths: list[float], max_length: int | None) -> int | None:
        if not widths or max_length is None or max_length < 100:
            return None
        targets = [width / 5.0 for width in widths]
        auto_estimate = statistics.median(targets)
        auto_length = int(round(auto_estimate / 100.0) * 100)
        auto_length = max(100, auto_length)
        if auto_length > max_length:
            auto_length = (max_length // 100) * 100
        if auto_length < 100:
            return None
        return auto_length

    def get_scalebar_auto_length_um(self) -> int | None:
        widths = self._scalebar_widths_um()
        max_length = self._max_scalebar_length(widths)
        return self._auto_scalebar_length(widths, max_length)

    def get_scalebar_max_length_um(self) -> int | None:
        widths = self._scalebar_widths_um()
        return self._max_scalebar_length(widths)

    def get_scalebar_length_um(self, config: Config) -> int | None:
        if not config.settings.scalebar_settings.enabled:
            return None
        widths = self._scalebar_widths_um()
        max_length = self._max_scalebar_length(widths)
        if max_length is None:
            return None
        if config.settings.scalebar_settings.auto:
            return self._auto_scalebar_length(widths, max_length)
        manual_length = int(config.settings.scalebar_settings.manual_length_um)
        manual_length = max(0, manual_length)
        manual_length = (manual_length // 10) * 10
        if manual_length < 10:
            return None
        return min(manual_length, max_length)

    def criteria_check(self) -> list[bool]:
        checks = []
        for _, image in self.samples.items():
            checks.append(image.criteria_check())
        checks = list(map(list, zip(*checks)))
        return [any(check) for check in checks]

    def get_spectrum(self, sample_id: str) -> npt.NDArray:
        return self.samples[sample_id].average_spectrum

    def get_max_intensity(self, image_type: ImageType, species_id: str) -> int | None:
        max_value: int | None = 0
        for _, (_, image_collection) in enumerate(self.samples.items()):
            image = image_collection.get(image_type, species_id)
            image_max = np.nanmax(image) if image is not None else 0
            max_value = image_max if max_value is not None and image_max > max_value else max_value
        max_value = None if max_value == 0 else max_value
        return max_value

    def save_to_pickle(self, path) -> None:
        """
        Saves a pickle file for each sample in self.samples.

        For each key in self.samples, this function creates a pickle file named <key>.pkl in the provided
        directory. Only the 'quant' dictionary from each SectionImage is saved, and any key/value pair in
        that dictionary where the value is None is omitted.

        Args:
            path (str): The directory where the pickle files should be saved.
        """
        # Ensure the directory exists
        os.makedirs(path, exist_ok=True)

        for key, section_image in self.samples.items():
            # Filter out any entries with None values from the quant dictionary
            quant_filtered = {k: v for k, v in section_image.quant.items() if v is not None}

            # Define the filename using the key (add .pkl extension)
            filename = f"{key}.pkl"
            filepath = os.path.join(path, filename)

            try:
                with open(filepath, "wb") as file:
                    pickle.dump(quant_filtered, file)
            except Exception as e:
                raise Exception("Error", f"An error occurred while saving the file:\n{e}")

    def __iter__(self):
        return iter(self.samples)

    def __getitem__(self, key):
        return self.samples.get(key)

    def __len__(self):
        return len(self.samples)


def load_database_image_collection(
    progress_file_callback,
    progress_overall_callback,
    database_path: str,
    ion_mode: IonMode,
    imzml_paths: list[str],
    config: Config,
) -> tuple[LipidDB, SampleCollection]:
    """
    Load a collection of sample images from multiple imzML files.
    """
    samples: dict[str, SectionMsiImage] = dict()
    database = DatabaseFactory(database_path, ion_mode).create_database()
    for idx, path in enumerate(imzml_paths):
        progress_overall_callback.emit(int(idx / len(imzml_paths) * 100))
        progress_file_callback.emit(15)
        image_collection = SectionMsiImage(
            progress_file_callback,
            database=database,
            imzml_path=path,
            ion_mode=ion_mode,
            config=config,
        )
        samples[Path(path).stem] = image_collection
    progress_overall_callback.emit(100)
    return database, SampleCollection(samples)


def ppm_to_tolerance(ppm: float, mz: float) -> float:
    """Convert ppm mass accuracy to atomic units."""
    return abs(ppm / 1e6 * mz)


def db_isotope_correction(
    database: LipidDB, images: dict[str, npt.NDArray]
) -> dict[str, npt.NDArray]:
    """
    Corrects for isotopic overlap between lipids of the same class but different degrees of saturation.

    This function addresses isobaric interferences where the isotopic peaks of a
    more unsaturated lipid overlap with the monoisotopic peak of a less
    unsaturated lipid within the same class. It accounts for the following cases:

    1.  **M+2 Overlap**: The M+2 isotopologue of a lipid (e.g., from two ¹³C atoms)
        with N double bonds interferes with the monoisotopic peak of a lipid with
        N-1 double bonds (which has two extra hydrogens).
        - Example: The M+2 peak of PC 34:2 contributes to the signal of PC 34:1.

    2.  **M+4 Overlap**: The M+4 isotopologue of a lipid (e.g., from four ¹³C atoms)
        with N double bonds interferes with the monoisotopic peak of a lipid with
        N-2 double bonds (which has four extra hydrogens).
        - Example: The M+4 peak of PC 34:2 contributes to the signal of PC 34:0.

    The function calculates the theoretical isotopic contributions from the more
    unsaturated species and subtracts them from the measured intensity of the
    less unsaturated species.
    """
    corrected_images: dict[str, npt.NDArray] = copy.deepcopy(images)
    for s in database.get_species_sorted_for_isotope():
        if s.id_adduct not in images.keys():
            continue
        if s.m2_isotope:
            corrected_images[s.id_adduct] = (
                images[s.id_adduct]
                - s.m2_isotope.m2_rel_abundance * corrected_images[s.m2_isotope.id_adduct]
            ).clip(min=0)
            if s.m4_isotope:
                corrected_images[s.id_adduct] = (
                    corrected_images[s.id_adduct]
                    - s.m4_isotope.m4_rel_abundance * corrected_images[s.m4_isotope.id_adduct]
                ).clip(min=0)
        else:
            corrected_images[s.id_adduct] = np.copy(images[s.id_adduct])

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

    # correct the [M+H]+
    for s in database.get_species_sorted_for_isotope():
        if "[M+H]+" != s.adduct:
            continue
        if s.na_isotope is not None and s.standard is not None:
            corrected_images[s.id_adduct] = (
                images[s.id_adduct]
                - h_na_ratio_ims[s.standard.id_adduct] * corrected_images[s.na_isotope.id_adduct]
            ).clip(min=0)

    # correct the [M+Na]+
    # e.g. PC 34:1[M+Na]+  = (PC 34:1[M+Na]+) - (PC 36:4[M+H]+)
    for s in database.get_species_sorted_for_isotope():
        if "[M+Na]+" != s.adduct:
            continue
        if s.na_isotope is not None:
            h_species_id_adduct = s.id + " [M+H]+"
            na_species_id_adduct = s.na_isotope.id + " [M+Na]+"
            corrected_images[na_species_id_adduct] = (
                corrected_images[na_species_id_adduct] - corrected_images[h_species_id_adduct]
            ).clip(min=0)

    return corrected_images


def quantitaton(database: LipidDB, images: dict[str, npt.NDArray]) -> dict[str, npt.NDArray | None]:
    """
    Quantify by dividing the ion images by the ion image of the standard (1 standard per class)
    and multiplying by a user provided factor (standard amount)
    """
    quant_images: dict[str, npt.NDArray | None] = dict()
    for specie in database.get_ids_non_standards():
        std = specie.standard
        if std is not None:
            quant_image = np.divide(images[specie.id_adduct], images[std.id_adduct]) * std.amount
            quant_image[quant_image == np.inf] = np.nan
            quant_images[specie.id_adduct] = quant_image
        else:
            quant_images[specie.id_adduct] = None

    return quant_images


def sum_adducts(
    database: LipidDB, images: dict[str, npt.NDArray | None]
) -> dict[str, npt.NDArray | None]:
    """
    Sum together the different adduct forms of the species
    """
    image: npt.NDArray | None = None
    all_species_ids, _ = database.get_all_species(neutral=True)
    summed_species = database.get_neutral_species()
    for specie in summed_species:
        adduct_forms = database.get_adduct_species_for_neutral(specie)
        adduct_images: list[npt.NDArray] = [
            images[s.id_adduct] for s in adduct_forms if s.id_adduct in images and images[s.id_adduct] is not None  # type: ignore
        ]
        if len(adduct_images) == 0:
            image = None
        elif len(adduct_images) == 1:
            image = adduct_images[0]
        else:
            stacked = np.stack(adduct_images, axis=0)
            # Sum the images ignoring NaNs.
            image = np.nansum(stacked, axis=0)
            # Create a mask for pixels where every image is NaN.
            all_nan_mask = np.all(np.isnan(stacked), axis=0)
            # Set those pixels to NaN in the summed image.
            if image is not None:
                image[all_nan_mask] = np.nan

        images[specie.id_adduct] = image

    # return in original order
    return {key: images[key] for key in all_species_ids if key in images}


@njit
def _add_padding(arr, pad_width) -> npt.NDArray:
    """
    Pads the array with NaNs to handle edge cases.
    """
    padded_shape = (arr.shape[0] + 2 * pad_width, arr.shape[1] + 2 * pad_width)
    padded_arr = np.full(padded_shape, np.nan)
    padded_arr[pad_width:-pad_width, pad_width:-pad_width] = arr
    return padded_arr


@njit
def replace_nan_with_median(arr: npt.NDArray) -> npt.NDArray:
    """
    Replaces nan values with mean of surrounding window of 3 by 3 pixels, excluding any nan in the window
    """
    # Pad the array with NaNs to handle edge cases
    padded_arr = _add_padding(arr, 1)
    padded_arr = np.where(padded_arr == 0.0, np.nan, padded_arr)  # also replace 0.0 with NaN
    nan_mask = np.isnan(arr) | (arr == 0.0)
    indices = np.argwhere(nan_mask)
    result = np.copy(arr)
    for i, j in indices:
        # Extract surrounding 3x3 window, taking into account offset by 1
        window = padded_arr[i : i + 3, j : j + 3]
        median = np.nanmedian(window)
        if math.isnan(median):  # window contained only NaNs (originally NaN or zero values)
            # Preserve transparency (NaN) for pixels with no data, otherwise keep zeros zero.
            result[i, j] = np.nan if math.isnan(arr[i, j]) else 0.0
        else:
            result[i, j] = median
    return result


@njit
def winsorize_image(image: npt.NDArray | None, upper_percentile: float = 99) -> npt.NDArray | None:
    """
    Set extreme high values to some percentile of the data
    """
    if image is None:
        return None
    upper_bound = np.nanpercentile(image, upper_percentile)
    winsorized_image = np.copy(image)

    # winsorized_image[winsorized_image > upper_bound] = upper_bound
    for i in range(winsorized_image.shape[0]):
        for j in range(winsorized_image.shape[1]):
            if winsorized_image[i, j] > upper_bound:
                winsorized_image[i, j] = upper_bound

    return winsorized_image
    return winsorized_image
    return winsorized_image
