from __future__ import annotations

import logging
import threading
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

from app.database import IonMode, LipidDB
from app.dataprocess import ImageType, SampleCollection, SectionMsiImage

logger = logging.getLogger(__name__)
ImageFrame = pd.DataFrame


class ScilsExportError(RuntimeError):
    """Raised when SCiLS export cannot be completed."""


class ScilsExportUnavailableError(ScilsExportError):
    """Raised when the SCiLS API is not available on the current platform."""


@dataclass(slots=True)
class ScilsExportReport:
    """Summary of a SCiLS export run."""

    exported_features: int
    skipped_species: list[str]
    dataset_path: Path


def export_score_spot_images(
    *,
    dataset_path: Path,
    samples: SampleCollection,
    sample_id: str,
    species_ids: Sequence[str],
    image_type: ImageType,
    database: LipidDB | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> ScilsExportReport:
    """Write processed ion images to a SCiLS dataset as score spot images."""

    section = _get_section(samples, sample_id)
    LocalSession = _load_local_session()

    skipped: list[str] = []
    exported = 0
    dataset_path = dataset_path.expanduser().resolve()
    total_species = len(species_ids)

    logger.info(
        "Exporting %s species from sample '%s' into SCiLS dataset %s as %s features",
        len(species_ids),
        sample_id,
        dataset_path,
        image_type.value,
    )

    session: Any | None = None

    try:
        try:
            session = LocalSession(filename=str(dataset_path))
        except RuntimeError as exc:  # dataset locked / server launch failure
            raise ScilsExportError(str(exc)) from exc

        dataset = session.dataset_proxy
        region_spots = dataset.get_region_spots("Regions")
        frame = _select_spot_frame(region_spots, section, preferred_sample_label=sample_id)
        spot_ids = _spot_ids_from_frame(frame)
        value_sampler = _prepare_value_sampler(frame, section)
        feature_table = dataset.feature_table
        feature_list_name = f"LipidQMap - {sample_id} ({_image_type_label(image_type)})"
        feature_list_id = feature_table.create_empty_feature_list(
            feature_list_name,
            allow_duplicate_name=True,
        )
        scils_spot_ids = spot_ids.astype(np.int64, copy=False).tolist()

        for index, species_id in enumerate(species_ids, start=1):
            image = section.get(image_type, species_id)
            if image is None:
                skipped.append(species_id)
                if progress_callback:
                    progress_callback(index, total_species or 1)
                continue

            try:
                values = _sanitize_values(value_sampler(image))
            except ScilsExportError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                raise ScilsExportError(str(exc)) from exc

            species_name = _species_display_name(database, species_id)

            try:
                feature_table.write_external_feature(
                    feature_list_id,
                    scils_spot_ids,
                    values.tolist(),
                    species_name,
                )
            except Exception as exc:  # pragma: no cover - relies on SCiLS runtime
                raise ScilsExportError(str(exc)) from exc

            exported += 1
            logger.debug(
                "Exported species '%s' with %s spot values to SCiLS feature list '%s'",
                species_name,
                len(values),
                feature_list_name,
            )
            if progress_callback:
                progress_callback(index, total_species or 1)
    finally:
        _shutdown_session_async(session)

    return ScilsExportReport(
        exported_features=exported,
        skipped_species=skipped,
        dataset_path=dataset_path,
    )


def _get_section(samples: SampleCollection, sample_id: str) -> SectionMsiImage:
    try:
        return samples.samples[sample_id]
    except KeyError as exc:
        raise ScilsExportError(f"Sample '{sample_id}' is not available.") from exc


def _load_local_session():
    try:
        from scilslab import LocalSession  # type: ignore
    except ImportError as exc:  # pragma: no cover - platform-specific
        raise ScilsExportUnavailableError(
            "SCiLS export is only available on Windows because the SCiLS Lab API "
            "does not provide wheels for other platforms."
        ) from exc
    return LocalSession


def _select_spot_frame(
    region_spots: Any,
    section: SectionMsiImage,
    *,
    preferred_sample_label: str | None = None,
) -> ImageFrame:
    df = _as_dataframe(region_spots)
    required = {"spot_id", "x", "y"}
    missing = required - set(df.columns)
    if missing:
        raise ScilsExportError(
            f"SCiLS dataset is missing required spot metadata columns: {sorted(missing)}"
        )

    candidate_groups = _candidate_frames(df, preferred_sample_label)
    sample_coords = _normalized_coords(section.coordinates, section.shape)
    coord_set = _coords_set(sample_coords)
    logger.debug(
        "Sample '%s' contains %s pixels (shape=%s)",
        preferred_sample_label or "<unknown>",
        len(sample_coords),
        section.shape,
    )

    for key, frame in candidate_groups:
        frame_coords = _frame_coords(frame)
        if frame_coords.shape[0] != sample_coords.shape[0]:
            logger.debug(
                "Skipping SCiLS measurement '%s' because spot counts differ (SCiLS=%s vs sample=%s)",
                _measurement_label(key, frame),
                frame_coords.shape[0],
                sample_coords.shape[0],
            )
            continue
        if _coords_set(frame_coords) == coord_set:
            logger.info(
                "Matched SCiLS measurement '%s' with %s spots",
                _measurement_label(key, frame),
                frame_coords.shape[0],
            )
            return frame

        logger.warning(
            "Coordinate mismatch for measurement '%s'; first SCiLS coord=%s, sample coord=%s. "
            "Proceeding with export despite mismatch.",
            _measurement_label(key, frame),
            frame_coords[:1].tolist(),
            sample_coords[:1].tolist(),
        )
        return frame

    raise ScilsExportError(
        "Could not find a measurement in the SCiLS dataset that matches the loaded imzML file.\n"
        "Please ensure you picked the SCiLS dataset that corresponds to the currently selected image."
    )


def _as_dataframe(region_spots: Any) -> ImageFrame:
    if isinstance(region_spots, pd.DataFrame):
        return region_spots
    return pd.DataFrame(region_spots)


def _candidate_frames(
    df: ImageFrame, preferred_sample_label: str | None
) -> list[tuple[Any, ImageFrame]]:
    grouping_columns = [
        col for col in ("sample_id", "sample", "run", "measurement", "raster") if col in df.columns
    ]
    if not grouping_columns:
        logger.debug(
            "SCiLS dataset does not contain grouping columns; treating entire region as one measurement"
        )
        return [(None, df)]

    column = grouping_columns[0]
    groups: list[tuple[Any, ImageFrame]] = list(df.groupby(column, sort=False))
    if preferred_sample_label is None:
        return groups

    for key, frame in groups:
        if str(key).lower() == preferred_sample_label.lower():
            logger.debug("Preferencing SCiLS measurement '%s' based on sample label match", key)
            return [(key, frame)]
    return groups


def _normalized_coords(coords: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    if coords.size == 0:
        width, height = shape[1], shape[0]
        xs = np.tile(np.arange(1, width + 1, dtype=np.int32), height)
        ys = np.repeat(np.arange(1, height + 1, dtype=np.int32), width)
        zeros = np.zeros_like(xs)
        return np.column_stack((xs, ys, zeros))

    coords = np.asarray(coords, dtype=np.int32)
    if coords.shape[1] == 2:
        zeros = np.zeros(coords.shape[0], dtype=np.int32)
        return np.column_stack((coords, zeros))
    return coords[:, :3]


def _frame_coords(frame: ImageFrame) -> np.ndarray:
    x = frame["x"].to_numpy(dtype=np.int32, copy=False)
    y = frame["y"].to_numpy(dtype=np.int32, copy=False)
    if "z" in frame.columns:
        z = frame["z"].fillna(0).to_numpy(dtype=np.int32, copy=False)
    else:
        z = np.zeros(len(frame), dtype=np.int32)
    return np.column_stack((x, y, z))


def _coords_set(coords: np.ndarray) -> set[tuple[int, int, int]]:
    return set(map(tuple, coords.tolist()))


def _spot_ids_from_frame(frame: ImageFrame) -> np.ndarray:
    try:
        return frame["spot_id"].to_numpy(dtype=np.uint64, copy=True)
    except ValueError as exc:
        raise ScilsExportError("SCiLS spot identifiers must be numeric.") from exc


def _prepare_value_sampler(frame: ImageFrame, section: SectionMsiImage):
    spot_lookup = getattr(section, "_spot_index_lookup", None)
    if spot_lookup and "spot_id" in frame.columns:
        scils_spot_ids = frame["spot_id"].to_numpy(copy=False)
        if scils_spot_ids.dtype.kind not in {"i", "u"}:
            scils_spot_ids = scils_spot_ids.astype(np.int64, copy=False)

        def sampler(image: np.ndarray) -> np.ndarray:
            return _sample_by_spot_ids(image, section, scils_spot_ids, spot_lookup)

        return sampler

    if not {"x", "y"}.issubset(frame.columns):
        raise ScilsExportError("SCiLS dataset is missing required coordinate columns.")

    x_coords = frame["x"].to_numpy(dtype=np.int32, copy=False)
    y_coords = frame["y"].to_numpy(dtype=np.int32, copy=False)

    def sampler(image: np.ndarray) -> np.ndarray:
        return _sample_by_coords(image, x_coords, y_coords)

    return sampler


def _sample_by_coords(image: np.ndarray, x_coords: np.ndarray, y_coords: np.ndarray) -> np.ndarray:
    if image is None or image.ndim != 2:
        raise ScilsExportError("Only 2D ion images can be exported to SCiLS.")
    try:
        values = image[y_coords - 1, x_coords - 1]
    except IndexError as exc:
        raise ScilsExportError("Image dimensions do not match SCiLS dataset coordinates.") from exc
    return np.ascontiguousarray(np.asarray(values, dtype=np.float32))


def _sample_by_spot_ids(
    image: np.ndarray,
    section: SectionMsiImage,
    scils_spot_ids: np.ndarray,
    lookup: dict[int, int],
) -> np.ndarray:
    if image is None or image.ndim != 2:
        raise ScilsExportError("Only 2D ion images can be exported to SCiLS.")
    values = np.empty(len(scils_spot_ids), dtype=np.float32)
    coords = section.coordinates
    for idx, spot_id in enumerate(scils_spot_ids):
        sample_idx = lookup.get(int(spot_id))
        if sample_idx is None:
            raise ScilsExportError(f"Spot ID '{spot_id}' is not present in the loaded imzML data.")
        x, y = coords[sample_idx, 0], coords[sample_idx, 1]
        values[idx] = _sample_pixel(image, x, y)
    return np.ascontiguousarray(values)


def _sample_pixel(image: np.ndarray, x: int, y: int) -> float:
    try:
        return float(image[int(y) - 1, int(x) - 1])
    except IndexError as exc:
        raise ScilsExportError("Image dimensions do not match SCiLS dataset coordinates.") from exc


def _sanitize_values(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float32)
    # Replace NaN and infinities with zero to satisfy SCiLS constraints
    np.nan_to_num(arr, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
    return arr


def _species_display_name(database: LipidDB | None, species_id: str) -> str:
    if database is None:
        return species_id
    specie = database.species.get(species_id)
    if specie is None and species_id.endswith((" (+)", " (-)")):
        # summed species are stored without suffix in the combined database
        specie = database.species.get(species_id[:-4])
    if specie is None:
        return species_id
    if specie.adduct in {"", "(+)", "(-)"} and specie.ion_mode in {
        IonMode.positive,
        IonMode.negative,
    }:
        suffix = "(+)" if specie.ion_mode == IonMode.positive else "(-)"
        return f"{specie.id} {suffix}"
    return specie.id_adduct


def _image_type_label(image_type: ImageType) -> str:
    return {
        ImageType.raw: "Raw",
        ImageType.isotope: "Isotope corrected",
        ImageType.quant: "Quantified",
    }[image_type]


def _measurement_label(group_key: Any, frame: ImageFrame) -> str:
    if group_key not in (None, ""):
        return str(group_key)
    for column in ("sample_id", "sample", "run", "measurement", "raster"):
        if column in frame.columns and frame[column].notna().any():
            return str(frame[column].iloc[0])
    return "<unnamed measurement>"


def _shutdown_session_async(session: Any | None) -> None:
    if session is None:
        return

    def _run() -> None:
        try:
            session.close()
        except Exception as exc:  # pragma: no cover - depends on SCiLS runtime
            logger.warning("SCILS session reported an error while closing: %s", exc)
            _force_terminate_session(session)

    threading.Thread(
        target=_run,
        name="ScilsSessionShutdown",
        daemon=True,
    ).start()

def _force_terminate_session(session: Any) -> None:
    process = getattr(session, "process", None)
    if process is not None and process.poll() is None:
        with suppress(Exception):
            process.kill()

    finalizer = getattr(session, "_finalizer", None)
    if finalizer is not None:
        with suppress(Exception):
            finalizer.detach()
        with suppress(Exception):
            session._finalizer = None  # type: ignore[attr-defined]

    for handle_name in ("_stdout_readhandle", "_stdout_writehandle"):
        handle = getattr(session, handle_name, None)
        if handle is not None:
            with suppress(Exception):
                handle.close()

    temp_dir = getattr(session, "_temp_dir", None)
    if temp_dir is not None:
        with suppress(Exception):
            temp_dir.cleanup()
