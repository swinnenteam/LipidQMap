from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QWidget

from app.database import IonMode, LipidDB
from app.dataprocess import ImageType, SampleCollection
from app.generated.MsiExportScilsDialog_ui import Ui_MsiExportScilsDialog
from app.scils_export import (
    ScilsExportError,
    ScilsExportReport,
    ScilsExportUnavailableError,
    _image_type_label,
    export_score_spot_images,
    write_aggregated_features,
)


class ScilsExportWindow(QDialog, Ui_MsiExportScilsDialog):
    """Dialog that manages exporting processed ion images into SCiLS."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.samples: SampleCollection | None = None
        self.database: LipidDB | None = None
        self.species_ids: list[str] = []
        self.all_species_ids: list[str] = []
        self.setupUi(self)
        self.scils_progressbar.setRange(0, 1)
        self.scils_progressbar.setValue(0)
        self.scils_progressbar.setVisible(True)
        self.connect_signals_slots()

    def connect_signals_slots(self) -> None:
        self.button_choose_file.clicked.connect(self.select_output_file)
        self.button_cancel.clicked.connect(self.close)
        self.button_export.clicked.connect(self.export)

    def set_context(
        self,
        *,
        samples: SampleCollection,
        database: LipidDB | None,
        species_ids: Sequence[str],
        all_species_ids: Sequence[str] | None = None,
    ) -> bool:
        """Populate the dialog with the data required for exporting."""
        self.samples = samples
        self.database = database
        self.species_ids = list(species_ids)
        self.all_species_ids = (
            list(all_species_ids) if all_species_ids is not None else list(self.species_ids)
        )

        self.quant_checkbox.setChecked(True)
        self.iso_checkbox.setChecked(False)
        self.raw_checkbox.setChecked(False)
        self.include_summed_checkbox.setChecked(True)
        self.selected_only_checkbox.setChecked(True)
        self.lineEdit.clear()

        if not self.all_species_ids:
            QMessageBox.information(
                self.parentWidget() or self,
                "Export to SCiLS",
                "No species are available for export.",
            )
            return False
        return True

    def _selected_image_types(self) -> list[ImageType]:
        types: list[ImageType] = []
        if self.quant_checkbox.isChecked():
            types.append(ImageType.quant)
        if self.iso_checkbox.isChecked():
            types.append(ImageType.isotope)
        if self.raw_checkbox.isChecked():
            types.append(ImageType.raw)
        return types

    @Slot()
    def select_output_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select SCiLS dataset",
            "",
            "SCiLS Lab dataset (*.slx);;All files (*)",
        )
        if filename:
            self.lineEdit.setText(filename)

    @Slot()
    def export(self) -> None:
        if self.samples is None:
            QMessageBox.critical(
                self,
                "Export to SCiLS",
                "No samples are loaded for export.",
            )
            return

        species_to_export = self._species_ids_for_export()
        if not species_to_export:
            QMessageBox.information(
                self,
                "Export to SCiLS",
                "No species remain to export with the current settings. "
                "Select features in the table or disable the 'Only export selected' option.",
                )
            return

        dataset_path = self._select_dataset()
        if dataset_path is None:
            return

        selected_types = self._selected_image_types()
        if not selected_types:
            QMessageBox.information(
                self,
                "Export to SCiLS",
                "Please select at least one image type to export.",
            )
            return

        sample_ids = list(self.samples.samples.keys())
        if not sample_ids:
            QMessageBox.warning(self, "Export to SCiLS", "No samples are available.")
            return

        per_sample_steps = len(species_to_export)
        total_steps = (
            per_sample_steps * len(sample_ids) * len(selected_types) + len(selected_types)
            if per_sample_steps and selected_types
            else len(selected_types)
        )
        self._set_busy_state(True, total_steps)

        reports: list[tuple[ImageType, ScilsExportReport]] = []
        progress_completed = 0
        had_error = False

        for image_type in selected_types:
            aggregate: dict[str, list[tuple[list[int], list[float]]]] = {}
            skipped_species: list[str] = []

            for sample_id in sample_ids:
                def progress_callback(current: int, total: int, *, _offset: int = progress_completed) -> None:
                    absolute = _offset + max(0, min(current, per_sample_steps))
                    self._update_progress(absolute, total_steps)
                    QApplication.processEvents()

                try:
                    report = export_score_spot_images(
                        dataset_path=dataset_path,
                        samples=self.samples,
                        sample_id=sample_id,
                        species_ids=species_to_export,
                        image_type=image_type,
                        database=self.database,
                        progress_callback=progress_callback,
                        feature_aggregate=aggregate,
                    )
                except ScilsExportUnavailableError as error:
                    QMessageBox.critical(self, "Export to SCiLS", str(error))
                    had_error = True
                    break
                except ScilsExportError as error:
                    QMessageBox.critical(self, "Export to SCiLS", str(error))
                    had_error = True
                    break
                else:
                    skipped_species.extend(report.skipped_species)
                    progress_completed += per_sample_steps
                    self._update_progress(progress_completed, total_steps)

            if had_error:
                break

            report = write_aggregated_features(
                dataset_path=dataset_path,
                feature_list_label=self._feature_list_label(sample_ids, image_type),
                image_type=image_type,
                aggregate=aggregate,
                skipped_species=skipped_species,
            )
            reports.append((image_type, report))
            progress_completed += 1
            self._update_progress(progress_completed, total_steps)
        else:
            if reports:
                self._show_summary(reports, dataset_path)
                self.close()

        self._set_busy_state(False)

    def _species_ids_for_export(self) -> list[str]:
        base_ids = self._base_species_ids()
        if self.database is None or self.include_summed_checkbox.isChecked():
            return base_ids

        filtered = [species_id for species_id in base_ids if not self._is_summed_species(species_id)]
        return filtered

    def _base_species_ids(self) -> list[str]:
        if not self.selected_only_checkbox.isChecked() and self.all_species_ids:
            return list(self.all_species_ids)
        return list(self.species_ids)

    def _is_summed_species(self, species_id: str) -> bool:
        specie = None
        if self.database is not None:
            specie = self.database.species.get(species_id)
        if specie is not None:
            return specie.ion_mode == IonMode.summed and specie.adduct in {"(+)", "(-)", ""}
        return species_id.endswith(" (+)") or species_id.endswith(" (-)")

    def _select_dataset(self) -> Path | None:
        text = self.lineEdit.text().strip()
        if not text:
            QMessageBox.warning(self, "Export to SCiLS", "Please select a SCiLS .slx file.")
            return None
        path = Path(text)
        if not path.exists():
            QMessageBox.warning(
                self,
                "Export to SCiLS",
                f"The selected file does not exist:\n{path}",
            )
            return None
        if path.suffix.lower() != ".slx":
            QMessageBox.warning(
                self,
                "Export to SCiLS",
                "Please select a SCiLS Lab dataset (*.slx).",
            )
            return None
        return path

    def _show_summary(
        self,
        reports: list[tuple[ImageType, ScilsExportReport]],
        dataset_path: Path,
    ) -> None:
        total_exported = sum(report.exported_features for _, report in reports)
        total_skipped = sum(len(report.skipped_species) for _, report in reports)

        if total_exported == 0:
            QMessageBox.information(
                self,
                "Export to SCiLS",
                "None of the selected features contained values to export.",
            )
            return

        message = [f"Exported {total_exported} external features to:\n{dataset_path}"]
        for image_type, report in reports:
            label = _image_type_label(image_type)
            message.append(
                f"{label}: {report.exported_features} features "
                f"(skipped {len(report.skipped_species)})"
            )
        if total_skipped:
            message.append(f"Skipped {total_skipped} species without computed images.")

        QMessageBox.information(self, "Export to SCiLS", "\n".join(message))

    def _feature_list_label(self, sample_ids: list[str], image_type: ImageType) -> str:
        if not sample_ids:
            base = "LipidQMap"
        elif len(sample_ids) == 1:
            base = f"LipidQMap - {sample_ids[0]}"
        else:
            base = f"LipidQMap - {sample_ids[0]} +{len(sample_ids) - 1}"
        return f"{base} ({_image_type_label(image_type)})"

    def _set_busy_state(self, busy: bool, total_steps: int | None = None, keep_message: bool = False) -> None:
        controls = [
            self.button_export,
            self.button_cancel,
            self.button_choose_file,
            self.quant_checkbox,
            self.iso_checkbox,
            self.raw_checkbox,
            self.include_summed_checkbox,
            self.selected_only_checkbox,
            self.lineEdit,
        ]
        for widget in controls:
            widget.setEnabled(not busy)

        if busy:
            if total_steps is None or total_steps <= 0:
                total_steps = 1
            self.scils_progressbar.setRange(0, total_steps)
            self.scils_progressbar.setValue(0)
            self.scils_progressbar.setVisible(True)
        elif not keep_message:
            self._reset_progress()

    def _reset_progress(self) -> None:
        self.scils_progressbar.setRange(0, 1)
        self.scils_progressbar.setValue(0)
        self.scils_progressbar.setVisible(True)

    def _update_progress(self, current: int, total: int) -> None:
        if total <= 0:
            total = 1
        if self.scils_progressbar.maximum() != total:
            self.scils_progressbar.setRange(0, total)
        self.scils_progressbar.setValue(min(current, total))
