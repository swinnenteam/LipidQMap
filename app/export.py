from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import h5py
import numpy as np
import pandas as pd
import pandas.api.types as pdt

from app import __version__
from app.dataprocess import ImageType, SampleCollection
from app.database import LipidDB


class CardinalExportError(RuntimeError):
    """Raised when a Cardinal HDF5 export cannot be completed."""


def export_cardinal_hdf5(
    filepath: str | Path,
    samples: SampleCollection,
    database: LipidDB,
    species_ids: Sequence[str],
    *,
    image_type: ImageType = ImageType.quant,
) -> Path:
    """Export MSI data to the Cardinal HDF5 format.

    Parameters
    ----------
    filepath:
        Target path for the HDF5 file. The ``.h5`` suffix is appended automatically when missing.
    samples:
        Collection of loaded MSI samples.
    database:
        Database that defines the lipid species metadata.
    species_ids:
        Ordered list of species identifiers that should be exported.
    image_type:
        Which images to export. Defaults to quantitative images.

    Returns
    -------
    pathlib.Path
        The final path of the written file.
    """

    if len(samples) == 0:
        raise CardinalExportError("There are no samples to export.")
    if not species_ids:
        raise CardinalExportError("There are no species marked for export.")

    output_path = Path(filepath)
    if output_path.suffix.lower() not in {".h5", ".hdf5"}:
        output_path = output_path.with_suffix(".h5")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pixel_df = _build_pixel_dataframe(samples)
    feature_df = _build_feature_dataframe(database, species_ids)
    intensity_matrix = _build_intensity_matrix(samples, species_ids, image_type)

    if intensity_matrix.shape != (len(feature_df), len(pixel_df)):
        raise CardinalExportError(
            "Exported intensity matrix shape does not match feature or pixel dimensions."
        )

    _write_hdf5(
        output_path,
        intensity_matrix=intensity_matrix,
        pixel_df=pixel_df,
        feature_df=feature_df,
        samples=samples,
        image_type=image_type,
    )

    return output_path


def _build_pixel_dataframe(samples: SampleCollection) -> pd.DataFrame:
    """Construct the pixel coordinate table for all samples."""
    pixel_tables: list[pd.DataFrame] = []
    running_index = 0
    for sample_index, (sample_id, section) in enumerate(samples.items(), start=1):
        coords_arr = getattr(section, "coordinates", None)
        if coords_arr is not None and coords_arr.size > 0:
            x_coords = coords_arr[:, 0].astype(np.int32)
            y_coords = coords_arr[:, 1].astype(np.int32)
        else:
            height, width = section.shape
            x_coords = np.tile(np.arange(1, width + 1, dtype=np.int32), height)
            y_coords = np.repeat(np.arange(1, height + 1, dtype=np.int32), width)
        pixel_count = len(x_coords)
        pixel_index = np.arange(running_index + 1, running_index + pixel_count + 1, dtype=np.int64)
        sample_index_array = np.full(pixel_count, sample_index, dtype=np.int32)
        run_labels = np.full(pixel_count, sample_id, dtype=object)

        pixel_tables.append(
            pd.DataFrame(
                {
                    "pixel_index": pixel_index,
                    "x": x_coords,
                    "y": y_coords,
                    "sample_index": sample_index_array,
                    "run": run_labels,
                    "sample_id": run_labels,
                }
            )
        )
        running_index += pixel_count

    return pd.concat(pixel_tables, ignore_index=True)


def _build_feature_dataframe(database: LipidDB, species_ids: Sequence[str]) -> pd.DataFrame:
    """Collect feature metadata for the exported species."""
    records: list[dict[str, object]] = []
    for feature_index, species_id in enumerate(species_ids, start=1):
        specie = database.species.get(species_id)
        if specie is None:
            raise CardinalExportError(f"Species '{species_id}' is not present in the database.")
        records.append(
            {
                "feature_index": feature_index,
                "feature_id": species_id,
                "mz": float(specie.mz),
                "lipid_class": specie.lipid_class,
                "adduct": specie.adduct,
                "neutral_id": specie.id,
                "is_standard": bool(specie.is_standard),
            }
        )

    return pd.DataFrame.from_records(records)


