from __future__ import annotations

from pathlib import Path
from typing import Sequence

import logging
import time
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QWidget,
)

from app.database import IonMode, LipidDB
from app.dataprocess import ImageType, SampleCollection
from app.generated.MsiExportScilsDialog_ui import Ui_MsiExportScilsDialog
from app.scils_export import (
    ScilsExportError,
    ScilsExportReport,
    ScilsExportUnavailableError,
    export_score_spot_images,
)

logger = logging.getLogger(__name__)


def _trace(message: str, *args) -> None:
    if args:
        message = message % args
    logger.info(message)
    _yield_thread()


class _ScilsExportWorkerSignals(QObject):
    finished = Signal()
    error = Signal(Exception)
    result = Signal(object)
    progress = Signal(int, int)


class _ScilsExportWorker(QRunnable):
    def __init__(self, *, fn, kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.kwargs = kwargs
        self.signals = _ScilsExportWorkerSignals()

    def _progress_callback(self, current: int, total: int) -> None:
        self.signals.progress.emit(current, total)

    @Slot()
    def run(self) -> None:
        _trace("[SCILS EXPORT] Worker thread started")
        try:
            result = self.fn(progress_callback=self._progress_callback, **self.kwargs)
        except Exception as exc:  # pragma: no cover - ensures UI feedback
            self.signals.error.emit(exc)
        else:
            self.signals.result.emit(result)
        finally:
            _trace("[SCILS EXPORT] Worker emitting finished signal")
            self.signals.finished.emit()


class ScilsExportWindow(QDialog, Ui_MsiExportScilsDialog):
    """Dialog that manages exporting processed ion images into SCiLS."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.samples: SampleCollection | None = None
        self.database: LipidDB | None = None
        self.species_ids: list[str] = []
        self.all_species_ids: list[str] = []
        self._last_sample_id: str | None = None
        self.threadpool = QThreadPool(self)
        self.setupUi(self)
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.radio_quant)
        self.button_group.addButton(self.radio_iso)
        self.button_group.addButton(self.radio_raw)
        self.scils_progressbar.setRange(0, 1)
        self.scils_progressbar.setValue(0)
        self.scils_progressbar.setVisible(False)
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

        self.radio_quant.setChecked(True)
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

    def _current_image_type(self) -> ImageType:
        if self.radio_raw.isChecked():
            return ImageType.raw
        if self.radio_iso.isChecked():
            return ImageType.isotope
        return ImageType.quant

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

        sample_id = self._select_sample_id()
        if sample_id is None:
            return

        dataset_path = self._select_dataset()
        if dataset_path is None:
            return

        self._set_busy_state(True, len(species_to_export))

        worker = _ScilsExportWorker(
            fn=export_score_spot_images,
            kwargs={
                "dataset_path": dataset_path,
                "samples": self.samples,
                "sample_id": sample_id,
                "species_ids": species_to_export,
                "image_type": self._current_image_type(),
                "database": self.database,
            },
        )
        worker.signals.progress.connect(self._update_progress)

        def handle_result(report: ScilsExportReport) -> None:
            _trace("[SCILS EXPORT] Worker result received")
            self._last_sample_id = sample_id
            self._show_summary(report)
            self._set_busy_state(False)
            self.close()

        def handle_error(exc: Exception) -> None:
            _trace("[SCILS EXPORT] Worker error received: %s", exc)
            message = str(exc)
            if isinstance(exc, (ScilsExportUnavailableError, ScilsExportError)):
                message = str(exc)
            QMessageBox.critical(self, "Export to SCiLS", message)
            self._set_busy_state(False)

        worker.signals.result.connect(handle_result)
        worker.signals.error.connect(handle_error)
        worker.signals.finished.connect(lambda: self._set_busy_state(False, keep_message=True))

        self.threadpool.start(worker)

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

    def _select_sample_id(self) -> str | None:
        if self.samples is None:
            return None
        sample_ids = list(self.samples.samples.keys())
        if not sample_ids:
            QMessageBox.warning(self, "Export to SCiLS", "No samples are available.")
            return None
        if len(sample_ids) == 1:
            return sample_ids[0]

        default_index = 0
        if self._last_sample_id and self._last_sample_id in sample_ids:
            default_index = sample_ids.index(self._last_sample_id)

        selection, ok = QInputDialog.getItem(
            self,
            "Select Sample",
            "Choose which loaded sample should be exported to SCiLS:",
            sample_ids,
            current=default_index,
            editable=False,
        )
        if not ok:
            return None
        return selection

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

    def _show_summary(self, report: ScilsExportReport) -> None:
        if report.exported_images == 0:
            QMessageBox.information(
                self,
                "Export to SCiLS",
                "None of the selected ion images contained values to export.",
            )
            return

        message = (
            f"Exported {report.exported_images} ion images to:\n{report.dataset_path}"
        )
        if report.skipped_species:
            message += (
                f"\nSkipped {len(report.skipped_species)} species "
                "that were not available in the current images."
            )

        QMessageBox.information(self, "Export to SCiLS", message)

    def _set_busy_state(self, busy: bool, total_steps: int | None = None, keep_message: bool = False) -> None:
        controls = [
            self.button_export,
            self.button_cancel,
            self.button_choose_file,
            self.radio_quant,
            self.radio_iso,
            self.radio_raw,
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
        self.scils_progressbar.setVisible(False)

    def _update_progress(self, current: int, total: int) -> None:
        if total <= 0:
            total = 1
        if self.scils_progressbar.maximum() != total:
            self.scils_progressbar.setRange(0, total)
        self.scils_progressbar.setValue(min(current, total))


def _yield_thread() -> None:
    time.sleep(0)
