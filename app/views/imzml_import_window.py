import os

from PySide6.QtCore import QThreadPool, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget

from app.config import Config, config_paths
from app.database import IonMode, LipidDB
from app.dataprocess import SampleCollection, load_database_image_collection
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
        self.database: LipidDB | None = None
        self.samples: SampleCollection
        self.setupUi(self)
        self.database_combo_box.addItems(fetch_db_list())
        self.update_ion_mode()
        self.pos_radio_button.setChecked(self.config.settings.processing_settings.pos_mode)
        self.neg_radio_button.setChecked(not self.config.settings.processing_settings.pos_mode)
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
        self.imputation_checkbox.setChecked(self.config.settings.processing_settings.imputation)
        # set last used database
        index = self.database_combo_box.findText(
            self.config.settings.database_settings.last_used_database
        )
        if index >= 0:
            self.database_combo_box.setCurrentIndex(index)
        self.connect_signals_slots()

    def connect_signals_slots(self) -> None:
        self.import_data_button.clicked.connect(self.process_imzml_files)
        self.open_imzml_button.clicked.connect(self.open_imzml_files)
        self.cal_checkbox.clicked.connect(self.toggle_cal_checked_value)
        self.pos_radio_button.clicked.connect(self.update_save_setting)
        self.neg_radio_button.clicked.connect(self.update_save_setting)
        self.cal_checkbox.clicked.connect(self.update_save_setting)
        self.ppm_spinbox.valueChanged.connect(self.update_save_setting)
        self.bin_size_spinbox.valueChanged.connect(self.update_save_setting)
        self.m2_iso_cor_checkbox.clicked.connect(self.update_save_setting)
        self.na_iso_cor_checkbox.clicked.connect(self.update_save_setting)
        self.calibrant_spinbox.valueChanged.connect(self.update_save_setting)
        self.cal_ppm_spinbox.valueChanged.connect(self.update_save_setting)
        self.cal_int_spinbox.valueChanged.connect(self.update_save_setting)
        self.pos_radio_button.clicked.connect(self.update_ion_mode)
        self.database_combo_box.currentTextChanged.connect(self.update_save_setting)
        self.imputation_checkbox.clicked.connect(self.update_save_setting)

    def process_imzml_files(self) -> None:

        if not self.filepath:
            raise ValueError("Please open an imzML file first.")

        self.set_ui_components_status(False)

        # process database path
        db_name = self.database_combo_box.currentText()
        db_path = os.path.join(config_paths["DATABASE_DIR"], db_name + ".xlsx")
        if not db_name:
            self.set_ui_components_status(True)
            raise ValueError(
                "Please select a database file, the readme provides details on how to create a database."
            )
        ion_mode = IonMode.positive if self.pos_radio_button.isChecked() else IonMode.negative

        # start database loading and imzML file processing on a new thread
        if self.filepath:
            worker = Worker(
                load_database_image_collection,
                database_path=db_path,
                ion_mode=ion_mode,
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

    @Slot()
    def handle_finished(self, database: LipidDB, samples: SampleCollection) -> None:
        """Emit results to main window"""
        self.samples = samples
        self.database = database
        self.finished_imzml_loading.emit()
        self.close()

    def open_imzml_files(self) -> None:
        """Open imzML files."""

        # clear file list
        self.imzml_list_view.clear()
        self.filepath, __ = QFileDialog.getOpenFileNames(
            self, "Select imzML file(s)", filter=";imzML(*.imzML)"
        )
        if self.filepath is None:
            return
        self.imzml_list_view.addItems([path.split(os.sep)[-1] for path in self.filepath])

    def update_ion_mode(self):
        if self.pos_radio_button.isChecked():
            self.calibrant_spinbox.setValue(self.config.settings.processing_settings.pos_calibrant)
        elif self.neg_radio_button.isChecked():
            self.calibrant_spinbox.setValue(self.config.settings.processing_settings.neg_calibrant)

    def toggle_cal_checked_value(self):
        self.calibrant_spinbox.setEnabled(self.cal_checkbox.isChecked())
        self.cal_ppm_spinbox.setEnabled(self.cal_checkbox.isChecked())
        self.cal_int_spinbox.setEnabled(self.cal_checkbox.isChecked())

    def update_save_setting(self):
        sender = self.sender()
        if sender == self.pos_radio_button:
            self.config.settings.processing_settings.pos_mode = sender.isChecked()
        elif sender == self.neg_radio_button:
            self.config.settings.processing_settings.pos_mode = not sender.isChecked()
        elif sender == self.database_combo_box:
            self.config.settings.database_settings.last_used_database = sender.currentText()
        elif sender == self.cal_int_spinbox:
            self.config.settings.processing_settings.calibration_min_intensity = sender.value()
        elif sender == self.bin_size_spinbox:
            self.config.settings.processing_settings.bin_size = sender.value()
        elif sender == self.cal_ppm_spinbox:
            self.config.settings.processing_settings.calibration_ppm = sender.value()
        elif sender == self.calibrant_spinbox:
            if self.pos_radio_button.isChecked():
                self.config.settings.processing_settings.pos_calibrant = sender.value()
            elif self.neg_radio_button.isChecked():
                self.config.settings.processing_settings.neg_calibrant = sender.value()
        elif sender == self.ppm_spinbox:
            self.config.settings.processing_settings.ppm = sender.value()
        elif sender == self.na_iso_cor_checkbox:
            self.config.settings.processing_settings.na_isotope_correction = sender.isChecked()
        elif sender == self.m2_iso_cor_checkbox:
            self.config.settings.processing_settings.db_isotope_correction = sender.isChecked()
        elif sender == self.cal_checkbox:
            self.config.settings.processing_settings.online_calibration = sender.isChecked()
        elif sender == self.imputation_checkbox:
            self.config.settings.processing_settings.imputation = sender.isChecked()
        self.config.save()

    def set_ui_components_status(self, active: bool) -> None:
        self.open_imzml_button.setEnabled(active)
        self.imzml_list_view.setEnabled(active)
        self.neg_radio_button.setEnabled(active)
        self.pos_radio_button.setEnabled(active)
        self.ppm_spinbox.setEnabled(active)
        self.bin_size_spinbox.setEnabled(active)
        self.database_combo_box.setEnabled(active)
        self.import_data_button.setEnabled(active)
        self.m2_iso_cor_checkbox.setEnabled(active)
        self.na_iso_cor_checkbox.setEnabled(active)
        self.cal_checkbox.setEnabled(active)
        self.cal_group_box.setEnabled(active)
        self.imputation_checkbox.setEnabled(active)
