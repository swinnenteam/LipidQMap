import os

from PySide6.QtCore import QThreadPool, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from app.config import Config, config_paths
from app.database import IonMode, LipidDB
from app.dataprocess import (
    SampleCollection,
    detect_imzml_ion_mode,
    load_database_image_collection,
)
from app.generated.MsiImportDialog_ui import Ui_Dialog
from app.multithreading import Worker


def fetch_db_list() -> list[str]:
    dbs = os.listdir(config_paths["DATABASE_DIR"])
    dbs = list(filter(lambda f: f.endswith(".xlsx"), dbs))
    return [os.path.splitext(s)[0] for s in dbs]


class ImzmlImportWindow(QWidget, Ui_Dialog):
    """
    Window in which imzML import setting are configured.
    """

    finished_imzml_loading = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.threadpool = QThreadPool()
        self.filepath: list[str] | None = None
        self.file_ion_modes: dict[str, IonMode] = {}
        self.database: LipidDB | None = None
        self.samples: SampleCollection
        self.setupUi(self)
        self.database_combo_box.addItems(fetch_db_list())

        self.ppm_spinbox.setValue(self.config.settings.processing_settings.ppm)
        self.bin_size_spinbox.setValue(self.config.settings.processing_settings.bin_size)
        self.m2_iso_cor_checkbox.setChecked(
            self.config.settings.processing_settings.db_isotope_correction
        )
        self.na_iso_cor_checkbox.setChecked(
            self.config.settings.processing_settings.na_isotope_correction
        )
        self.cal_checkbox.setChecked(self.config.settings.processing_settings.online_calibration)
        self.cal_ppm_spinbox.setValue(self.config.settings.processing_settings.calibration_ppm)
        self.cal_int_spinbox.setValue(
            self.config.settings.processing_settings.calibration_min_intensity
        )
        self.calibrant_pos_spinbox.setValue(self.config.settings.processing_settings.pos_calibrant)
        self.calibrant_neg_spinbox.setValue(self.config.settings.processing_settings.neg_calibrant)
        self.imputation_checkbox.setChecked(self.config.settings.processing_settings.imputation)
        # set last used database
        index = self.database_combo_box.findText(
            self.config.settings.database_settings.last_used_database
        )
        if index >= 0:
            self.database_combo_box.setCurrentIndex(index)
        self.connect_signals_slots()
        self.toggle_cal_checked_value(self.cal_checkbox.isChecked())

    def connect_signals_slots(self) -> None:
        """
        Connect signals from UI widgets to their corresponding slots.
        """
        self.import_data_button.clicked.connect(self.process_imzml_files)
        self.open_imzml_button.clicked.connect(self.open_imzml_files)

        # UI state and interactivity
        self.cal_checkbox.toggled.connect(self.toggle_cal_checked_value)

        # Connect settings changes to their specific handler slots
        self.database_combo_box.currentTextChanged.connect(self._on_database_changed)
        self.ppm_spinbox.valueChanged.connect(self._on_ppm_changed)
        self.bin_size_spinbox.valueChanged.connect(self._on_bin_size_changed)
        self.calibrant_pos_spinbox.valueChanged.connect(self._on_calibrant_pos_changed)
        self.calibrant_neg_spinbox.valueChanged.connect(self._on_calibrant_neg_changed)
        self.cal_ppm_spinbox.valueChanged.connect(self._on_cal_ppm_changed)
        self.cal_int_spinbox.valueChanged.connect(self._on_cal_int_changed)
        self.na_iso_cor_checkbox.toggled.connect(self._on_na_iso_cor_changed)
        self.m2_iso_cor_checkbox.toggled.connect(self._on_m2_iso_cor_changed)
        self.cal_checkbox.toggled.connect(self._on_online_cal_changed)
        self.imputation_checkbox.toggled.connect(self._on_imputation_changed)

    def process_imzml_files(self) -> None:
        if not self.filepath:
            raise ValueError("Please open an imzML file first.")

        self.set_ui_components_status(False)

        db_name = self.database_combo_box.currentText()
        db_path = os.path.join(config_paths["DATABASE_DIR"], db_name + ".xlsx")
        if not db_name:
            self.set_ui_components_status(True)
            raise ValueError(
                "Please select a database file, the readme provides details on how to create a database."
            )
        if self.filepath:
            worker = Worker(
                load_database_image_collection,
                database_path=db_path,
                imzml_paths=self.filepath,
                config=self.config,
            )
            worker.signals.progress_file.connect(self.handle_progress_file)
            worker.signals.progress_overall.connect(self.handle_progress_overall)
            worker.signals.result.connect(self.handle_finished)
            self.threadpool.start(worker)

    @Slot()
    def handle_progress_file(self, file_progress: int) -> None:
        """Update progressbar"""
        self.progress_bar_file.setValue(file_progress)

    @Slot()
    def handle_progress_overall(self, overall_progress: int) -> None:
        """Update progressbar"""
        self.progress_bar_overall.setValue(overall_progress)

    @Slot(LipidDB, SampleCollection)
    def handle_finished(self, database: LipidDB, samples: SampleCollection) -> None:
        """Emit results to main window"""
        self.samples = samples
        self.database = database
        self.finished_imzml_loading.emit()
        self.close()

    def open_imzml_files(self) -> None:
        """Open imzML files."""
        self.imzml_list_view.clear()
        self.file_ion_modes = {}
        self.filepath, __ = QFileDialog.getOpenFileNames(
            self, "Select imzML file(s)", filter=";imzML(*.imzML)"
        )
        if not self.filepath:
            return
        items: list[str] = []
        for path in self.filepath:
            try:
                ion_mode = detect_imzml_ion_mode(path)
            except ValueError as exc:
                QMessageBox.warning(self, "Ion mode detection failed", str(exc))
                self.filepath = None
                self.file_ion_modes = {}
                self.imzml_list_view.clear()
                return
            self.file_ion_modes[path] = ion_mode
            label = "POS" if ion_mode == IonMode.positive else "NEG"
            items.append(f"{os.path.basename(path)} ({label})")
        self.imzml_list_view.addItems(items)

    def toggle_cal_checked_value(self, is_checked: bool):
        """Enables or disables calibration-related widgets."""
        self.calibrant_pos_spinbox.setEnabled(is_checked)
        self.calibrant_neg_spinbox.setEnabled(is_checked)
        self.cal_ppm_spinbox.setEnabled(is_checked)
        self.cal_int_spinbox.setEnabled(is_checked)

    @Slot(str)
    def _on_database_changed(self, db_name: str):
        """Saves the last used database name."""
        self.config.settings.database_settings.last_used_database = db_name
        self.config.save()

    @Slot(float)
    def _on_ppm_changed(self, value: float):
        """Saves the PPM tolerance."""
        self.config.settings.processing_settings.ppm = value
        self.config.save()

    @Slot(float)
    def _on_bin_size_changed(self, value: float):
        """Saves the bin size."""
        self.config.settings.processing_settings.bin_size = value
        self.config.save()

    @Slot(float)
    def _on_calibrant_pos_changed(self, value: float):
        """Persist the positive-ion calibrant m/z."""
        self.config.settings.processing_settings.pos_calibrant = value
        self.config.save()

    @Slot(float)
    def _on_calibrant_neg_changed(self, value: float):
        """Persist the negative-ion calibrant m/z."""
        self.config.settings.processing_settings.neg_calibrant = value
        self.config.save()

    @Slot(float)
    def _on_cal_ppm_changed(self, value: float):
        """Saves the calibration PPM."""
        self.config.settings.processing_settings.calibration_ppm = value
        self.config.save()

    @Slot(int)
    def _on_cal_int_changed(self, value: int):
        """Saves the calibration minimum intensity."""
        self.config.settings.processing_settings.calibration_min_intensity = value
        self.config.save()

    @Slot(bool)
    def _on_na_iso_cor_changed(self, is_checked: bool):
        """Saves the Na isotope correction setting."""
        self.config.settings.processing_settings.na_isotope_correction = is_checked
        self.config.save()

    @Slot(bool)
    def _on_m2_iso_cor_changed(self, is_checked: bool):
        """Saves the DB isotope correction setting."""
        self.config.settings.processing_settings.db_isotope_correction = is_checked
        self.config.save()

    @Slot(bool)
    def _on_online_cal_changed(self, is_checked: bool):
        """Saves the online calibration setting."""
        self.config.settings.processing_settings.online_calibration = is_checked
        self.config.save()

    @Slot(bool)
    def _on_imputation_changed(self, is_checked: bool):
        """Saves the imputation setting."""
        self.config.settings.processing_settings.imputation = is_checked
        self.config.save()

    def set_ui_components_status(self, active: bool) -> None:
        self.open_imzml_button.setEnabled(active)
        self.imzml_list_view.setEnabled(active)
        self.ppm_spinbox.setEnabled(active)
        self.bin_size_spinbox.setEnabled(active)
        self.database_combo_box.setEnabled(active)
        self.import_data_button.setEnabled(active)
        self.m2_iso_cor_checkbox.setEnabled(active)
        self.na_iso_cor_checkbox.setEnabled(active)
        self.cal_checkbox.setEnabled(active)
        self.cal_group_box.setEnabled(active)
        self.imputation_checkbox.setEnabled(active)
