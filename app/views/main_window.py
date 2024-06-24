import pandas as pd
from pyimzml.ImzMLParser import ImzMLParser
from PySide6.QtCore import QItemSelectionModel, Qt, QThreadPool
from PySide6.QtWidgets import QFileDialog, QMainWindow, QVBoxLayout

from app import __appname__
from app.config import Config
from app.database import LipidDB
from app.dataprocess import ImageType, SampleImageCollection
from app.figures import MplCanvas
from app.generated.MsiMainWindow_ui import Ui_MainWindow
from app.utils import BooleanDelegate, PandasModelEditable
from app.views.file_save_window import FileSaveWindow
from app.views.imzml_import_window import ImzmlImportWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Main window of the application
    """

    def __init__(self) -> None:
        super().__init__()
        self.database: LipidDB | None = None
        self.config: Config | None = None
        self.samples: dict[str, SampleImageCollection] | None = None
        self.ncols: int = 2
        self.nrows: int
        self.imzml_import_window = ImzmlImportWindow()
        self.save_window = FileSaveWindow()
        self.boolean_delegate = BooleanDelegate()

        self.setupUi(self)
        self.image_canvas_raw = MplCanvas(parent=self, canvas_type=ImageType.raw)
        self.verticalLayout_4.addWidget(self.image_canvas_raw)
        self.image_canvas_iso = MplCanvas(parent=self, canvas_type=ImageType.isotope)
        self.verticalLayout_2.addWidget(self.image_canvas_iso)
        self.image_canvas_quant = MplCanvas(parent=self, canvas_type=ImageType.quant)
        self.verticalLayout_3.addWidget(self.image_canvas_quant)

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
            value = model.get_is_checked(index.row())
            model.setData(model.index(index.row(), 2), not value)

        if event.key() == Qt.Key.Key_R:
            self.tab_widget.setCurrentIndex(0)

        if event.key() == Qt.Key.Key_Q:
            self.tab_widget.setCurrentIndex(2)

        if event.key() == Qt.Key.Key_I:
            self.tab_widget.setCurrentIndex(1)

        if event.key() == Qt.Key.Key_G:
            self.action_global.trigger()

    def connect_signals_slots(self) -> None:
        """Connect methods to signal slots."""
        self.action_open_imzml_dialog.triggered.connect(self.open_imzml_dialog)
        self.action_open_save_dialog.triggered.connect(self.open_save_dialog)
        self.action_global.triggered.connect(self.handle_species_selection_changed)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.imzml_import_window.finished_imzml_loading.connect(self.init_data)

    def open_imzml_dialog(self):
        """Launch the imzML import dialog."""
        self.imzml_import_window.set_ui_components_status(True)
        self.imzml_import_window.show()

    def open_save_dialog(self) -> None:
        """Launch the save images dialog."""
        self.save_window.set_ui_components_status(True)
        if self.database is not None:
            self.save_window.species_selection = self.species_table.model().get_checked_list()
            self.save_window.samples = self.samples
            self.save_window.global_scale = self.action_global.isChecked()
            self.save_window.nrows = self.nrows
            self.save_window.ncols = self.ncols
            self.save_window.show()

    def handle_species_selection_changed(self) -> None:
        global_scale = self.action_global.isChecked()
        species_id = None
        if self.database is not None:
            index = self.species_table.selectionModel().selectedRows()[0].row()
            species_id = self.database.get_id(index)
        if self.image_canvas_raw is not None and species_id is not None:
            self.image_canvas_raw.update_figure(
                samples=self.samples, species_id=species_id, global_scale=global_scale
            )
        if self.image_canvas_iso is not None and species_id is not None:
            self.image_canvas_iso.update_figure(
                samples=self.samples, species_id=species_id, global_scale=global_scale
            )
        if self.image_canvas_quant is not None and species_id is not None:
            self.image_canvas_quant.update_figure(
                samples=self.samples, species_id=species_id, global_scale=global_scale
            )

    def init_data(self) -> None:
        self.samples = self.imzml_import_window.samples
        self.database = self.imzml_import_window.database
        assert self.database is not None
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
        self.reset_canvas()
        self.setup_plots()
        self.handle_species_selection_changed()

    def setup_plots(self) -> None:
        nsamples = len(self.samples)
        self.nrows = nsamples // self.ncols + (nsamples % self.ncols > 0)
        self.image_canvas_raw.setup(nrows=self.nrows, ncols=self.ncols, nsamples=nsamples)
        self.image_canvas_iso.setup(nrows=self.nrows, ncols=self.ncols, nsamples=nsamples)
        self.image_canvas_quant.setup(nrows=self.nrows, ncols=self.ncols, nsamples=nsamples)
        # set height according to heuristic (multiply nrows by a factor that decreases by number of columns)
        self.scroll_area_raw_contents.setMinimumHeight((1 / self.ncols) * 800 * self.nrows)
        self.scroll_area_iso_contents.setMinimumHeight((1 / self.ncols) * 800 * self.nrows)
        self.scroll_area_quant_contents.setMinimumHeight((1 / self.ncols) * 800 * self.nrows)

    def reset_canvas(self) -> None:
        for ax in self.image_canvas_raw.fig.get_axes():
            ax.cla()
            ax.remove()
        for ax in self.image_canvas_iso.fig.get_axes():
            ax.cla()
            ax.remove()
        for ax in self.image_canvas_quant.fig.get_axes():
            ax.cla()
            ax.remove()

    def zoom_in(self) -> None:
        self.ncols -= 1
        if self.ncols < 1:
            self.ncols = 1
            return
        self.reset_canvas()
        self.setup_plots()
        self.handle_species_selection_changed()

    def zoom_out(self) -> None:
        self.ncols += 1
        self.reset_canvas()
        self.setup_plots()
        self.handle_species_selection_changed()
