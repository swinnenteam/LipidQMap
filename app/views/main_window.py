from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

from app import __appname__, __version__
from app.config import Config
from app.database import LipidDB
from app.dataprocess import ImageType, SampleImageCollection
from app.figures import BarplotCanvas, MplCanvas
from app.generated.MsiMainWindow_ui import Ui_MainWindow
from app.utils import BooleanDelegate, PandasModelEditable
from app.views.about_window import AboutWindow
from app.views.file_save_window import FileSaveWindow
from app.views.imzml_import_window import ImzmlImportWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    Main window of the application.

    This class manages the main interface of the application, handling user interactions,
    displaying sample images, and managing the application's state.
    """

    def __init__(self) -> None:
        """
        Initialize the main window and set up the UI components.
        """
        super().__init__()
        self.database: LipidDB | None = None
        self.config: Config | None = None
        self.samples: dict[str, SampleImageCollection] | None = None
        self.active_sample_id: str = ""
        self.ncols: int = 2
        self.nrows: int
        self.imzml_import_window = ImzmlImportWindow()
        self.save_window = FileSaveWindow()
        self.about_window = AboutWindow(__version__)
        self.boolean_delegate = BooleanDelegate()

        self.setupUi(self)
        self.image_canvas_raw = MplCanvas(parent=self, canvas_type=ImageType.raw)
        self.verticalLayout_4.addWidget(self.image_canvas_raw)
        self.image_canvas_iso = MplCanvas(parent=self, canvas_type=ImageType.isotope)
        self.verticalLayout_2.addWidget(self.image_canvas_iso)
        self.image_canvas_quant = MplCanvas(parent=self, canvas_type=ImageType.quant)
        self.verticalLayout_3.addWidget(self.image_canvas_quant)
        self.barplot_canvas = BarplotCanvas(parent=self)
        self.verticalLayout_5.addWidget(self.barplot_canvas)
        self.splitter_barplot.setSizes([100, 0])
        self.connect_signals_slots()

    def keyPressEvent(self, event) -> None:
        """
        Handle key press events for navigation and interaction.

        Parameters:
        event (QKeyEvent): The key event to handle.
        """
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
        self.action_open_about_dialog.triggered.connect(self.open_about_dialog)
        self.action_global.triggered.connect(self.handle_species_selection_changed)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_rotate_left.triggered.connect(self.rotate_left)
        self.action_rotate_right.triggered.connect(self.rotate_right)
        self.action_reflect_horizontal.triggered.connect(self.reflect_horizontal)
        self.action_reflect_vertical.triggered.connect(self.reflect_vertical)
        self.imzml_import_window.finished_imzml_loading.connect(self.init_data)
        self.image_canvas_raw.image_clicked.connect(self.select_image)
        self.image_canvas_iso.image_clicked.connect(self.select_image)
        self.image_canvas_quant.image_clicked.connect(self.select_image)

    def open_imzml_dialog(self) -> None:
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

    def open_about_dialog(self) -> None:
        self.about_window.show()

    def handle_species_selection_changed(self) -> None:
        """
        Handle the event when the species selection is changed.
        """
        global_scale = self.action_global.isChecked()
        species_id = None
        if self.database is not None:
            index = self.species_table.selectionModel().selectedRows()[0].row()
            species_id = self.database.get_id(index)
            all_class_species = self.database.get_all_species_same_class(species_id)

        if species_id is None or self.samples is None:
            return

        if self.image_canvas_raw is not None:
            self.image_canvas_raw.update_figure(
                samples=self.samples,
                species_id=species_id,
                active_sample_id=self.active_sample_id,
                global_scale=global_scale,
            )
            self.barplot_canvas.update_figure(
                sample=self.samples[self.active_sample_id], species=all_class_species
            )
        if self.image_canvas_iso is not None:
            self.image_canvas_iso.update_figure(
                samples=self.samples,
                species_id=species_id,
                active_sample_id=self.active_sample_id,
                global_scale=global_scale,
            )
        if self.image_canvas_quant is not None:
            self.image_canvas_quant.update_figure(
                samples=self.samples,
                species_id=species_id,
                active_sample_id=self.active_sample_id,
                global_scale=global_scale,
            )

    def init_data(self) -> None:
        """
        Initialize data after loading imzML files.
        """
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
        self.species_table.keyPressEvent = self.keyPressEvent

        hint = self.species_table.sizeHint()
        self.frame_2.setMaximumWidth(hint.width() * 1.2)
        self.frame_2.adjustSize()

        self.active_sample_id = next(iter(self.samples))

        self.reset_canvas()
        self.setup_plots()
        self.species_table.selectRow(0)

    def setup_plots(self) -> None:
        """
        Set up the plots for displaying sample images.
        """
        if self.samples is None:
            return
        nsamples = len(self.samples)
        dimensions = [sample.shape for sample in self.samples.values()]

        self.nrows = nsamples // self.ncols + (nsamples % self.ncols > 0)
        self.image_canvas_raw.setup(nrows=self.nrows, ncols=self.ncols, dimensions=dimensions)
        self.image_canvas_iso.setup(nrows=self.nrows, ncols=self.ncols, dimensions=dimensions)
        self.image_canvas_quant.setup(nrows=self.nrows, ncols=self.ncols, dimensions=dimensions)
        self.barplot_canvas.setup()
        # set height according to heuristic (multiply nrows by a factor that decreases by number of columns)
        self.scroll_area_raw_contents.setMinimumHeight((1 / self.ncols) * 800 * self.nrows)
        self.scroll_area_iso_contents.setMinimumHeight((1 / self.ncols) * 800 * self.nrows)
        self.scroll_area_quant_contents.setMinimumHeight((1 / self.ncols) * 800 * self.nrows)

    def select_image(self, image_id: str) -> None:
        """
        Set the active (clicked on) image.
        """
        self.active_sample_id = image_id
        self.image_canvas_raw.set_active_image(image_id)
        self.image_canvas_iso.set_active_image(image_id)
        self.image_canvas_quant.set_active_image(image_id)

        index = self.species_table.selectionModel().selectedRows()[0].row()
        if self.database is None or self.samples is None:
            return
        species_id = self.database.get_id(index)
        all_class_species = self.database.get_all_species_same_class(species_id)

        self.barplot_canvas.update_figure(sample=self.samples[image_id], species=all_class_species)

    def reset_canvas(self) -> None:
        """
        Reset the canvases by clearing and removing all axes.
        """
        self.image_canvas_raw.reset_canvas()
        self.image_canvas_iso.reset_canvas()
        self.image_canvas_quant.reset_canvas()
        self.barplot_canvas.reset_canvas()

    def zoom_in(self) -> None:
        """
        Zoom in by decreasing the number of columns and adjusting the layout.
        """
        self.ncols -= 1
        if self.ncols < 1:
            self.ncols = 1
            return
        self.reset_canvas()
        self.setup_plots()
        self.handle_species_selection_changed()

    def zoom_out(self) -> None:
        """
        Zoom out by increasing the number of columns and adjusting the layout.
        """
        self.ncols += 1
        self.reset_canvas()
        self.setup_plots()
        self.handle_species_selection_changed()

    def rotate_left(self) -> None:
        if self.samples is not None:
            self.samples[self.active_sample_id].transform("rotate_left")
            self.handle_species_selection_changed()

    def rotate_right(self) -> None:
        if self.samples is not None:
            self.samples[self.active_sample_id].transform("rotate_right")
            self.handle_species_selection_changed()

    def reflect_horizontal(self) -> None:
        if self.samples is not None:
            self.samples[self.active_sample_id].transform("reflect_horizontal")
            self.handle_species_selection_changed()

    def reflect_vertical(self) -> None:
        if self.samples is not None:
            self.samples[self.active_sample_id].transform("reflect_vertical")
            self.handle_species_selection_changed()
