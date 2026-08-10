from __future__ import annotations

import logging
import re
import threading
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

from app.database import IonMode, LipidDB
from app.msi_data import ImageType, SampleCollection, SectionMsiImage

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
    feature_list_id: int


def export_score_spot_images(
    *,
    dataset_path: Path,
    samples: SampleCollection,
    sample_id: str,
    species_ids: Sequence[str],
    image_type: ImageType,
    database: LipidDB | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    status_callback: Callable[[str], None] | None = None,
    feature_aggregate: dict[str, list[tuple[list[int], list[float]]]] | None = None,
) -> ScilsExportReport:
    """Write processed ion images to a SCiLS dataset as score spot images."""

    if status_callback:
        status_callback(f"Connecting to SCiLS for sample '{sample_id}'...")

    section = _get_section(samples, sample_id)
    LocalSession = _load_local_session()

    skipped: list[str] = []
    exported = 0
    dataset_path = dataset_path.expanduser().resolve()
    total_species = len(species_ids)

    logger.debug(
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

        if status_callback:
            status_callback(f"Inspecting SCiLS coordinates for sample '{sample_id}'...")
        dataset = session.dataset_proxy
        region_spots = _region_spots_for_sample(dataset, section, sample_id)
        frame = _select_spot_frame(
            region_spots, section, preferred_sample_label=sample_id
        )
        coord_transform = _fit_coordinate_transform(frame, section)
        spot_ids = _spot_ids_from_frame(frame)
        value_sampler = _prepare_value_sampler(
            frame, section, coord_transform=coord_transform
        )
        feature_table = dataset.feature_table
        feature_list_name = f"LipidQMap - {sample_id} ({_image_type_label(image_type)})"
        feature_list_id: int | None = None
        if feature_aggregate is None:
            feature_list_id = feature_table.create_empty_feature_list(
                feature_list_name,
                allow_duplicate_name=True,
            )
        scils_spot_ids = spot_ids.astype(np.int64, copy=False).tolist()

        for index, species_id in enumerate(species_ids, start=1):
            species_name = _species_display_name(database, species_id)
            if status_callback:
                status_callback(
                    f"Preparing {_image_type_label(image_type).lower()} feature "
                    f"{index} of {total_species}: {species_name}"
                )
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

            if feature_aggregate is None:
                try:
                    feature_table.write_external_feature(
                        feature_list_id,
                        scils_spot_ids,
                        values.tolist(),
                        species_name,
                    )
                except Exception as exc:  # pragma: no cover - relies on SCiLS runtime
                    raise ScilsExportError(str(exc)) from exc
            else:
                feature_aggregate.setdefault(species_name, []).append(
                    (scils_spot_ids.copy(), values.tolist())
                )

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
        feature_list_id=feature_list_id or -1,
    )


def _get_section(samples: SampleCollection, sample_id: str) -> SectionMsiImage:
    try:
        return samples.samples[sample_id]
    except KeyError as exc:
        raise ScilsExportError(f"Sample '{sample_id}' is not available.") from exc


def _region_spots_for_sample(
    dataset: Any,
    section: SectionMsiImage,
    sample_id: str,
) -> Any:
    """Prefer a named SCiLS measurement region over the all-spots root."""
    try:
        region_tree = dataset.get_region_tree()
        regions = region_tree.get_all_regions()
    except (AttributeError, RuntimeError, ValueError) as exc:
        logger.debug("Could not inspect the SCiLS region tree: %s", exc)
    else:
        sample_key = _measurement_name_key(sample_id)
        matches = [
            region
            for region in regions
            if getattr(region, "id", None) != "Regions"
            and _measurement_name_key(getattr(region, "name", "")) == sample_key
        ]
        if matches:
            expected_count = len(section.coordinates)
            region = min(
                matches,
                key=lambda item: abs(
                    len(getattr(item, "spots", {}).get("spot_id", ())) - expected_count
                ),
            )
            logger.debug(
                "Matched sample '%s' to SCiLS region '%s' (%s spots)",
                sample_id,
                getattr(region, "name", "<unnamed>"),
                len(region.spots.get("spot_id", ())),
            )
            return region.spots

    return dataset.get_region_spots("Regions")


