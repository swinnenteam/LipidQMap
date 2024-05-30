import os

from PySide6.QtCore import Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget

from app.config import config, config_paths
from app.database import IonMode, LipidDB
from app.dataprocess import SampleImageCollection, load_database_image_collection
from app.generated.MsiImportDialog_ui import Ui_Dialog
from app.multithreading import Worker2


class ImzmlImportWindow(QWidget, Ui_Dialog):
    """
    Window in which imzML import setting are configured.
    """

    finished_imzml_loading = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.threadpool = QThreadPool()
        self.filepath: list[str] | None = None
        self.database: LipidDB | None = None
        self.setupUi(self)
        self.connect_signals_slots()
        self.fetch_db_list()
        self.update_ion_mode()
        self.ppm_spinbox.setValue(config.settings.processing_settings.ppm)
        self.m2_iso_cor_checkbox.setChecked(
            config.settings.processing_settings.m2_isotope_correction
        )
        self.na_iso_cor_checkbox.setChecked(
            config.settings.processing_settings.na_isotope_correction
        )
        self.cal_checkbox.setChecked(config.settings.processing_settings.online_calibration)
        self.cal_ppm_spinbox.setValue(config.settings.processing_settings.calibration_ppm)
        self.cal_int_spinbox.setValue(config.settings.processing_settings.calibration_max_intensity)
        # set last used database
        index = self.database_combo_box.findText(
            config.settings.database_settings.last_used_database
        )
        if index >= 0:
            self.database_combo_box.setCurrentIndex(index)

    def connect_signals_slots(self) -> None:
        self.import_data_button.clicked.connect(self.process_imzml_files)
        self.open_imzml_button.clicked.connect(self.open_imzml_files)
        self.ppm_spinbox.valueChanged.connect(self.update_ppm_value)
        self.m2_iso_cor_checkbox.clicked.connect(self.update_m2_iso_cor)
        self.na_iso_cor_checkbox.clicked.connect(self.update_na_iso_cor)
        self.cal_checkbox.clicked.connect(self.update_cal_checked_value)
        self.calibrant_spinbox.valueChanged.connect(self.update_calibrant)
        self.cal_ppm_spinbox.valueChanged.connect(self.update_cal_ppm)
        self.cal_int_spinbox.valueChanged.connect(self.update_cal_intensity)
        self.pos_radio_button.clicked.connect(self.update_ion_mode)
        # self.database_combo_box.currentTextChanged.connect(self.update_last_used_database)

    def fetch_db_list(self):
        dbs = os.listdir(config_paths["DATABASE_DIR"])
        dbs = list(filter(lambda f: f.endswith(".xlsx"), dbs))
        dbs = [s.strip(".xlsx") for s in dbs]
        self.database_combo_box.addItems(dbs)

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
            worker = Worker2(
                load_database_image_collection,
                database_path=db_path,
                ion_mode=ion_mode,
                imzml_path=self.filepath[0],
                config=config,
            )
            worker.signals.progress.connect(self.handle_progress)
            worker.signals.result.connect(self.handle_finished)
            self.threadpool.start(worker)

    @Slot()
    def handle_progress(self, value: int) -> None:
        """Update progressbar"""
        self.progress_bar.setValue(value)

    @Slot()
    def handle_finished(self, database: LipidDB, image_collection: SampleImageCollection) -> None:
        """Emit results to main window"""
        self.image_collection = image_collection
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
            self.calibrant_spinbox.setValue(config.settings.processing_settings.pos_calibrant)
        elif self.neg_radio_button.isChecked():
            self.calibrant_spinbox.setValue(config.settings.processing_settings.neg_calibrant)

    def update_m2_iso_cor(self):
        config.settings.processing_settings.m2_isotope_correction = (
            self.m2_iso_cor_checkbox.isChecked()
        )
        config.save()

    def update_na_iso_cor(self):
        config.settings.processing_settings.na_isotope_correction = (
            self.na_iso_cor_checkbox.isChecked()
        )
        config.save()

    def update_ppm_value(self):
        config.settings.processing_settings.ppm = self.ppm_spinbox.value()
        config.save()

    def update_cal_checked_value(self):
        config.settings.processing_settings.online_calibration = self.cal_checkbox.isChecked()
        self.calibrant_spinbox.setEnabled(self.cal_checkbox.isChecked())
        self.cal_ppm_spinbox.setEnabled(self.cal_checkbox.isChecked())
        self.cal_int_spinbox.setEnabled(self.cal_checkbox.isChecked())
        config.save()

    def update_calibrant(self):
        if self.pos_radio_button.isChecked():
            config.settings.processing_settings.pos_calibrant = self.calibrant_spinbox.value()
        elif self.neg_radio_button.isChecked():
            config.settings.processing_settings.neg_calibrant = self.calibrant_spinbox.value()
        config.save()

    def update_cal_ppm(self):
        config.settings.processing_settings.calibration_ppm = self.cal_ppm_spinbox.value()
        config.save()

    def update_cal_intensity(self):
        config.settings.processing_settings.calibration_max_intensity = self.cal_int_spinbox.value()
        config.save()

    def update_last_used_database(self):
        config.settings.database_settings.last_used_database = self.database_combo_box.currentText()
        config.save()

    def set_ui_components_status(self, active: bool) -> None:
        self.open_imzml_button.setEnabled(active)
        self.imzml_list_view.setEnabled(active)
        self.neg_radio_button.setEnabled(active)
        self.pos_radio_button.setEnabled(active)
        self.ppm_spinbox.setEnabled(active)
        self.database_combo_box.setEnabled(active)
        self.import_data_button.setEnabled(active)
        self.m2_iso_cor_checkbox.setEnabled(active)
        self.na_iso_cor_checkbox.setEnabled(active)
        self.cal_checkbox.setEnabled(active)
        self.cal_group_box.setEnabled(active)
