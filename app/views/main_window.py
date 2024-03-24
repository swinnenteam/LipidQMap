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
from app.utils import BooleanDelegate, PandasModelEditable
from app.views.imzml_import_window import ImzmlImportWindow


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
        # self.imzml_parser: ImzMLParser | None = None
        self.image_collection: SampleImageCollection
        self.imzml_import_window = ImzmlImportWindow()
        self.boolean_delegate = BooleanDelegate()
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
        self.action_open_imzml_dialog.triggered.connect(self.open_imzml_dialog)  # type: ignore
        self.imzml_import_window.finished_imzml_loading.connect(self.init_data)

    def open_imzml_dialog(self):
        """Launch the imzML import dialog."""
        # self.db_window.fatty_acid_database = self.fatty_acid_database
        self.imzml_import_window.set_ui_components_status(True)
        self.imzml_import_window.show()

    def handle_species_selection_changed(self) -> None:
        if self.image_canvas is not None and self.database is not None:
            index = self.species_table.selectionModel().selectedRows()[0].row()
            species_id = self.database.get_id(index)
            self.image_canvas.update_figure(
                image_collection=self.image_collection, species_id=species_id
            )

    def init_data(self) -> None:
        self.image_collection = self.imzml_import_window.image_collection
        self.database = self.imzml_import_window.database
        self.species_table_data = self.database.get_table()
        self.species_table.setModel(PandasModelEditable(self.species_table_data))
        self.species_table.setItemDelegateForColumn(2, self.boolean_delegate)
        species_selection = self.species_table.selectionModel()
        species_selection.selectionChanged.connect(self.handle_species_selection_changed)

        self.species_table.verticalHeader().setVisible(False)
        self.species_table.resizeColumnsToContents()
        self.species_table.selectRow(0)

        self.species_table.keyPressEvent = self.keyPressEvent

        hint = self.species_table.sizeHint()
        self.frame_2.setMaximumWidth(hint.width() * 1.2)
        self.frame_2.adjustSize()

        self.image_canvas = MplCanvas(self)
        self.image_canvas.setup()
        self.gridLayout.addWidget(self.image_canvas)

        self.handle_species_selection_changed()
