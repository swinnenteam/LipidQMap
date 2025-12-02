import copy
import math
import os
import pickle
import re
import statistics
from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Callable, Iterable, ItemsView, Sequence

import numpy as np
import numpy.typing as npt
from numba import njit

from app.config import Config
from app.database import DatabaseFactory, IonMode, LipidDB, LipidSpecies
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


class SampleIonMode(str, Enum):
    """
    Ion mode at the section/sample level. Supports combined datasets.
    """

    positive = "positive"
    negative = "negative"
    combined = "combined"

    @classmethod
    def from_ion_mode(cls, ion_mode: IonMode) -> "SampleIonMode":
        """Map a database ion mode to the sample-level mode enumeration."""
        if ion_mode == IonMode.positive:
            return cls.positive
        if ion_mode == IonMode.negative:
            return cls.negative
        if ion_mode == IonMode.summed:
            raise ValueError("Summed ion mode is not valid for sample acquisition.")
        raise ValueError(f"Unsupported ion mode '{ion_mode}'.")


@dataclass(slots=True)
class SampleFiles:
    """
    Grouping of imzML files representing one logical sample across ion modes.

    Attributes:
        label: Display label used for downstream sample identification.
        pos_path: Path to the positive ion mode file, if available.
        neg_path: Path to the negative ion mode file, if available.
        pos_filename: Basename cached for UI display of the positive mode file.
        neg_filename: Basename cached for UI display of the negative mode file.
    """

    _POLARITY_TOKENS = {"pos", "neg", "positive", "negative"}

    label: str
    pos_path: str | None = None
    neg_path: str | None = None
    pos_filename: str | None = None
    neg_filename: str | None = None

    @staticmethod
    def _tokenize_filename(filename: str) -> list[str]:
        """Return alphanumeric tokens extracted from the filename stem."""
        stem = Path(filename).stem
        return [token for token in re.split(r"[^0-9A-Za-z]+", stem) if token]

    @classmethod
    def normalized_key(cls, filename: str) -> str:
        """Produce a polarity-agnostic key used to group complementary files."""
        tokens = cls._tokenize_filename(filename)
        filtered = [token.lower() for token in tokens if token.lower() not in cls._POLARITY_TOKENS]
        return " ".join(filtered) if filtered else Path(filename).stem.lower()

    @classmethod
    def derive_label(cls, filename: str) -> str:
        """Generate a default label for display, removing polarity markers when possible."""
        tokens = cls._tokenize_filename(filename)
        filtered = [token for token in tokens if token.lower() not in cls._POLARITY_TOKENS]
        if filtered:
            return "_".join(filtered)
        return Path(filename).stem

    def can_accept(self, mode: IonMode) -> bool:
        """Return True when the selection still has an empty slot for the given mode."""
        if mode == IonMode.positive:
            return self.pos_path is None
        if mode == IonMode.negative:
            return self.neg_path is None
        return False

    def assign(self, mode: IonMode, path: str, filename: str) -> None:
        """Store the chosen path and filename for the provided ion mode."""
        if mode == IonMode.positive:
            self.pos_path = path
            self.pos_filename = filename
        elif mode == IonMode.negative:
            self.neg_path = path
            self.neg_filename = filename
        else:
            raise ValueError("Cannot assign combined ion mode input.")

    def mode_paths(self) -> list[tuple[IonMode, str]]:
        """Return (mode, path) tuples for each available file in the selection."""
        paths: list[tuple[IonMode, str]] = []
        if self.pos_path is not None:
            paths.append((IonMode.positive, self.pos_path))
        if self.neg_path is not None:
            paths.append((IonMode.negative, self.neg_path))
        return paths

    def normalized_key_value(self) -> str:
        """Expose the grouping key based on whichever filename is present."""
        for candidate in (self.pos_filename, self.neg_filename):
            if candidate:
                return self.normalized_key(candidate)
        return self.label.lower()