def _build_intensity_matrix(
    samples: SampleCollection,
    species_ids: Sequence[str],
    image_type: ImageType,
) -> np.ndarray:
    """Build the feature-by-pixel intensity matrix."""
    feature_stack: list[np.ndarray] = []
    for species_id in species_ids:
        pixel_values: list[np.ndarray] = []
        for _, section in samples.items():
            coords_arr = getattr(section, "coordinates", None)
            image = _extract_image(section, species_id, image_type)
            if image is None:
                if coords_arr is not None and coords_arr.size > 0:
                    pixel_count = coords_arr.shape[0]
                else:
                    pixel_count = section.shape[0] * section.shape[1]
                image_vector = np.full(pixel_count, np.nan, dtype=np.float32)
            else:
                image_array = np.asarray(image, dtype=np.float32)
                if coords_arr is not None and coords_arr.size > 0:
                    x_idx = coords_arr[:, 0].astype(int) - 1
                    y_idx = coords_arr[:, 1].astype(int) - 1
                    image_vector = image_array[y_idx, x_idx]
                else:
                    image_vector = image_array.ravel(order="C")
            pixel_values.append(image_vector)
        if pixel_values:
            feature_stack.append(np.concatenate(pixel_values))

    if not feature_stack:
        return np.empty((0, 0), dtype=np.float32)

    return np.vstack(feature_stack)


def _extract_image(section, species_id: str, image_type: ImageType):
    """Return the preferred image array for a species, falling back to raw intensities."""
    containers: Iterable[dict[str, np.ndarray | None]]
    match image_type:
        case ImageType.raw:
            containers = (section.raw,)
        case ImageType.isotope:
            containers = (section.isotope, section.raw)
        case ImageType.quant:
            containers = (section.quant, section.isotope, section.raw)
        case _:
            containers = (section.quant, section.isotope, section.raw)

    for container in containers:
        if container is None:
            continue
        image = container.get(species_id)
        if image is not None:
            return image
    return None


def _write_hdf5(
    output_path: Path,
    *,
    intensity_matrix: np.ndarray,
    pixel_df: pd.DataFrame,
    feature_df: pd.DataFrame,
    samples: SampleCollection,
    image_type: ImageType,
) -> None:
    """Write the assembled data to an HDF5 container compatible with Cardinal."""
    with h5py.File(output_path, "w") as h5:
        h5.attrs["format"] = "Cardinal::HDF5"
        h5.attrs["creator"] = "LipidQMap"
        h5.attrs["creator_version"] = __version__
        h5.attrs["image_type"] = image_type.value

        spectra_group = h5.create_group("spectraData")
        spectra_group.create_dataset(
            "intensity",
            data=intensity_matrix.astype(np.float32),
            compression="gzip",
            compression_opts=4,
            shuffle=True,
        )
        spectra_group.attrs["n_features"] = intensity_matrix.shape[0]
        spectra_group.attrs["n_spectra"] = intensity_matrix.shape[1]

        pixel_group = h5.create_group("pixelData")
        _write_dataframe(pixel_group, pixel_df)

        feature_group = h5.create_group("featureData")
        _write_dataframe(feature_group, feature_df)

        samples_group = h5.create_group("samples")
        for sample_index, (sample_id, section) in enumerate(samples.items(), start=1):
            sample_group = samples_group.create_group(str(sample_index))
            sample_group.attrs["sample_id"] = sample_id
            height, width = section.shape
            sample_group.attrs["height_px"] = height
            sample_group.attrs["width_px"] = width
            coords_arr = getattr(section, "coordinates", None)
            if coords_arr is not None and coords_arr.size > 0:
                sample_group.attrs["n_pixels"] = coords_arr.shape[0]
                sample_group.attrs["min_x"] = int(coords_arr[:, 0].min())
                sample_group.attrs["max_x"] = int(coords_arr[:, 0].max())
                sample_group.attrs["min_y"] = int(coords_arr[:, 1].min())
                sample_group.attrs["max_y"] = int(coords_arr[:, 1].max())
            else:
                sample_group.attrs["n_pixels"] = height * width

            pixel_size = getattr(section, "pixel_size_um", None)
            if pixel_size:
                sample_group.attrs["pixel_size_um_x"] = float(pixel_size[0])
                sample_group.attrs["pixel_size_um_y"] = float(pixel_size[1])


def _write_dataframe(group: h5py.Group, df: pd.DataFrame) -> None:
    """Store a pandas DataFrame as datasets within an HDF5 group."""
    group.attrs["columns"] = list(df.columns)
    for column in df.columns:
        series = df[column]
        if pdt.is_bool_dtype(series):
            data = series.fillna(False).to_numpy(dtype=np.bool_)
        elif pdt.is_integer_dtype(series):
            data = series.to_numpy(dtype=np.int64)
        elif pdt.is_float_dtype(series):
            data = series.to_numpy(dtype=np.float32)
        else:
            dtype = h5py.string_dtype(encoding="utf-8")
            data = series.astype(str).to_numpy()
            group.create_dataset(column, data=data, dtype=dtype)
            continue
        group.create_dataset(column, data=data)
