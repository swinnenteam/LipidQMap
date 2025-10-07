from __future__ import annotations

from pathlib import Path
from typing import Sequence

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QButtonGroup, QDialog, QFileDialog, QMessageBox, QWidget

from app.database import LipidDB
from app.dataprocess import ImageType, SampleCollection
from app.export import CardinalExportError, export_cardinal_hdf5
from app.generated.MsiExportHdf5Dialog_ui import Ui_MsiExportHdf5Dialog


class Hdf5ExportWindow(QDialog, Ui_MsiExportHdf5Dialog):
    """Dialog that manages Cardinal HDF5 exports."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.samples: SampleCollection | None = None
        self.database: LipidDB | None = None
        self.species_ids: list[str] = []
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
    ) -> bool:
        """Populate the dialog with the data required for exporting."""
        self.samples = samples
        self.database = database
        self.species_ids = list(species_ids)

        self.line_edit_output.clear()
        self.radio_quant.setChecked(True)

        if not self.species_ids:
            QMessageBox.information(
                self.parentWidget() or self,
                "Export Cardinal HDF5",
                "No species are marked for export.",
            )
            return False
        return True

    @Slot()
    def select_output_file(self) -> None:
        current_text = self.line_edit_output.text().strip()
        initial_dir = str(Path(current_text).parent) if current_text else ""
        selected, _ = QFileDialog.getSaveFileName(
            self,
            "Export Cardinal HDF5",
            initial_dir,
            "Cardinal HDF5 (*.h5 *.hdf5)",
        )
        if not selected:
            return
        path = Path(selected)
        path = self._ensure_hdf5_suffix(path)
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
                "Export Cardinal HDF5",
                "No samples are loaded for export.",
            )
            return

        if not self.species_ids:
            QMessageBox.information(
                self.parentWidget() or self,
                "Export Cardinal HDF5",
                "No species are marked for export.",
            )
            return

        output_text = self.line_edit_output.text().strip()
        if not output_text:
            QMessageBox.warning(
                self,
                "Export Cardinal HDF5",
                "Please choose an output file.",
            )
            return

        output_path = Path(output_text)
        output_path = self._ensure_hdf5_suffix(output_path)
        self.line_edit_output.setText(str(output_path))

        try:
            written_path = export_cardinal_hdf5(
                filepath=output_path,
                samples=self.samples,
                database=self.database,
                species_ids=self.species_ids,
                image_type=self._current_image_type(),
            )
        except CardinalExportError as error:
            QMessageBox.critical(self, "Export Cardinal HDF5", str(error))
            return
        except OSError as error:
            QMessageBox.critical(self, "Export Cardinal HDF5", str(error))
            return

        QMessageBox.information(
            self,
            "Export Cardinal HDF5",
            f"Export completed:\n{written_path}",
        )
        self.close()

    @staticmethod
    def _ensure_hdf5_suffix(path: Path) -> Path:
        if path.suffix.lower() not in {".h5", ".hdf5"}:
            return path.with_suffix(".h5")
        return path