def _measurement_name_key(label: Any) -> tuple[str, ...]:
    leaf = str(label).replace("\\", "/").rsplit("/", 1)[-1]
    tokens = re.findall(r"[a-z]+|\d+", leaf.casefold())
    return tuple(str(int(token)) if token.isdigit() else token for token in tokens)


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
    sample_coords = _section_match_coords(section)
    coord_set = _coords_set(sample_coords)
    sample_spot_ids = _normalized_spot_ids(getattr(section, "spot_ids", None))
    best_candidate: tuple[str, ImageFrame, np.ndarray, float] | None = None
    best_score = float("inf")

    for key, frame in candidate_groups:
        label = _measurement_label(key, frame)
        frame_coords = _frame_coords(frame)
        if frame_coords.shape[0] != sample_coords.shape[0]:
            logger.debug(
                "Skipping SCiLS measurement '%s' because spot counts differ (SCiLS=%s vs sample=%s)",
                label,
                frame_coords.shape[0],
                sample_coords.shape[0],
            )
            continue

        if sample_spot_ids is not None:
            frame_spot_ids = _sorted_spot_ids_from_frame(frame)
            if frame_spot_ids.shape == sample_spot_ids.shape and np.array_equal(
                frame_spot_ids, sample_spot_ids
            ):
                logger.debug(
                    "Matched SCiLS measurement '%s' using spot identifiers (%s spots)",
                    label,
                    frame_coords.shape[0],
                )
                return frame
        if sample_spot_ids is None:
            coords_match = _coords_set(frame_coords) == coord_set
            if coords_match:
                logger.debug(
                    "Matched SCiLS measurement '%s' with %s spots",
                    label,
                    frame_coords.shape[0],
                )
                return frame

        score = _coordinate_distance(frame_coords, sample_coords)
        if score < best_score:
            best_score = score
            best_candidate = (label, frame, frame_coords, score)

    if best_candidate is not None:
        label, frame, frame_coords, score = best_candidate
        logger.debug(
            "Matched SCiLS measurement '%s' with %s spots based on closest coordinate arrangement "
            "(avg delta=%.2f)",
            label,
            frame_coords.shape[0],
            score,
        )
        return frame

    if candidate_groups:
        label = _measurement_label(candidate_groups[0][0], candidate_groups[0][1])
        frame_coords = _frame_coords(candidate_groups[0][1])
        logger.warning(
            "Coordinate mismatch for measurement '%s'; first SCiLS coord=%s, sample coord=%s. "
            "Proceeding with export despite mismatch.",
            label,
            frame_coords[:1].tolist(),
            sample_coords[:1].tolist(),
        )
        return candidate_groups[0][1]

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
        col
        for col in ("sample_id", "sample", "run", "measurement", "raster")
        if col in df.columns
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

    matches: list[tuple[Any, ImageFrame]] = []
    others: list[tuple[Any, ImageFrame]] = []
    for key, frame in groups:
        if str(key).lower() == preferred_sample_label.lower():
            matches.append((key, frame))
        else:
            others.append((key, frame))

    if matches:
        logger.debug(
            "Preferencing SCiLS measurement '%s' based on sample label match",
            matches[0][0],
        )
        return matches + others
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


def _section_match_coords(section: SectionMsiImage) -> np.ndarray:
    stage_coords = getattr(section, "stage_coordinates", None)
    stage_normalized = _normalized_stage_coords(stage_coords)
    if stage_normalized is not None:
        return stage_normalized
    return _normalized_coords(section.coordinates, section.shape)


def _normalized_stage_coords(stage_coords: np.ndarray | None) -> np.ndarray | None:
    if stage_coords is None:
        return None
    arr = np.asarray(stage_coords, dtype=np.float64)
    if arr.size == 0:
        return None
    if arr.ndim != 2:
        return None
    arr = arr[:, :3]
    if not np.isfinite(arr).all():
        return None
    rounded = np.rint(arr).astype(np.int64)
    return rounded


