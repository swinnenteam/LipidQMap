from pathlib import Path
from types import SimpleNamespace
from typing import Any

import h5py
import numpy as np
import numpy.typing as npt

from app.config import Config
from app.database import DatabaseFactory, IonMode, LipidDB, LipidSpecies
from app.image_processing import ppm_to_tolerance
from app.importers.common import _combine_mode_databases
from app.msi_data import (
    AnnDataMatrixChoice,
    LoadedMsiData,
    SampleCollection,
    SectionMsiImage,
    _combine_section_images,
    _unique_label,
)


class _ProgressTracker:
    def __init__(self, callback) -> None:
        self.callback = callback
        self.value = 0

    def emit(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        if value >= self.value:
            self.value = value
            self.callback.emit(value)


class _ScaledProgressTracker:
    def __init__(
        self,
        parent: _ProgressTracker,
        source_min: int,
        source_max: int,
        target_min: int,
        target_max: int,
    ) -> None:
        self.parent = parent
        self.source_min = source_min
        self.source_max = source_max
        self.target_min = target_min
        self.target_max = target_max

    def emit(self, value: int) -> None:
        value = max(self.source_min, min(self.source_max, int(value)))
        span = self.source_max - self.source_min
        if span <= 0:
            self.parent.emit(self.target_max)
            return
        fraction = (value - self.source_min) / span
        scaled = self.target_min + round(fraction * (self.target_max - self.target_min))
        self.parent.emit(scaled)


def get_anndata_matrix_choices(anndata_path: str) -> list[AnnDataMatrixChoice]:
    """Return importable matrix choices for an AnnData file."""
    if _is_h5mu_path(anndata_path):
        return _get_h5mu_matrix_choices(anndata_path)
    adata = _read_anndata(anndata_path)
    try:
        choices = [AnnDataMatrixChoice.raw]
        if "x_batch_free" in adata.layers.keys():
            choices.append(AnnDataMatrixChoice.batch_corrected)
        return choices
    finally:
        _close_anndata(adata)


def load_database_anndata_collection(
    progress_file_callback,
    progress_overall_callback,
    database_path: str,
    anndata_path: str,
    matrix_choice: AnnDataMatrixChoice | str,
    config: Config,
) -> tuple[LipidDB, SampleCollection]:
    """Load a collection of sample images from one AnnData .h5ad or MuData .h5mu file."""
    progress_overall_callback.emit(0)
    progress_file_callback.emit(0)
    matrix_choice = AnnDataMatrixChoice(matrix_choice)
    if _is_h5mu_path(anndata_path):
        with h5py.File(anndata_path, "r") as h5mu:
            mod_group = _select_h5mu_modality(h5mu)
            matrix = _select_h5mu_matrix_node(mod_group, matrix_choice)
            adata = _read_h5mu_metadata(h5mu, mod_group, matrix)
            return _load_database_anndata_collection_from_source(
                progress_file_callback=progress_file_callback,
                progress_overall_callback=progress_overall_callback,
                database_path=database_path,
                anndata_path=anndata_path,
                matrix=matrix,
                adata=adata,
                config=config,
            )

    adata = _read_anndata(anndata_path)
    try:
        matrix = _select_anndata_matrix(adata, matrix_choice)
        return _load_database_anndata_collection_from_source(
            progress_file_callback=progress_file_callback,
            progress_overall_callback=progress_overall_callback,
            database_path=database_path,
            anndata_path=anndata_path,
            matrix=matrix,
            adata=adata,
            config=config,
        )
    finally:
        _close_anndata(adata)


def _load_database_anndata_collection_from_source(
    progress_file_callback,
    progress_overall_callback,
    database_path: str,
    anndata_path: str,
    matrix: Any,
    adata: Any,
    config: Config,
) -> tuple[LipidDB, SampleCollection]:
    _validate_anndata_matrix(matrix)
    mzs = _get_anndata_mzs(adata)
    mz_modes = _get_anndata_mz_modes(adata)
    spatial = _get_anndata_spatial(adata)
    foreground = _get_anndata_foreground(adata)
    sample_labels = _get_anndata_sample_labels(adata, anndata_path)

    databases_by_mode: dict[IonMode, LipidDB] = {}
    filtered_databases_by_mode: dict[IonMode, LipidDB] = {}
    matches_by_mode: dict[IonMode, dict[str, int]] = {}

    for mode in (IonMode.positive, IonMode.negative):
        if not np.any(mz_modes == mode):
            continue
        database = DatabaseFactory(database_path, mode).create_database()
        matches = _match_anndata_features_to_database(
            database=database,
            mzs=mzs,
            mz_modes=mz_modes,
            ion_mode=mode,
            ppm=config.settings.processing_settings.ppm,
        )
        if not matches:
            continue
        databases_by_mode[mode] = database
        filtered_databases_by_mode[mode] = _filter_database_for_matched_adducts(
            database=database,
            matched_adduct_ids=set(matches),
        )
        matches_by_mode[mode] = matches

    if not matches_by_mode:
        raise ValueError(
            "No AnnData m/z features matched the selected LipidQMap database within "
            f"{config.settings.processing_settings.ppm:g} ppm."
        )

    samples: dict[str, SectionMsiImage] = {}
    skipped_na_correction_classes: set[str] = set()
    unique_sample_labels = list(dict.fromkeys(sample_labels.tolist()))
    total_samples = len(unique_sample_labels)

    for sample_index, sample_label in enumerate(unique_sample_labels):
        file_progress = _ProgressTracker(progress_file_callback)
        file_progress.emit(0)
        sample_mask = sample_labels == sample_label
        sample_rows = np.flatnonzero(sample_mask)
        if sample_rows.size == 0:
            continue
        sample_coordinates, image_shape, pixel_size_um = _build_anndata_grid(
            spatial=spatial[sample_rows],
            sample_label=sample_label,
            spot_size=_spot_size_for_sample(adata.uns.get("spot_size"), sample_label),
        )
        sample_stage_coordinates = np.column_stack(
            (
                spatial[sample_rows, 0].astype(np.float64),
                spatial[sample_rows, 1].astype(np.float64),
                np.zeros(sample_rows.size, dtype=np.float64),
            )
        )
        sample_foreground = foreground[sample_rows]
        transparent_mask = _build_transparent_mask(
            coordinates=sample_coordinates,
            image_shape=image_shape,
            foreground=sample_foreground,
        )
        file_progress.emit(10)

        sample_images: list[tuple[IonMode, SectionMsiImage]] = []
        modes_to_process = list(matches_by_mode.items())
        for mode_index, (mode, matches) in enumerate(modes_to_process):
            mode_start = 10 + int(mode_index / len(modes_to_process) * 85)
            mode_end = 10 + int((mode_index + 1) / len(modes_to_process) * 85)
            mode_progress = _ScaledProgressTracker(
                parent=file_progress,
                source_min=0,
                source_max=100,
                target_min=mode_start,
                target_max=mode_end,
            )
            mode_progress.emit(0)
            database = filtered_databases_by_mode[mode]
            raw_images = _build_anndata_raw_images(
                matrix=matrix,
                sample_rows=sample_rows,
                coordinates=sample_coordinates,
                image_shape=image_shape,
                foreground=sample_foreground,
                matches=matches,
                species_ids=set(database.species),
            )
            if not raw_images:
                continue
            mode_progress.emit(30)
            average_spectrum = _build_anndata_average_spectrum(
                matrix=matrix,
                rows=sample_rows,
                mzs=mzs,
                mz_modes=mz_modes,
                ion_mode=mode,
                foreground=sample_foreground,
            )
            mode_progress.emit(40)
            loaded = LoadedMsiData(
                ion_mode=mode,
                raw=raw_images,
                average_spectrum=average_spectrum,
                num_spectra=sample_rows.size,
                coordinates=sample_coordinates,
                pixel_size_um=pixel_size_um,
                stage_coordinates=sample_stage_coordinates,
                transparent_mask=transparent_mask,
            )
            image_collection = SectionMsiImage.from_loaded_data(
                mode_progress,
                database=database,
                data=loaded,
                config=config,
            )
            skipped_na_correction_classes.update(
                image_collection.na_isotope_correction_skipped_classes
            )
            sample_images.append((mode, image_collection))

        if sample_images:
            samples[_unique_label(sample_label, set(samples))] = _combine_section_images(
                sample_images
            )
        file_progress.emit(100)
        progress_overall_callback.emit(int((sample_index + 1) / total_samples * 100))

    if not samples:
        raise ValueError("AnnData import did not produce any sample images.")

    progress_file_callback.emit(100)
    progress_overall_callback.emit(100)
    combined_database = _combine_mode_databases(
        filtered_databases_by_mode,
        skipped_na_correction_classes=skipped_na_correction_classes,
    )
    return combined_database, SampleCollection(samples, species_order=combined_database.index)


def _is_h5mu_path(anndata_path: str) -> bool:
    return Path(anndata_path).suffix.lower() == ".h5mu"


def _read_anndata(anndata_path: str) -> Any:
    try:
        import anndata as ad
    except ImportError as exc:
        raise ImportError(
            "AnnData import requires the 'anndata' package. Install project dependencies again."
        ) from exc
    return ad.read_h5ad(anndata_path)


def _get_h5mu_matrix_choices(anndata_path: str) -> list[AnnDataMatrixChoice]:
    with h5py.File(anndata_path, "r") as h5mu:
        mod_group = _select_h5mu_modality(h5mu)
        choices = [AnnDataMatrixChoice.raw]
        if "layers" in mod_group and "x_batch_free" in mod_group["layers"]:
            choices.append(AnnDataMatrixChoice.batch_corrected)
        return choices


def _read_h5mu_metadata(h5mu: h5py.File, mod_group: h5py.Group, matrix: Any) -> Any:
    from anndata.io import read_elem

    mod_name = mod_group.name.rsplit("/", 1)[-1]
    obs = read_elem(mod_group["obs"])
    var = read_elem(mod_group["var"])
    obsm = read_elem(mod_group["obsm"]) if "obsm" in mod_group else {}
    uns = read_elem(mod_group["uns"]) if "uns" in mod_group else {}
    n_obs, n_vars = matrix.shape

    if "spatial" not in obsm:
        spatial = _read_h5mu_root_obsm(h5mu, mod_name, "spatial", n_obs)
        if spatial is not None:
            obsm["spatial"] = spatial
    if "spot_size" not in uns and "uns" in h5mu and "spot_size" in h5mu["uns"]:
        uns["spot_size"] = read_elem(h5mu["uns"]["spot_size"])

    for column in ("sample_id", "foreground"):
        if column not in obs and "obs" in h5mu and column in h5mu["obs"]:
            values = _read_h5mu_root_obs_column(h5mu, mod_name, column, n_obs)
            if values is not None:
                obs[column] = values

    return SimpleNamespace(obs=obs, var=var, obsm=obsm, uns=uns, n_obs=n_obs, n_vars=n_vars)


def _select_h5mu_modality(h5mu: h5py.File) -> h5py.Group:
    if "mod" not in h5mu:
        raise ValueError("The selected .h5mu file does not contain a 'mod' modality group.")
    candidates = [
        mod_name
        for mod_name, mod_group in h5mu["mod"].items()
        if _is_importable_h5mu_modality(mod_group)
    ]
    if not candidates:
        raise ValueError(
            "No importable MSI modality was found in the selected .h5mu file. Expected a "
            "modality with var['mz'], var['mz_mode'], and an X matrix or layers['raw']."
        )
    for mod_name in candidates:
        if mod_name.lower() == "msi":
            return h5mu["mod"][mod_name]
    if len(candidates) == 1:
        return h5mu["mod"][candidates[0]]
    raise ValueError(
        "Multiple importable modalities were found in the selected .h5mu file: "
        f"{', '.join(candidates)}. Rename the MSI modality to 'MSI' or export a .h5ad file."
    )


def _is_importable_h5mu_modality(mod_group: h5py.Group) -> bool:
    if "var" not in mod_group or "mz" not in mod_group["var"] or "mz_mode" not in mod_group["var"]:
        return False
    if "X" in mod_group:
        return True
    return "layers" in mod_group and "raw" in mod_group["layers"]


def _select_h5mu_matrix_node(mod_group: h5py.Group, matrix_choice: AnnDataMatrixChoice) -> Any:
    from anndata.io import read_elem

    if matrix_choice == AnnDataMatrixChoice.batch_corrected:
        if "layers" not in mod_group or "x_batch_free" not in mod_group["layers"]:
            raise ValueError(
                "The selected MuData modality does not contain layers['x_batch_free']."
            )
        node = mod_group["layers"]["x_batch_free"]
    elif "layers" in mod_group and "raw" in mod_group["layers"]:
        node = mod_group["layers"]["raw"]
    elif "X" in mod_group:
        node = mod_group["X"]
    else:
        raise ValueError("The selected MuData modality does not contain an X matrix.")

    if isinstance(node, h5py.Dataset):
        return node
    return read_elem(node)


def _read_h5mu_root_obsm(
    h5mu: h5py.File, mod_name: str, key: str, mod_n_obs: int
) -> npt.NDArray | None:
    if "obsm" not in h5mu or key not in h5mu["obsm"]:
        return None
    from anndata.io import read_elem

    values = np.asarray(read_elem(h5mu["obsm"][key]))
    return _align_h5mu_root_obs_values(h5mu, mod_name, values, mod_n_obs)


def _read_h5mu_root_obs_column(
    h5mu: h5py.File, mod_name: str, column: str, mod_n_obs: int
) -> npt.NDArray | None:
    if "obs" not in h5mu or column not in h5mu["obs"]:
        return None
    from anndata.io import read_elem

    values = np.asarray(read_elem(h5mu["obs"][column]))
    return _align_h5mu_root_obs_values(h5mu, mod_name, values, mod_n_obs)


def _align_h5mu_root_obs_values(
    h5mu: h5py.File, mod_name: str, values: npt.NDArray, mod_n_obs: int
) -> npt.NDArray:
    if "obsmap" not in h5mu or mod_name not in h5mu["obsmap"]:
        if values.shape[0] != mod_n_obs:
            raise ValueError(f"Root MuData metadata cannot be aligned to modality '{mod_name}'.")
        return values

    from anndata.io import read_elem

    obsmap = np.asarray(read_elem(h5mu["obsmap"][mod_name])).reshape(-1).astype(np.int64)
    if values.shape[0] != obsmap.shape[0]:
        raise ValueError(f"Root MuData metadata cannot be aligned to modality '{mod_name}'.")

    obsmap_max = obsmap.max(initial=-1)
    if obsmap_max == mod_n_obs:
        valid = obsmap > 0
        mod_indices = obsmap[valid].astype(np.int64) - 1
    else:
        valid = obsmap >= 0
        mod_indices = obsmap[valid].astype(np.int64)

    if (
        mod_indices.size != mod_n_obs
        or np.unique(mod_indices).size != mod_n_obs
        or mod_indices.min(initial=0) < 0
        or mod_indices.max(initial=-1) >= mod_n_obs
    ):
        raise ValueError(f"Root MuData metadata cannot be aligned to modality '{mod_name}'.")
    return values[valid][np.argsort(mod_indices)]


def _close_anndata(adata: Any) -> None:
    file_obj = getattr(adata, "file", None)
    if file_obj is not None:
        try:
            file_obj.close()
        except Exception:
            return


def _select_anndata_matrix(adata: Any, matrix_choice: AnnDataMatrixChoice) -> Any:
    if matrix_choice == AnnDataMatrixChoice.batch_corrected:
        if "x_batch_free" not in adata.layers.keys():
            raise ValueError("The selected AnnData file does not contain layers['x_batch_free'].")
        return adata.layers["x_batch_free"]
    if "raw" in adata.layers.keys():
        return adata.layers["raw"]
    return adata.X


def _validate_anndata_matrix(matrix: Any) -> None:
    if len(matrix.shape) != 2:
        raise ValueError("The selected AnnData matrix must be two-dimensional.")


def _matrix_vector(
    matrix: Any, rows: npt.NDArray[np.int64], column: int
) -> npt.NDArray[np.float32]:
    values = matrix[rows, column]
    if hasattr(values, "toarray"):
        values = values.toarray()
    return np.asarray(values, dtype=np.float32).reshape(-1)


def _matrix_rows_columns(
    matrix: Any, rows: npt.NDArray[np.int64], columns: npt.NDArray[np.int64]
) -> npt.NDArray[np.float32]:
    if isinstance(matrix, h5py.Dataset):
        row_block = matrix[rows, :]
        return np.asarray(row_block[:, columns], dtype=np.float32)
    values = matrix[np.ix_(rows, columns)]
    if hasattr(values, "toarray"):
        values = values.toarray()
    return np.asarray(values, dtype=np.float32)


def _get_anndata_mzs(adata: Any) -> npt.NDArray[np.float64]:
    if "mz" not in adata.var:
        raise ValueError("AnnData var['mz'] is required for LipidQMap import.")
    mzs = np.asarray(adata.var["mz"], dtype=np.float64)
    if mzs.ndim != 1 or mzs.size != adata.n_vars:
        raise ValueError("AnnData var['mz'] must contain one numeric m/z value per feature.")
    return mzs


def _get_anndata_mz_modes(adata: Any) -> npt.NDArray:
    if "mz_mode" not in adata.var:
        raise ValueError("AnnData var['mz_mode'] is required for LipidQMap import.")
    modes = np.asarray([_normalize_anndata_ion_mode(value) for value in adata.var["mz_mode"]])
    if any(mode is None for mode in modes):
        raise ValueError("AnnData var['mz_mode'] must contain positive/negative mode values.")
    return modes


def _normalize_anndata_ion_mode(value: Any) -> IonMode | None:
    text = str(value).strip().lower()
    if text in {"+", "pos", "positive", "positive mode", "positive ion mode"}:
        return IonMode.positive
    if text in {"-", "neg", "negative", "negative mode", "negative ion mode"}:
        return IonMode.negative
    return None


def _get_anndata_spatial(adata: Any) -> npt.NDArray[np.float64]:
    if "spatial" not in adata.obsm:
        raise ValueError("AnnData obsm['spatial'] is required for LipidQMap import.")
    spatial = np.asarray(adata.obsm["spatial"], dtype=np.float64)
    if spatial.ndim != 2 or spatial.shape[0] != adata.n_obs or spatial.shape[1] < 2:
        raise ValueError("AnnData obsm['spatial'] must have shape (n_obs, 2).")
    return spatial[:, :2]


def _get_anndata_foreground(adata: Any) -> npt.NDArray[np.bool_]:
    if "foreground" not in adata.obs:
        return np.ones(adata.n_obs, dtype=np.bool_)
    values = adata.obs["foreground"]
    if hasattr(values, "to_numpy"):
        values = values.to_numpy()
    return np.asarray([_normalize_bool(value) for value in values], dtype=np.bool_)


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y", "foreground"}


def _get_anndata_sample_labels(adata: Any, anndata_path: str) -> npt.NDArray:
    if "sample_id" not in adata.obs:
        return np.full(adata.n_obs, Path(anndata_path).stem, dtype=object)
    values = adata.obs["sample_id"]
    if hasattr(values, "to_numpy"):
        values = values.to_numpy()
    return np.asarray([str(value) for value in values], dtype=object)


def _spot_size_for_sample(value: Any, sample_label: str) -> tuple[float, float] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        if sample_label in value:
            return _coerce_spot_size(value[sample_label])
        text_label = str(sample_label)
        if text_label in value:
            return _coerce_spot_size(value[text_label])
        return None
    return _coerce_spot_size(value)


def _coerce_spot_size(value: Any) -> tuple[float, float] | None:
    array = np.asarray(value, dtype=np.float64).reshape(-1)
    if array.size == 0:
        return None
    if array.size == 1:
        array = np.repeat(array, 2)
    size_x, size_y = float(array[0]), float(array[1])
    if size_x <= 0 or size_y <= 0:
        return None
    return size_x, size_y


def _build_anndata_grid(
    spatial: npt.NDArray[np.float64],
    sample_label: str,
    spot_size: tuple[float, float] | None,
) -> tuple[npt.NDArray[np.int32], tuple[int, int], tuple[float, float] | None]:
    coords = np.empty((spatial.shape[0], 3), dtype=np.int32)
    seen: set[tuple[int, int]] = set()

    if spot_size is not None:
        size_x, size_y = spot_size
        x_indices = np.rint((spatial[:, 0] - np.min(spatial[:, 0])) / size_x).astype(np.int32) + 1
        y_indices = np.rint((spatial[:, 1] - np.min(spatial[:, 1])) / size_y).astype(np.int32) + 1
        image_shape = (int(np.max(y_indices)), int(np.max(x_indices)))
        iterator = zip(x_indices, y_indices)
    else:
        x_values = spatial[:, 0]
        y_values = spatial[:, 1]
        unique_x = np.unique(x_values)
        unique_y = np.unique(y_values)
        x_lookup = {value: idx + 1 for idx, value in enumerate(sorted(unique_x))}
        y_lookup = {value: idx + 1 for idx, value in enumerate(sorted(unique_y))}
        image_shape = (len(unique_y), len(unique_x))
        iterator = ((x_lookup[x_value], y_lookup[y_value]) for x_value, y_value in spatial)

    for row, (x, y) in enumerate(iterator):
        key = (x, y)
        if key in seen:
            raise ValueError(
                f"AnnData sample '{sample_label}' contains duplicate spatial coordinates."
            )
        seen.add(key)
        coords[row] = (x, y, 1)
    return coords, image_shape, spot_size


def _match_anndata_features_to_database(
    database: LipidDB,
    mzs: npt.NDArray[np.float64],
    mz_modes: npt.NDArray,
    ion_mode: IonMode,
    ppm: float,
) -> dict[str, int]:
    matches: dict[str, int] = {}
    mode_indices = np.flatnonzero(mz_modes == ion_mode)
    mode_mzs = mzs[mode_indices]
    for species_id, target_mz in zip(*database.get_all_species()):
        tolerance = ppm_to_tolerance(ppm=ppm, mz=target_mz)
        deltas = np.abs(mode_mzs - target_mz)
        candidates = np.flatnonzero(deltas <= tolerance)
        if candidates.size == 0:
            continue
        best_local_index = candidates[np.argmin(deltas[candidates])]
        matches[species_id] = int(mode_indices[best_local_index])
    return matches


def _filter_database_for_matched_adducts(
    database: LipidDB, matched_adduct_ids: set[str]
) -> LipidDB:
    matched_base_ids = {
        database.species[species_id].id
        for species_id in matched_adduct_ids
        if species_id in database.species
    }
    filtered_species: dict[str, LipidSpecies] = {}
    for species_id, specie in database.species.items():
        if species_id in matched_adduct_ids or (
            specie.ion_mode == IonMode.summed and specie.id in matched_base_ids
        ):
            filtered_species[species_id] = specie
    filtered_database = LipidDB(filtered_species)
    filtered_database.index = filtered_database.species_ids_neutral_first()
    return filtered_database


def _build_anndata_raw_images(
    matrix: Any,
    sample_rows: npt.NDArray[np.int64],
    coordinates: npt.NDArray[np.int32],
    image_shape: tuple[int, int],
    foreground: npt.NDArray[np.bool_],
    matches: dict[str, int],
    species_ids: set[str],
) -> dict[str, npt.NDArray]:
    raw_images: dict[str, npt.NDArray] = {}
    for species_id, feature_index in matches.items():
        if species_id not in species_ids:
            continue
        image = np.full(image_shape, np.nan, dtype=np.float32)
        values = _matrix_vector(matrix, sample_rows, feature_index)
        for row, (x, y, _) in enumerate(coordinates):
            if foreground[row]:
                image[y - 1, x - 1] = values[row]
        raw_images[species_id] = image
    return raw_images


def _build_transparent_mask(
    coordinates: npt.NDArray[np.int32],
    image_shape: tuple[int, int],
    foreground: npt.NDArray[np.bool_],
) -> npt.NDArray[np.bool_]:
    mask = np.zeros(image_shape, dtype=np.bool_)
    for row, (x, y, _) in enumerate(coordinates):
        if not foreground[row]:
            mask[y - 1, x - 1] = True
    return mask


def _build_anndata_average_spectrum(
    matrix: Any,
    rows: npt.NDArray[np.int64],
    mzs: npt.NDArray[np.float64],
    mz_modes: npt.NDArray,
    ion_mode: IonMode,
    foreground: npt.NDArray[np.bool_],
) -> npt.NDArray[np.float64]:
    feature_indices = np.flatnonzero(mz_modes == ion_mode)
    average_rows = rows[foreground]
    if average_rows.size == 0:
        average_rows = rows
    intensities = _matrix_rows_columns(matrix, average_rows, feature_indices)
    means = np.nanmean(intensities, axis=0).astype(np.float64)
    means[np.isnan(means)] = 0.0
    spectrum_mzs = mzs[feature_indices]
    order = np.argsort(spectrum_mzs)
    return np.vstack((spectrum_mzs[order], means[order]))
