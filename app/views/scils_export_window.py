from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6.QtCore import Slot
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


class ScilsExportWindow(QDialog, Ui_MsiExportScilsDialog):
    """Dialog that manages exporting processed ion images into SCiLS."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.samples: SampleCollection | None = None
        self.database: LipidDB | None = None
        self.species_ids: list[str] = []
        self.all_species_ids: list[str] = []
        self._last_sample_id: str | None = None
        self.setupUi(self)
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.radio_quant)
        self.button_group.addButton(self.radio_iso)
        self.button_group.addButton(self.radio_raw)
        self.connect_signals_slots()

    def connect_signals_slots(self) -> None:
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

        try:
            report = export_score_spot_images(
                dataset_path=dataset_path,
                samples=self.samples,
                sample_id=sample_id,
                species_ids=species_to_export,
                image_type=self._current_image_type(),
                database=self.database,
            )
        except ScilsExportUnavailableError as error:
            QMessageBox.critical(self, "Export to SCiLS", str(error))
            return
        except ScilsExportError as error:
            QMessageBox.critical(self, "Export to SCiLS", str(error))
            return

        self._last_sample_id = sample_id
        self._show_summary(report)
        self.close()

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
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select SCiLS dataset",
            "",
            "SCiLS Lab dataset (*.slx);;All files (*)",
        )
        if not filename:
            return None
        return Path(filename)

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