def _coordinate_distance(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape or a.size == 0:
        return float("inf")
    a_sorted = _sorted_coords(a)
    b_sorted = _sorted_coords(b)
    diff = np.abs(a_sorted.astype(np.float64) - b_sorted.astype(np.float64))
    return float(diff.mean())


def _sorted_coords(coords: np.ndarray) -> np.ndarray:
    if coords.ndim != 2 or coords.shape[1] < 3:
        return coords
    order = np.lexsort((coords[:, 2], coords[:, 1], coords[:, 0]))
    return coords[order]


def _normalized_spot_ids(spot_ids: np.ndarray | None) -> np.ndarray | None:
    if spot_ids is None:
        return None
    arr = np.asarray(spot_ids, dtype=np.int64)
    if arr.size == 0:
        return None
    valid = arr >= 0
    normalized = arr[valid]
    if normalized.size == 0:
        return None
    normalized.sort()
    return normalized


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


def _fit_coordinate_transform(
    frame: ImageFrame,
    section: SectionMsiImage,
) -> tuple[np.ndarray, np.ndarray] | None:
    try:
        scils_coords = _frame_coords(frame)[:, :2].astype(np.float64, copy=False)
        pixel_coords = np.asarray(section.coordinates[:, :2], dtype=np.float64)
    except Exception:
        return None
    if scils_coords.shape[0] < 2 or pixel_coords.shape[0] < 2:
        return None

    x_transform = _axis_endpoint_transform(scils_coords[:, 0], pixel_coords[:, 0])
    y_transform = _axis_endpoint_transform(scils_coords[:, 1], pixel_coords[:, 1])
    if x_transform is None or y_transform is None:
        return None

    target_set = set(map(tuple, np.rint(pixel_coords).astype(np.int64).tolist()))
    preferred_x_sign = _stage_axis_transform_sign(section, axis=0)
    preferred_y_sign = _stage_axis_transform_sign(section, axis=1)
    best: tuple[np.ndarray, np.ndarray] | None = None
    best_score = (-1, -1)
    for x_scale, x_offset in x_transform:
        for y_scale, y_offset in y_transform:
            px = np.rint(scils_coords[:, 0] * x_scale + x_offset).astype(np.int64)
            py = np.rint(scils_coords[:, 1] * y_scale + y_offset).astype(np.int64)
            overlap = sum((int(x), int(y)) in target_set for x, y in zip(px, py))
            direction_matches = int(
                preferred_x_sign is not None and np.sign(x_scale) == preferred_x_sign
            ) + int(
                preferred_y_sign is not None and np.sign(y_scale) == preferred_y_sign
            )
            score = (overlap, direction_matches)
            if score > best_score:
                best_score = score
                best = (
                    np.array([x_scale, 0.0, x_offset], dtype=np.float64),
                    np.array([0.0, y_scale, y_offset], dtype=np.float64),
                )

    if best is not None:
        logger.debug(
            "Fitted SCiLS coordinate transform by geometry (%s/%s coordinates overlap)",
            best_score[0],
            scils_coords.shape[0],
        )
    return best


def _stage_axis_transform_sign(section: SectionMsiImage, axis: int) -> float | None:
    stage_coords = getattr(section, "stage_coordinates", None)
    if stage_coords is None:
        return None
    stage = np.asarray(stage_coords, dtype=np.float64)
    pixels = np.asarray(section.coordinates, dtype=np.float64)
    if (
        stage.ndim != 2
        or pixels.ndim != 2
        or stage.shape[0] != pixels.shape[0]
        or stage.shape[1] <= axis
        or pixels.shape[1] <= axis
    ):
        return None
    valid = np.isfinite(stage[:, axis]) & np.isfinite(pixels[:, axis])
    if np.count_nonzero(valid) < 2:
        return None
    covariance = np.cov(stage[valid, axis], pixels[valid, axis])[0, 1]
    if not np.isfinite(covariance) or covariance == 0:
        return None
    return float(np.sign(covariance))


def _axis_endpoint_transform(
    source: np.ndarray,
    target: np.ndarray,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    source_min = float(np.min(source))
    source_max = float(np.max(source))
    target_min = float(np.min(target))
    target_max = float(np.max(target))
    source_span = source_max - source_min
    target_span = target_max - target_min
    if source_span == 0 or target_span == 0:
        return None

    forward_scale = target_span / source_span
    reverse_scale = -forward_scale
    return (
        (forward_scale, target_min - source_min * forward_scale),
        (reverse_scale, target_max - source_min * reverse_scale),
    )


def _apply_coordinate_transform(
    x_coords: np.ndarray,
    y_coords: np.ndarray,
    transform: tuple[np.ndarray, np.ndarray],
    shape: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray]:
    coeff_x, coeff_y = transform
    coords = np.column_stack(
        [
            x_coords.astype(np.float64, copy=False),
            y_coords.astype(np.float64, copy=False),
            np.ones_like(x_coords, dtype=np.float64),
        ]
    )
    px = coords @ coeff_x
    py = coords @ coeff_y
    px = np.rint(px).astype(np.int32, copy=False)
    py = np.rint(py).astype(np.int32, copy=False)
    width = shape[1]
    height = shape[0]
    px = np.clip(px, 1, width)
    py = np.clip(py, 1, height)
    return px, py


def write_aggregated_features(
    *,
    dataset_path: Path,
    feature_list_label: str,
    image_type: ImageType,
    aggregate: dict[str, list[tuple[list[int], list[float]]]],
    skipped_species: list[str] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    status_callback: Callable[[str], None] | None = None,
) -> ScilsExportReport:
    if not aggregate:
        return ScilsExportReport(
            exported_features=0,
            skipped_species=skipped_species or [],
            dataset_path=dataset_path,
            feature_list_id=-1,
        )

    if status_callback:
        status_callback(
            f"Connecting to SCiLS to write {_image_type_label(image_type).lower()} features..."
        )

    LocalSession = _load_local_session()
    session: Any | None = None
    exported = 0

    try:
        session = LocalSession(filename=str(dataset_path))
        if status_callback:
            status_callback(f"Creating SCiLS feature list '{feature_list_label}'...")
        feature_table = session.dataset_proxy.feature_table
        feature_list_id = feature_table.create_empty_feature_list(
            feature_list_label,
            allow_duplicate_name=True,
        )
        total_features = len(aggregate)
        for index, (species_name, batches) in enumerate(aggregate.items(), start=1):
            if status_callback:
                status_callback(
                    f"Writing feature {index} of {total_features} to SCiLS: {species_name}"
                )
            spot_ids, values = _merge_feature_batches(batches)
            if spot_ids:
                try:
                    feature_table.write_external_feature(
                        feature_list_id,
                        spot_ids,
                        values,
                        species_name,
                    )
                except Exception as exc:  # pragma: no cover - relies on SCiLS runtime
                    raise ScilsExportError(str(exc)) from exc
                exported += 1
            if progress_callback:
                progress_callback(index, total_features)
        if status_callback:
            status_callback("Finalizing the SCiLS export...")
    finally:
        _shutdown_session_async(session)

    return ScilsExportReport(
        exported_features=exported,
        skipped_species=skipped_species or [],
        dataset_path=dataset_path,
        feature_list_id=feature_list_id,
    )


def _merge_feature_batches(
    batches: list[tuple[list[int], list[float]]],
) -> tuple[list[int], list[float]]:
    if not batches:
        return [], []
    merged: list[tuple[int, float]] = []
    for batch_spots, batch_values in batches:
        merged.extend((int(s), float(v)) for s, v in zip(batch_spots, batch_values))
    merged.sort(key=lambda item: item[0])
    if not merged:
        return [], []
    spot_ids, values = zip(*merged)
    return list(spot_ids), list(values)


def _spot_ids_from_frame(frame: ImageFrame) -> np.ndarray:
    try:
        return frame["spot_id"].to_numpy(dtype=np.uint64, copy=True)
    except ValueError as exc:
        raise ScilsExportError("SCiLS spot identifiers must be numeric.") from exc


def _sorted_spot_ids_from_frame(frame: ImageFrame) -> np.ndarray:
    spot_ids = _spot_ids_from_frame(frame)
    if spot_ids.dtype != np.int64:
        spot_ids = spot_ids.astype(np.int64, copy=False)
    spot_ids.sort()
    return spot_ids


def _first_missing_spot_id(
    scils_spot_ids: np.ndarray, lookup: dict[int, int]
) -> int | None:
    for spot_id in scils_spot_ids:
        if lookup.get(int(spot_id)) is None:
            return int(spot_id)
    return None


def _prepare_value_sampler(
    frame: ImageFrame,
    section: SectionMsiImage,
    *,
    coord_transform: tuple[np.ndarray, np.ndarray] | None = None,
):
    if not {"x", "y"}.issubset(frame.columns):
        raise ScilsExportError("SCiLS dataset is missing required coordinate columns.")

    x_coords = frame["x"].to_numpy(dtype=np.float64, copy=False)
    y_coords = frame["y"].to_numpy(dtype=np.float64, copy=False)
    if coord_transform is not None:
        # SCiLS spot IDs and imzML spectrum IDs are independent namespaces. Their
        # numeric values can overlap even when they refer to different pixels, so
        # a verified physical-coordinate transform must take precedence.
        x_coords, y_coords = _apply_coordinate_transform(
            x_coords,
            y_coords,
            coord_transform,
            section.shape,
        )

        def sampler(image: np.ndarray) -> np.ndarray:
            return _sample_by_coords(image, x_coords, y_coords)

        return sampler

    spot_lookup = getattr(section, "_spot_index_lookup", None)
    if spot_lookup and "spot_id" in frame.columns:
        scils_spot_ids = frame["spot_id"].to_numpy(copy=False)
        if scils_spot_ids.dtype.kind not in {"i", "u"}:
            scils_spot_ids = scils_spot_ids.astype(np.int64, copy=False)

        missing = _first_missing_spot_id(scils_spot_ids, spot_lookup)
        if missing is None:

            def sampler(image: np.ndarray) -> np.ndarray:
                return _sample_by_spot_ids(image, section, scils_spot_ids, spot_lookup)

            return sampler

        logger.debug(
            "SCiLS spot identifiers do not match the loaded imzML; falling back to coordinate sampling "
            "(first missing spot id=%s)",
            missing,
        )

    x_coords = x_coords.astype(np.int32, copy=False)
    y_coords = y_coords.astype(np.int32, copy=False)

    def sampler(image: np.ndarray) -> np.ndarray:
        return _sample_by_coords(image, x_coords, y_coords)

    return sampler


def _sample_by_coords(
    image: np.ndarray, x_coords: np.ndarray, y_coords: np.ndarray
) -> np.ndarray:
    if image is None or image.ndim != 2:
        raise ScilsExportError("Only 2D ion images can be exported to SCiLS.")
    try:
        values = image[y_coords - 1, x_coords - 1]
    except IndexError as exc:
        height, width = image.shape
        logger.error(
            "Image sampling failed: image_shape=(%s,%s), requested x range [%s,%s], y range [%s,%s]",
            height,
            width,
            int(np.min(x_coords)),
            int(np.max(x_coords)),
            int(np.min(y_coords)),
            int(np.max(y_coords)),
        )
        raise ScilsExportError(
            "Image dimensions do not match SCiLS dataset coordinates."
        ) from exc
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
            raise ScilsExportError(
                f"Spot ID '{spot_id}' is not present in the loaded imzML data."
            )
        x, y = coords[sample_idx, 0], coords[sample_idx, 1]
        values[idx] = _sample_pixel(image, x, y)
    return np.ascontiguousarray(values)


def _sample_pixel(image: np.ndarray, x: int, y: int) -> float:
    try:
        return float(image[int(y) - 1, int(x) - 1])
    except IndexError as exc:
        height, width = image.shape
        logger.error(
            "Pixel sampling failed: image_shape=(%s,%s), requested x=%s, y=%s",
            height,
            width,
            x,
            y,
        )
        raise ScilsExportError(
            "Image dimensions do not match SCiLS dataset coordinates."
        ) from exc


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
