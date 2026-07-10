from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFileDialog,
    QMessageBox,
    QWidget,
)

from app.database import IonMode, LipidDB
from app.generated.MsiExportPickleDialog_ui import Ui_MsiExportPickleDialog
from app.msi_data import ImageType, SampleCollection


def filter_species_by_summed_option(
    species_ids: Sequence[str],
    *,
    include_summed: bool,
    is_summed_fn: Callable[[str], bool],
) -> list[str]:
    """Return species IDs after applying the pickle summed-neutral export option."""
    if include_summed:
        return list(species_ids)
    return [species_id for species_id in species_ids if not is_summed_fn(species_id)]


class PickleExportWindow(QDialog, Ui_MsiExportPickleDialog):
    """Dialog that manages Python pickle exports."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.samples: SampleCollection | None = None
        self.database: LipidDB | None = None
        self.species_ids: list[str] = []
        self.all_species_ids: list[str] = []
        self.setupUi(self)
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.radio_quant)
        self.button_group.addButton(self.radio_iso)
        self.button_group.addButton(self.radio_raw)
        self.connect_signals_slots()

    def connect_signals_slots(self) -> None:
        self.button_choose_file.clicked.connect(self.select_output_file)
        self.button_cancel.clicked.connect(self.close)
        self.button_export.clicked.connect(self.export)

    def set_context(
        self,
        *,
        samples: SampleCollection,
        database: LipidDB,
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

        self.line_edit_output.clear()
        self.radio_quant.setChecked(True)
        self.include_summed_checkbox.setChecked(True)
        self.selected_only_checkbox.setChecked(True)

        if not self.all_species_ids:
            QMessageBox.information(
                self.parentWidget() or self,
                "Export Python pickle",
                "No species are available for export.",
            )
            return False
        return True

    @Slot()
    def select_output_file(self) -> None:
        current_text = self.line_edit_output.text().strip()
        initial_dir = str(Path(current_text).parent) if current_text else ""
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Export Python pickle",
            initial_dir,
            "Python pickle (*.pkl);;All files (*)",
        )
        if not selected:
            return
        path = SampleCollection._ensure_pickle_suffix(Path(selected))
        self.line_edit_output.setText(str(path))
        self.activateWindow()
        self.raise_()

    def _current_image_type(self) -> ImageType:
        if self.radio_raw.isChecked():
            return ImageType.raw
        if self.radio_iso.isChecked():
            return ImageType.isotope
        return ImageType.quant

    @Slot()
    def export(self) -> None:
        if self.samples is None or self.database is None:
            QMessageBox.critical(
                self.parentWidget() or self,
                "Export Python pickle",
                "No samples are loaded for export.",
            )
            return

        output_text = self.line_edit_output.text().strip()
        if not output_text:
            QMessageBox.warning(
                self,
                "Export Python pickle",
                "Please choose an output file.",
            )
            return

        species_to_export = self._species_ids_for_export()
        if not species_to_export:
            QMessageBox.information(
                self,
                "Export Python pickle",
                "No species remain to export with the current settings. "
                "Select features in the table or disable the 'Only export selected' option.",
            )
            return

        output_path = SampleCollection._ensure_pickle_suffix(Path(output_text))
        self.line_edit_output.setText(str(output_path))
        try:
            written_path = self.samples.save_to_pickle(
                output_path,
                species_ids=species_to_export,
                image_type=self._current_image_type(),
            )
        except OSError as error:
            QMessageBox.critical(self, "Export Python pickle", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "Export Python pickle", str(error))
            return

        QMessageBox.information(
            self,
            "Export Python pickle",
            f"Export completed:\n{written_path}",
        )
        self.close()

    def _species_ids_for_export(self) -> list[str]:
        base_ids = self._base_species_ids()
        if self.database is None:
            return base_ids

        return filter_species_by_summed_option(
            base_ids,
            include_summed=self.include_summed_checkbox.isChecked(),
            is_summed_fn=self._is_summed_species,
        )

    def _base_species_ids(self) -> list[str]:
        if not self.selected_only_checkbox.isChecked() and self.all_species_ids:
            return list(self.all_species_ids)
        return list(self.species_ids)

    def _is_summed_species(self, species_id: str) -> bool:
        specie = None
        if self.database is not None:
            specie = self.database.species.get(species_id)
        if specie is not None:
            return specie.ion_mode == IonMode.summed and specie.adduct in {"(+)", "(-)"}
        return species_id.endswith(" (+)") or species_id.endswith(" (-)")
