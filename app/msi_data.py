import math
import os
import pickle
import re
import statistics
from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path
from typing import Callable, ItemsView, Sequence

import numpy as np
import numpy.typing as npt

from app.config import Config
from app.database import IonMode, LipidDB, LipidSpecies
from app.image_processing import (
    _apply_transparent_mask,
    db_isotope_correction,
    na_isotope_correction,
    ppm_to_tolerance,
    quantitaton,
    replace_nan_with_median,
    sum_adducts,
    threshold_check,
    winsorize_image,
)
from app.pyimzml_mod import ImzMLParser, get_average_spectrum, get_ion_images


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
class LoadedMsiData:
    """Source-neutral MSI data ready for LipidQMap post-processing."""

    ion_mode: IonMode
    raw: dict[str, npt.NDArray]
    average_spectrum: npt.NDArray
    num_spectra: int
    coordinates: npt.NDArray
    pixel_size_um: tuple[float, float] | None = None
    stage_coordinates: npt.NDArray | None = None
    spot_ids: np.ndarray | None = None
    spot_index_lookup: dict[int, int] | None = None
    transparent_mask: npt.NDArray[np.bool_] | None = None


class AnnDataMatrixChoice(str, Enum):
    """AnnData matrix options exposed by the import dialog."""

    raw = "raw"
    batch_corrected = "batch_corrected"


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
        self.average_spectra_by_mode: dict[IonMode, npt.NDArray]
        self.num_spectra: int = 0
        self.coordinates: npt.NDArray = np.empty((0, 3), dtype=int)
        self.pixel_size_um: tuple[float, float] | None = None
        self.stage_coordinates: npt.NDArray | None = None
        self.spot_ids: np.ndarray | None = None
        self._spot_index_lookup: dict[int, int] | None = None
        self.na_isotope_correction_skipped_classes: list[str] = []
        loaded_data = self.load_data(
            progress_file_callback, database=database, imzml_path=imzml_path
        )
        self._process_loaded_data(progress_file_callback, database=database, data=loaded_data)

    @classmethod
    def from_loaded_data(
        cls,
        progress_file_callback,
        database: LipidDB,
        data: LoadedMsiData,
        config: Config,
    ) -> "SectionMsiImage":
        """Create a processed section image from source-neutral raw MSI data."""
        self = cls.__new__(cls)
        self.ion_mode = SampleIonMode.from_ion_mode(data.ion_mode)
        self._measurement_mode = data.ion_mode
        self.config = config
        self.database = database
        self.raw = {}
        self.isotope = {}
        self.quant = {}
        self.average_spectrum = np.empty((2, 0), dtype=np.float64)
        self.average_spectra_by_mode = {}
        self.num_spectra = 0
        self.coordinates = np.empty((0, 3), dtype=np.int32)
        self.pixel_size_um = None
        self.stage_coordinates = None
        self.spot_ids = None
        self._spot_index_lookup = None
        self.na_isotope_correction_skipped_classes = []
        self._process_loaded_data(progress_file_callback, database=database, data=data)
        return self

    def load_data(
        self, progress_file_callback, database: LipidDB, imzml_path: str
    ) -> LoadedMsiData:
        """
        Load raw images from the imzML file.

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
        coordinates = np.asarray(imzml_parser.coordinates, dtype=np.int32)
        stage_coordinates = self._extract_stage_coordinates(imzml_parser)
        spot_ids, spot_index_lookup = self._extract_spot_ids(imzml_parser)
        pixel_size_um = self._extract_pixel_size(imzml_parser)
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
        species_ids, species_mzs = database.get_all_species()
        ppm = self.config.settings.processing_settings.ppm
        tolerances = [ppm_to_tolerance(ppm=ppm, mz=mz) for mz in species_mzs]
        image_stack = get_ion_images(p=imzml_parser, mzs=species_mzs, tolerances=tolerances)
        raw = dict(zip(species_ids, list(image_stack)))
        progress_file_callback.emit(60)

        # calculate average spectrum
        bin_size = self.config.settings.processing_settings.bin_size
        average_spectrum = get_average_spectrum(p=imzml_parser, bin_size=bin_size, n_pixels=1000)
        if self._measurement_mode is None:
            raise ValueError("imzML loading requires a concrete ion mode.")
        return LoadedMsiData(
            ion_mode=self._measurement_mode,
            raw=raw,
            average_spectrum=average_spectrum,
            num_spectra=len(imzml_parser.coordinates),
            coordinates=coordinates,
            pixel_size_um=pixel_size_um,
            stage_coordinates=stage_coordinates,
            spot_ids=spot_ids,
            spot_index_lookup=spot_index_lookup,
        )

    def _process_loaded_data(
        self,
        progress_file_callback,
        database: LipidDB,
        data: LoadedMsiData,
    ) -> None:
        """Run source-independent LipidQMap processing on raw ion images."""
        self.ion_mode = SampleIonMode.from_ion_mode(data.ion_mode)
        self._measurement_mode = data.ion_mode
        self.raw = data.raw
        self.average_spectrum = data.average_spectrum
        self.average_spectra_by_mode = {data.ion_mode: data.average_spectrum}
        self.num_spectra = data.num_spectra
        self.coordinates = data.coordinates
        self.pixel_size_um = data.pixel_size_um
        self.stage_coordinates = data.stage_coordinates
        self.spot_ids = data.spot_ids
        self._spot_index_lookup = data.spot_index_lookup
        # perform isotope correction
        self.isotope = dict()
        if self.config.settings.processing_settings.na_isotope_correction:
            skipped_classes: set[str] = set()
            self.isotope = na_isotope_correction(
                database=database,
                images=self.raw,
                skipped_classes=skipped_classes,
            )
            self.na_isotope_correction_skipped_classes = sorted(skipped_classes)
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

        if data.transparent_mask is not None:
            self.raw = _apply_transparent_mask(self.raw, data.transparent_mask)  # type: ignore
            self.isotope = _apply_transparent_mask(self.isotope, data.transparent_mask)  # type: ignore
            self.quant = _apply_transparent_mask(self.quant, data.transparent_mask)

        # sum the different adduct forms of the same species
        neutral_suffix = "(+)" if data.ion_mode == IonMode.positive else "(-)"
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
        spot_ids, lookup = self._extract_spot_ids(parser)
        self.spot_ids = spot_ids
        self._spot_index_lookup = lookup

    @staticmethod
    def _extract_spot_ids(
        parser: ImzMLParser,
    ) -> tuple[np.ndarray | None, dict[int, int] | None]:
        parsed_ids = getattr(parser, "spot_ids", None)
        if not parsed_ids or not any(value is not None for value in parsed_ids):
            return None, None
        arr = np.full(len(parsed_ids), -1, dtype=np.int64)
        lookup: dict[int, int] = {}
        for idx, value in enumerate(parsed_ids):
            if value is None:
                continue
            spot_id = int(value)
            arr[idx] = spot_id
            lookup[spot_id] = idx
        return arr, lookup if lookup else None

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
                return float(np.nanmean(image, axis=(0, 1)))
            case ImageType.isotope:
                image = self.isotope.get(species_id)
                if image is None:
                    return 0
                return float(np.nanmean(image, axis=(0, 1)))
            case ImageType.quant:
                image = self.quant.get(species_id)
                if image is None:
                    return 0
                return float(np.nanmean(image, axis=(0, 1)))

    def get_average_spectrum_for_mode(self, ion_mode: IonMode | None = None) -> npt.NDArray:
        """Return the polarity-specific average spectrum when one is available."""
        if ion_mode is not None:
            spectrum = self.average_spectra_by_mode.get(ion_mode)
            if spectrum is not None:
                return spectrum
        return self.average_spectrum

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
        self.isotope = {
            key: func(value, param) if value is not None else value
            for (key, value) in self.isotope.items()
        }
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

    def get_spectrum(self, sample_id: str, ion_mode: IonMode | None = None) -> npt.NDArray:
        return self.samples[sample_id].get_average_spectrum_for_mode(ion_mode=ion_mode)

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
    """Merge two average spectra arrays, keeping mz values strictly sorted."""
    if primary.size == 0:
        return secondary
    if secondary.size == 0:
        return primary
    merged = np.concatenate((primary, secondary), axis=1)
    order = np.argsort(merged[0])
    merged = merged[:, order]

    # Collapse duplicated m/z bins so the chart series remains monotonic in combined mode.
    unique_mz, inverse = np.unique(merged[0], return_inverse=True)
    if unique_mz.shape[0] == merged.shape[1]:
        return merged

    summed_intensity = np.zeros(unique_mz.shape[0], dtype=merged.dtype)
    counts = np.zeros(unique_mz.shape[0], dtype=np.int32)
    np.add.at(summed_intensity, inverse, merged[1])
    np.add.at(counts, inverse, 1)
    averaged_intensity = summed_intensity / counts
    return np.vstack((unique_mz, averaged_intensity))


def _combine_section_images(
    images: list[tuple[IonMode, SectionMsiImage]],
) -> SectionMsiImage:
    """Combine one or more SectionMsiImage instances into a single multi-mode sample."""
    if not images:
        raise ValueError("No SectionMsiImage instances provided for combination.")
    base_mode, combined = images[0]
    for mode, image in images[1:]:
        if combined.raw and image.raw and combined.shape != image.shape:
            raise ValueError("Cannot combine samples with differing spatial dimensions.")
        combined.raw.update(image.raw)
        combined.isotope.update(image.isotope)
        combined.quant.update(image.quant)
        combined.average_spectra_by_mode.update(image.average_spectra_by_mode)
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
