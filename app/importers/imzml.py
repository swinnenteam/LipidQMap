import os
from typing import Sequence

from app.config import Config
from app.database import DatabaseFactory, IonMode, LipidDB
from app.importers.common import _combine_mode_databases
from app.msi_data import (
    SampleCollection,
    SampleFiles,
    SectionMsiImage,
    _combine_section_images,
    _unique_label,
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
    skipped_na_correction_classes: set[str] = set()

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
            skipped_na_correction_classes.update(
                image_collection.na_isotope_correction_skipped_classes
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
    combined_database = _combine_mode_databases(
        databases_by_mode,
        skipped_na_correction_classes=skipped_na_correction_classes,
    )
    return combined_database, SampleCollection(samples, species_order=combined_database.index)
