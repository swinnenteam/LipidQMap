import pandas as pd
from pyimzml.ImzMLParser import ImzMLParser
from PySide6.QtCore import QItemSelectionModel, Qt, QThreadPool
from PySide6.QtWidgets import QFileDialog, QMainWindow

from app import __appname__
from app.config import Config
from app.database import LipidDB
from app.dataprocess import SampleImageCollection, isotope_correction, load_ion_images, quantitaton
from app.figures import MplCanvas
from app.generated.MsiMainWindow_ui import Ui_MainWindow
from app.multithreading import Worker
from app.utils import PandasModelEditable


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Main window of the application
    """

    def __init__(self) -> None:
        super().__init__()
        self.database: LipidDB | None = None
        self.config: Config | None = None
        self.species_selection: pd.DataFrame | None = None
        self.image_canvas: MplCanvas | None = None
        self.imzml_parser: ImzMLParser | None = None
        self.image_collection: SampleImageCollection = SampleImageCollection()
        self.setupUi(self)
        self.connect_signals_slots()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Down:
            index = self.species_table.selectionModel().selectedRows()[0].row()
            self.species_table.selectRow(index + 1)

        if event.key() == Qt.Key.Key_Up:
            index = self.species_table.selectionModel().selectedRows()[0].row()
            self.species_table.selectRow(index - 1)

        if event.key() == Qt.Key.Key_Space:
            index = self.species_table.selectionModel().selectedRows()[0]
            model = self.species_table.model()
            value = model.get_checked(index.row())
            model.setData(model.index(index.row(), 2), not value)

    def connect_signals_slots(self) -> None:
        """Connect methods to signal slots."""

        self.action_open_imzml_file.triggered.connect(self.open_imzml_file)  # type: ignore

    def process_imzml_files(self, progress_callback, filepath) -> None:
        assert self.database
        self.imzml_parser = ImzMLParser(filepath[0])
        self.image_collection.raw = load_ion_images(database=self.database, imzml=self.imzml_parser)
        self.image_collection.isotope = isotope_correction(
            database=self.database, images=self.image_collection.raw
        )
        self.image_collection.quant = quantitaton(
            database=self.database, images=self.image_collection.isotope
        )
        self.handle_species_selection_changed()

    def open_imzml_file(self) -> None:
        """Load an imzML file."""
        filepath, __ = QFileDialog.getOpenFileNames(
            self, "Select imzML file(s)", filter=";imzML(*.imzML)"
        )
        if filepath:
            assert self.image_canvas
            self.image_canvas.setup()
            worker = Worker(self.process_imzml_files, filepath=filepath)
            # worker.signals.progress.connect(splash_screen.handle_progress)
            # worker.signals.finished.connect(splash_screen.handle_finished)
            threadpool = QThreadPool()
            threadpool.start(worker)

    def handle_species_selection_changed(self) -> None:
        if self.image_canvas is not None and self.database is not None:
            index = self.species_table.selectionModel().selectedRows()[0].row()
            species_id = self.database.get_id(index)
            self.image_canvas.update_figure(
                image_collection=self.image_collection, species_id=species_id
            )

    def init_table(self) -> None:
        assert self.database is not None
        self.species_table_data = self.database.get_table()
        self.species_table.setModel(PandasModelEditable(self.species_table_data))
        species_selection = self.species_table.selectionModel()
        species_selection.selectionChanged.connect(self.handle_species_selection_changed)

        self.species_table.verticalHeader().setVisible(False)
        self.species_table.resizeColumnsToContents()
        self.species_table.selectRow(0)

        self.species_table.keyPressEvent = self.keyPressEvent

        hint = self.species_table.sizeHint()
        self.frame_2.setMaximumWidth(hint.width() * 1.3)
        self.frame_2.adjustSize()

        self.image_canvas = MplCanvas(self)
        self.gridLayout.addWidget(self.image_canvas)