class SectionMsiImage:
    """
    Class for handling collections of sample images with different types (raw, isotope, quant).

    Attributes:
        ion_mode (SampleIonMode): Ionization mode context of the sample (positive, negative, combined).
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
        self.ion_mode = SampleIonMode.from_ion_mode(ion_mode)
        self._measurement_mode: IonMode | None = ion_mode
        self.config = config
        self.database = database
        self.raw: dict[str, npt.NDArray]
        self.isotope: dict[str, npt.NDArray]
        self.quant: dict[str, npt.NDArray | None]
        self.average_spectrum: npt.NDArray
        self.num_spectra: int = 0
        self.coordinates: npt.NDArray = np.empty((0, 3), dtype=int)
        self.pixel_size_um: tuple[float, float] | None = None
        self.stage_coordinates: npt.NDArray | None = None
        self.spot_ids: np.ndarray | None = None
        self._spot_index_lookup: dict[int, int] | None = None
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
        detected_polarity = getattr(imzml_parser, "polarity", None)
        if detected_polarity is not None:
            detected_mode = _polarity_to_ion_mode(detected_polarity, imzml_path)
            if detected_mode != self._measurement_mode:
                raise ValueError(
                    f"ImzML file '{imzml_path}' reports polarity '{detected_polarity}', "
                    f"which does not match the detected ion mode "
                    f"'{self._measurement_mode.name if self._measurement_mode else 'combined'}'."
                )
        self.coordinates = np.asarray(imzml_parser.coordinates, dtype=np.int32)
        self.stage_coordinates = self._extract_stage_coordinates(imzml_parser)
        self._initialize_spot_ids(imzml_parser)
        self.pixel_size_um = self._extract_pixel_size(imzml_parser)
        progress_file_callback.emit(20)

        # internal calibration
        cal_ppm = self.config.settings.processing_settings.calibration_ppm
        calibrant_mz = (
            self.config.settings.processing_settings.pos_calibrant
            if self.ion_mode == SampleIonMode.positive
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
        neutral_suffix = "(+)" if self._measurement_mode == IonMode.positive else "(-)"
        self.raw = sum_adducts(
            database=database, images=self.raw, neutral_suffix=neutral_suffix
        )  # type: ignore
        self.isotope = sum_adducts(
            database=database, images=self.isotope, neutral_suffix=neutral_suffix
        )  # type: ignore
        self.quant = sum_adducts(
            database=database, images=self.quant, neutral_suffix=neutral_suffix
        )
        progress_file_callback.emit(95)

    def _extract_stage_coordinates(self, parser: ImzMLParser) -> npt.NDArray | None:
        stage_coords = getattr(parser, "stage_coordinates", None)
        if not stage_coords:
            return None
        if not any(coord is not None for coord in stage_coords):
            return None
        arr = np.full((len(stage_coords), 3), np.nan, dtype=np.float64)
        for idx, coord in enumerate(stage_coords):
            if coord is not None:
                arr[idx] = coord
        return arr

    def _initialize_spot_ids(self, parser: ImzMLParser) -> None:
        parsed_ids = getattr(parser, "spot_ids", None)
        if not parsed_ids or not any(value is not None for value in parsed_ids):
            self.spot_ids = None
            self._spot_index_lookup = None
            return
        arr = np.full(len(parsed_ids), -1, dtype=np.int64)
        lookup: dict[int, int] = {}
        for idx, value in enumerate(parsed_ids):
            if value is None:
                continue
            spot_id = int(value)
            arr[idx] = spot_id
            lookup[spot_id] = idx
        self.spot_ids = arr
        self._spot_index_lookup = lookup if lookup else None

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
            if image is None:
                result.append(False)
                continue
            result.append(
                threshold_check(winsorize_image(image, winsor), min_intensity, min_pixels)
            )
        return result

    def update_summed_image(
        self,
        database: LipidDB,
        neutral_specie: LipidSpecies,
        allowed_adduct_ids: set[str] | None,
    ) -> None:
        """
        Recompute the summed neutral image for a single specie using the provided
        set of allowed adduct IDs.
        """
        target_key = neutral_specie.id_adduct
        self.raw[target_key] = _sum_images_for_neutral(
            database=database,
            neutral_specie=neutral_specie,
            images=self.raw,
            allowed_adduct_ids=allowed_adduct_ids,
        )
        self.isotope[target_key] = _sum_images_for_neutral(
            database=database,
            neutral_specie=neutral_specie,
            images=self.isotope,
            allowed_adduct_ids=allowed_adduct_ids,
        )
        self.quant[target_key] = _sum_images_for_neutral(
            database=database,
            neutral_specie=neutral_specie,
            images=self.quant,
            allowed_adduct_ids=allowed_adduct_ids,
        )

    @property
    def shape(self) -> tuple[int, int]:
        for image in self.raw.values():
            if image is not None:
                x, y = image.shape
                return (x, y)
        raise ValueError("No non-empty images available to determine shape.")

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

    def __init__(self, samples: dict[str, SectionMsiImage], species_order: Sequence[str]):
        self.samples = samples
        self.index: list[str] = list(samples.keys())
        self.species_order: list[str] = list(species_order)

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
        if not self.samples:
            return []

        aggregated: dict[str, bool] = {species_id: False for species_id in self.species_order}

        for image in self.samples.values():
            image_checks = image.criteria_check()
            for species_id, check in zip(image.raw.keys(), image_checks):
                if species_id not in aggregated:
                    aggregated[species_id] = check
                else:
                    aggregated[species_id] = aggregated[species_id] or check

        return [aggregated.get(species_id, False) for species_id in self.species_order]

    def update_summed_images(
        self,
        database: LipidDB,
        neutral_species_ids: Iterable[str],
        allowed_adduct_ids: set[str] | None,
    ) -> None:
        """
        Refresh the summed neutral images for the provided neutral species IDs.
        """
        for neutral_id in neutral_species_ids:
            neutral_specie = database.species.get(neutral_id)
            if neutral_specie is None:
                continue
            for sample in self.samples.values():
                sample.update_summed_image(
                    database=database,
                    neutral_specie=neutral_specie,
                    allowed_adduct_ids=allowed_adduct_ids,
                )

    def recompute_summed_images(
        self,
        database: LipidDB,
        allowed_adduct_ids: set[str],
        changed_adduct_ids: Iterable[str] | None = None,
    ) -> set[str]:
        """
        Recompute summed images using the allowed adduct IDs. If a subset of adducts
        changed, only their neutral counterparts are recomputed.
        Returns the set of neutral IDs that were updated.
        """
        neutral_ids: set[str] = set()
        if changed_adduct_ids is None:
            neutral_ids = {s.id_adduct for s in database.get_neutral_species()}
        else:
            for adduct_id in changed_adduct_ids:
                neutral_specie = database.get_neutral_from_adduct(adduct_id)
                if neutral_specie is not None:
                    neutral_ids.add(neutral_specie.id_adduct)

        if not neutral_ids:
            return set()

        self.update_summed_images(
            database=database,
            neutral_species_ids=neutral_ids,
            allowed_adduct_ids=allowed_adduct_ids,
        )
        return neutral_ids

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


def _polarity_to_ion_mode(polarity: str | None, imzml_path: str) -> IonMode:
    if polarity == "positive":
        return IonMode.positive
    if polarity == "negative":
        return IonMode.negative
    if polarity == "mixed":
        raise ValueError(
            f"ImzML file '{imzml_path}' reports mixed polarity, which is not supported."
        )
    raise ValueError(
        f"ImzML file '{imzml_path}' does not specify an ion mode. Please ensure polarity metadata is present."
    )


def detect_imzml_ion_mode(imzml_path: str) -> IonMode:
    """
    Detect the ion mode of an imzML file by scanning for polarity markers in the XML.

    The function searches for the PSI CV accessions and keywords that indicate polarity:
    - Positive ion mode: ``MS:1000130`` or ``positive scan``
    - Negative ion mode: ``MS:1000129`` or ``negative scan``

    Args:
        imzml_path (str): Path to the imzML file.

    Returns:
        IonMode: Detected ion mode for the file.

    Raises:
        ValueError: If the polarity cannot be determined or conflicting markers are found.
    """

    markers: dict[IonMode, tuple[bytes, ...]] = {
        IonMode.positive: (b"MS:1000130", b"positive scan"),
        IonMode.negative: (b"MS:1000129", b"negative scan"),
    }
    found_modes: set[IonMode] = set()
    chunk_size = 65536
    tail = b""

    try:
        with open(imzml_path, "rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                data = tail + chunk
                for mode, terms in markers.items():
                    if mode in found_modes:
                        continue
                    if any(term in data for term in terms):
                        found_modes.add(mode)
                if len(found_modes) > 1:
                    break
                tail = data[-64:]
    except OSError as exc:
        raise ValueError(f"Unable to read imzML file '{imzml_path}': {exc}") from exc

    if len(found_modes) == 1:
        return next(iter(found_modes))
    if len(found_modes) > 1:
        raise ValueError(
            f"ImzML file '{imzml_path}' contains both positive and negative polarity markers."
        )
    raise ValueError(
        f"ImzML file '{imzml_path}' does not specify ion mode metadata. "
        "Ensure the file includes 'MS:1000130' (positive) or 'MS:1000129' (negative)."
    )


def _unique_label(base_label: str, existing: set[str]) -> str:
    """Create a label that is unique within the provided set by appending numeric suffixes."""
    label = base_label
    suffix = 2
    while label in existing:
        label = f"{base_label}_{suffix}"
        suffix += 1
    return label


def _merge_average_spectra(
    primary: npt.NDArray[np.floating], secondary: npt.NDArray[np.floating]
) -> npt.NDArray[np.floating]:
    """Merge two average spectra arrays, keeping mz values sorted."""
    if primary.size == 0:
        return secondary
    if secondary.size == 0:
        return primary
    merged = np.concatenate((primary, secondary), axis=1)
    order = np.argsort(merged[0])
    return merged[:, order]


def _combine_section_images(
    images: list[tuple[IonMode, SectionMsiImage]],
) -> SectionMsiImage:
    """Combine one or more SectionMsiImage instances into a single multi-mode sample."""
    if not images:
        raise ValueError("No SectionMsiImage instances provided for combination.")
    base_mode, combined = images[0]
    for mode, image in images[1:]:
        if combined.raw and image.raw and combined.shape != image.shape:
            raise ValueError(
                "Cannot combine samples with differing spatial dimensions."
            )
        combined.raw.update(image.raw)
        combined.isotope.update(image.isotope)
        combined.quant.update(image.quant)
        combined.average_spectrum = _merge_average_spectra(
            combined.average_spectrum, image.average_spectrum
        )
        combined.num_spectra += image.num_spectra
        if combined.pixel_size_um is None and image.pixel_size_um is not None:
            combined.pixel_size_um = image.pixel_size_um
        if combined.coordinates.size == 0 and image.coordinates.size > 0:
            combined.coordinates = image.coordinates
        if combined.stage_coordinates is None and image.stage_coordinates is not None:
            combined.stage_coordinates = np.copy(image.stage_coordinates)
        if combined.spot_ids is None and image.spot_ids is not None:
            combined.spot_ids = np.copy(image.spot_ids)
            combined._spot_index_lookup = (
                dict(image._spot_index_lookup) if image._spot_index_lookup is not None else None
            )
    if len(images) > 1:
        combined.ion_mode = SampleIonMode.combined
        combined._measurement_mode = None
    else:
        combined.ion_mode = SampleIonMode.from_ion_mode(base_mode)
        combined._measurement_mode = base_mode
    return combined


def _normalize_selections(
    imzml_inputs: Sequence[str | SampleFiles],
) -> list[SampleFiles]:
    """Convert raw path inputs into a list of SampleFiles groupings ready for loading."""
    selections: list[SampleFiles] = []
    groups_by_key: dict[str, list[SampleFiles]] = {}
    names_in_use: set[str] = set()

    for item in imzml_inputs:
        if isinstance(item, SampleFiles):
            label = _unique_label(item.label, names_in_use)
            if label != item.label:
                item.label = label
            names_in_use.add(item.label)
            key = item.normalized_key_value()
            groups_by_key.setdefault(key, []).append(item)
            selections.append(item)
            continue

        path = item
        filename = os.path.basename(path)
        ion_mode = detect_imzml_ion_mode(path)
        key = SampleFiles.normalized_key(filename)
        candidates = groups_by_key.setdefault(key, [])
        selection = next(
            (candidate for candidate in candidates if candidate.can_accept(ion_mode)),
            None,
        )
        if selection is None:
            base_label = SampleFiles.derive_label(filename)
            label = _unique_label(base_label, names_in_use)
            selection = SampleFiles(label=label)
            candidates.append(selection)
            selections.append(selection)
            names_in_use.add(selection.label)
        selection.assign(ion_mode, path, filename)

    return selections


def load_database_image_collection(
    progress_file_callback,
    progress_overall_callback,
    database_path: str,
    imzml_paths: Sequence[str | SampleFiles],
    config: Config,
) -> tuple[LipidDB, SampleCollection]:
    """
    Load a collection of sample images from multiple imzML files.
    """
    selections = _normalize_selections(imzml_paths)
    samples: dict[str, SectionMsiImage] = {}
    databases_by_mode: dict[IonMode, LipidDB] = {}

    total_selections = len(selections)

    for idx, selection in enumerate(selections):
        if total_selections:
            progress_overall_callback.emit(int(idx / total_selections * 100))
        sample_images: list[tuple[IonMode, SectionMsiImage]] = []

        for ion_mode, path in selection.mode_paths():
            progress_file_callback.emit(15)
            if ion_mode not in databases_by_mode:
                db = DatabaseFactory(database_path, ion_mode).create_database()
                databases_by_mode[ion_mode] = db

            image_collection = SectionMsiImage(
                progress_file_callback,
                database=databases_by_mode[ion_mode],
                imzml_path=path,
                ion_mode=ion_mode,
                config=config,
            )
            sample_images.append((ion_mode, image_collection))

        if not sample_images:
            continue

        combined_image = _combine_section_images(sample_images)
        progress_file_callback.emit(100)
        label = _unique_label(selection.label, set(samples.keys()))
        if label != selection.label:
            selection.label = label
        samples[label] = combined_image
    progress_overall_callback.emit(100)
    combined_species: dict[str, LipidSpecies] = {}
    for mode in (IonMode.positive, IonMode.negative):
        db = databases_by_mode.get(mode)
        if db is None:
            continue
        for specie in db.species.values():
            if specie.adduct == "":
                neutral_copy = specie.model_copy(deep=True)
                neutral_copy.adduct = "(+)" if mode == IonMode.positive else "(-)"
                for attr in ("id_adduct", "class_adduct", "ion_mode"):
                    neutral_copy.__dict__.pop(attr, None)
                combined_species[neutral_copy.id_adduct] = neutral_copy
            else:
                combined_species.setdefault(specie.id_adduct, specie)

    for db in databases_by_mode.values():
        for specie in db.species.values():
            if specie.adduct in {"", "(+)", "(-)"}:
                continue
            combined_species.setdefault(specie.id_adduct, specie)

    combined_database = LipidDB(combined_species)
    species_order = combined_database.species_ids_neutral_first()
    combined_database.index = species_order
    return combined_database, SampleCollection(samples, species_order=species_order)


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


def _sum_images_for_neutral(
    database: LipidDB,
    neutral_specie: LipidSpecies,
    images: dict[str, npt.NDArray | None],
    allowed_adduct_ids: set[str] | None = None,
) -> npt.NDArray | None:
    """
    Return the summed image for a neutral specie using the provided adduct images.
    """
    adduct_forms = database.get_adduct_species_for_neutral(neutral_specie)
    adduct_images: list[npt.NDArray] = []
    for specie in adduct_forms:
        if allowed_adduct_ids is not None and specie.id_adduct not in allowed_adduct_ids:
            continue
        candidate = images.get(specie.id_adduct)
        if candidate is not None:
            adduct_images.append(candidate)

    if len(adduct_images) == 0:
        image: npt.NDArray | None = None
    elif len(adduct_images) == 1:
        image = adduct_images[0]
    else:
        stacked = np.stack(adduct_images, axis=0).astype(np.float64, copy=False)
        all_nan_mask = np.all(np.isnan(stacked), axis=0)
        np.nan_to_num(stacked, copy=False, nan=0.0)
        image = np.sum(stacked, axis=0)
        image[all_nan_mask] = np.nan

    return image


def sum_adducts(
    database: LipidDB,
    images: dict[str, npt.NDArray | None],
    neutral_suffix: str | None = None,
    allowed_adduct_ids: set[str] | None = None,
) -> dict[str, npt.NDArray | None]:
    """
    Sum together the different adduct forms of each species.

    Args:
        database: Lipid database providing species relationships.
        images: Mapping from species ID (with adduct) to image data.
        neutral_suffix: Optional suffix used to rename neutral species keys. When
            provided, neutral entries are emitted as ``<id> <neutral_suffix>``.
        allowed_adduct_ids: Optional set of adduct IDs that are permitted to
            contribute to the summed neutral image.
    """

    result: dict[str, npt.NDArray | None] = {}
    all_species_ids, _ = database.get_all_species(neutral=True)
    neutral_lookup = {specie.id_adduct: specie for specie in database.get_neutral_species()}

    for species_id in all_species_ids:
        specie = database.species[species_id]
        if species_id in neutral_lookup:
            neutral_specie = neutral_lookup[species_id]
            image = _sum_images_for_neutral(
                database=database,
                neutral_specie=neutral_specie,
                images=images,
                allowed_adduct_ids=allowed_adduct_ids,
            )

            key = neutral_specie.id_adduct
            if neutral_suffix is not None:
                key = f"{neutral_specie.id} {neutral_suffix}"
            result[key] = image
        else:
            result[specie.id_adduct] = images.get(specie.id_adduct)

    return result


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
