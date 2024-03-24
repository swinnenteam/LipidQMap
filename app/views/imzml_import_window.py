import os

from pyimzml.ImzMLParser import ImzMLParser
from PySide6.QtCore import QItemSelectionModel, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMainWindow, QWidget

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
        self.database: LipidDB | None = None
        self.setupUi(self)
        self.connect_signals_slots()
        self.fetch_db_list()
        self.ppm_spin_box.setValue(config.settings.processing_settings.ppm)

    def connect_signals_slots(self) -> None:
        self.import_data_button.clicked.connect(self.process_imzml_files)
        self.open_imzml_button.clicked.connect(self.open_imzml_files)
        self.ppm_spin_box.valueChanged.connect(self.update_ppm_value)

    def fetch_db_list(self):
        dbs = os.listdir(config_paths["DATABASE_DIR"])
        dbs = list(filter(lambda f: f.endswith(".xlsx"), dbs))
        dbs = [s.strip(".xlsx") for s in dbs]
        self.database_combo_box.addItems(dbs)

    def process_imzml_files(self) -> None:
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
            )
            worker.signals.progress.connect(self.handle_progress)
            worker.signals.result.connect(self.handle_finished)
            self.threadpool.start(worker)

    @Slot()
    def handle_progress(self, value) -> None:
        """Update progressbar"""
        self.progress_bar.setValue(value)

    @Slot()
    def handle_finished(self, database, image_collection) -> None:
        """Emit results to main window"""
        self.image_collection = image_collection
        self.database = database
        self.finished_imzml_loading.emit()
        self.close()

    def open_imzml_files(self) -> None:
        """Open imzML files."""
        self.filepath, __ = QFileDialog.getOpenFileNames(
            self, "Select imzML file(s)", filter=";imzML(*.imzML)"
        )

        self.imzml_list_view.addItems([path.split(os.sep)[-1] for path in self.filepath])

    def update_ppm_value(self):
        config.settings.processing_settings.ppm = self.ppm_spin_box.value()
        config.save()

    def set_ui_components_status(self, active: bool) -> None:
        self.open_imzml_button.setEnabled(active)
        self.imzml_list_view.setEnabled(active)
        self.neg_radio_button.setEnabled(active)
        self.pos_radio_button.setEnabled(active)
        self.ppm_spin_box.setEnabled(active)
        self.database_combo_box.setEnabled(active)
        self.import_data_button.setEnabled(active)
