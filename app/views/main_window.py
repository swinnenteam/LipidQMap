import sys
from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow

from app import __version__
from app.config import Config, config_paths, get_config
from app.database import LipidDB
from app.dataprocess import ImageType, SampleCollection
from app.generated.MsiMainWindow_ui import Ui_MainWindow
from app.matplotlib_figures import BarplotCanvas, MplCanvas
from app.qt_figures import SpectrumPlotView
from app.utils import BooleanDelegate, PandasModelEditable, open_folder
from app.views.about_window import AboutWindow
from app.views.calculator_window import CalculatorWindow
from app.views.file_save_window import FileSaveWindow
from app.views.imzml_import_window import ImzmlImportWindow
from app.views.scils_export_window import ScilsExportWindow
from app.views.settings_window import SettingsWindow
from app.views.hdf5_export_window import Hdf5ExportWindow


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
        self.config: Config = get_config()
        self.samples: SampleCollection | None = None
        self.active_sample_id: str = ""
        self.current_tab_type: ImageType = ImageType.raw
        self.ncols: int = 2
        self.nrows: int
        self.imzml_import_window = ImzmlImportWindow(config=self.config)
        self.save_window = FileSaveWindow(config=self.config)
        self.about_window = AboutWindow(__version__)
        self.settings_window = SettingsWindow(config=self.config)
        self.calculator_window = CalculatorWindow(config=self.config)
        self.hdf5_export_window = Hdf5ExportWindow(parent=self)
        self._scils_supported = sys.platform.startswith("win")
        self.scils_export_window: ScilsExportWindow | None = (
            ScilsExportWindow(parent=self) if self._scils_supported else None
        )
        self.boolean_delegate = BooleanDelegate()

        self.setupUi(self)
        self.image_canvas_raw = MplCanvas(
            parent=self, canvas_type=ImageType.raw, config=self.config
        )
        self.verticalLayout_4.addWidget(self.image_canvas_raw)
        self.image_canvas_iso = MplCanvas(
            parent=self, canvas_type=ImageType.isotope, config=self.config
        )
        self.verticalLayout_2.addWidget(self.image_canvas_iso)
        self.image_canvas_quant = MplCanvas(
            parent=self, canvas_type=ImageType.quant, config=self.config
        )
        self.verticalLayout_3.addWidget(self.image_canvas_quant)
        self.spectrum_view = SpectrumPlotView(config=self.config)
        self.verticalLayout_8.addWidget(self.spectrum_view)
        self.barplot_canvas = BarplotCanvas(parent=self)
        self.verticalLayout_6.addWidget(self.barplot_canvas)
        self.splitter_charts.setSizes([100, 0])
        self.connect_signals_slots()

    def closeEvent(self, event):
        for window in QApplication.topLevelWidgets():
            window.close()

    def keyPressEvent(self, event) -> None:
        """
        Handle key press events for navigation and interaction.

        Parameters:
        event (QKeyEvent): The key event to handle.
        """
        if event.key() == Qt.Key.Key_Down:
            # random = np.vstack((np.arange(100, 1700, 0.01), np.random.randint(0, 10000, 160000)))
            # self.spectrum_view.update_figure(random)
            if self.species_table.selectionModel() is None:
                return
            index = self.species_table.selectionModel().selectedRows()[0].row()
            self.species_table.selectRow(index + 1)

        if event.key() == Qt.Key.Key_Up:
            # self.spectrum_view.update_target(np.random.uniform(100, 1700), 0.05)
            if self.species_table.selectionModel() is None:
                return
            index = self.species_table.selectionModel().selectedRows()[0].row()
            self.species_table.selectRow(index - 1)

        if event.key() == Qt.Key.Key_Right:
            if self.species_table.selectionModel() is None:
                return
            index = self.species_table.selectionModel().selectedRows()[0].row()
            model = cast(PandasModelEditable, self.species_table.model())
            num_rows = model.rowCount()
            for i in range(index + 1, num_rows):
                if model.get_is_checked(i):
                    index = i
                    break
            self.species_table.selectRow(index)

        if event.key() == Qt.Key.Key_Left:
            if self.species_table.selectionModel() is None:
                return
            index = self.species_table.selectionModel().selectedRows()[0].row()
            model = cast(PandasModelEditable, self.species_table.model())
            num_rows = model.rowCount()
            for i in range(index - 1, -1, -1):
                if model.get_is_checked(i):
                    index = i
                    break
            self.species_table.selectRow(index)

        if event.key() == Qt.Key.Key_Space:
            if self.species_table.selectionModel() is None:
                return
            index = self.species_table.selectionModel().selectedRows()[0].row()
            model = cast(PandasModelEditable, self.species_table.model())
            value = model.get_is_checked(index)
            model.setData(model.index(index, 2), not value)

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
        self.action_export_python_pickle.triggered.connect(self.open_export_pickle_dialog)
        self.action_export_cardinal_HDF5.triggered.connect(self.open_export_cardinal_hdf5_dialog)
        if self._scils_supported and self.scils_export_window is not None:
            self.action_export_scils.triggered.connect(self.open_export_scils_dialog)
        else:
            self.action_export_scils.setEnabled(False)
            self.action_export_scils.setToolTip("SCiLS export is only available on Windows.")
        self.action_show_database_location.triggered.connect(self.open_database_location)
        self.action_open_about_dialog.triggered.connect(self.open_about_dialog)
        self.action_open_settings_window.triggered.connect(self.open_settings_dialog)
        self.action_open_calculator_dialog.triggered.connect(self.open_calculator_dialog)
        self.action_global.triggered.connect(self.update_plots)
        self.action_zoom_in.triggered.connect(self.zoom_in)
        self.action_zoom_out.triggered.connect(self.zoom_out)
        self.action_rotate_left.triggered.connect(self.rotate_left)
        self.action_rotate_right.triggered.connect(self.rotate_right)
        self.action_reflect_horizontal.triggered.connect(self.reflect_horizontal)
        self.action_reflect_vertical.triggered.connect(self.reflect_vertical)
        self.action_copy_species_plot.triggered.connect(self.copy_species_plot)
        self.action_select_all_species.triggered.connect(self.select_all_species)
        self.action_deselect_all_species.triggered.connect(self.deselect_all_species)
        self.imzml_import_window.finished_imzml_loading.connect(self.init_data)
        self.image_canvas_raw.image_clicked.connect(self.select_image)
        self.image_canvas_iso.image_clicked.connect(self.select_image)
        self.image_canvas_quant.image_clicked.connect(self.select_image)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.settings_window.settings_changed.connect(self.update_plots)
        self.settings_window.settings_changed.connect(self.update_table_selection)

    def open_imzml_dialog(self) -> None:
        """Launch the imzML import dialog."""
        self.imzml_import_window.set_ui_components_status(True)
        self.imzml_import_window.show()
        self.imzml_import_window.activateWindow()
        self.imzml_import_window.raise_()

    def open_save_dialog(self) -> None:
        """Launch the save images dialog."""
        self.save_window.set_ui_components_status(True)
        if self.database is not None:
            model = cast(PandasModelEditable, self.species_table.model())
            self.save_window.species_selection = model.get_checked_list()
            self.save_window.samples = self.samples
            self.save_window.global_scale = self.action_global.isChecked()
            self.save_window.nrows = self.nrows
            self.save_window.ncols = self.ncols
            self.save_window.show()
            self.save_window.activateWindow()
            self.save_window.raise_()

    def open_export_pickle_dialog(self) -> None:
        """Launch the export pickle dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder and self.samples is not None:
            self.samples.save_to_pickle(folder)

    def open_export_cardinal_hdf5_dialog(self) -> None:
        """Launch the Cardinal HDF5 export dialog."""
        if self.samples is None or self.database is None:
            return
        model_obj = self.species_table.model()
        if model_obj is None:
            return

        model = cast(PandasModelEditable, model_obj)
        checked_species = model.get_checked_list()
        all_species = model.get_all_ids()
        if not self.hdf5_export_window.set_context(
            samples=self.samples,
            database=self.database,
            species_ids=checked_species,
            all_species_ids=all_species,
        ):
            return

        self.hdf5_export_window.show()
        self.hdf5_export_window.activateWindow()
        self.hdf5_export_window.raise_()

    def open_export_scils_dialog(self) -> None:
        """Launch the SCiLS export dialog."""
        if self.scils_export_window is None or self.samples is None:
            return
        model_obj = self.species_table.model()
        if model_obj is None:
            return

        model = cast(PandasModelEditable, model_obj)
        checked_species = model.get_checked_list()
        all_species = model.get_all_ids()
        if not self.scils_export_window.set_context(
            samples=self.samples,
            database=self.database,
            species_ids=checked_species,
            all_species_ids=all_species,
        ):
            return

        self.scils_export_window.show()
        self.scils_export_window.activateWindow()
        self.scils_export_window.raise_()

    def open_database_location(self) -> None:
        """Open the folder containing the database files."""
        open_folder(config_paths["DATABASE_DIR"])

    def open_about_dialog(self) -> None:
        self.about_window.show()
        self.about_window.activateWindow()
        self.about_window.raise_()

    def open_settings_dialog(self) -> None:
        self.settings_window.samples = self.samples
        self.settings_window.show()
        self.settings_window.activateWindow()
        self.settings_window.raise_()

    def open_calculator_dialog(self) -> None:
        self.calculator_window.show()
        self.calculator_window.activateWindow()
        self.calculator_window.raise_()

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
        species_selection.selectionChanged.connect(self.update_plots)

        self.species_table.verticalHeader().setVisible(False)
        self.species_table.resizeColumnsToContents()
        self.species_table.keyPressEvent = self.keyPressEvent

        self.active_sample_id = next(iter(self.samples))

        self.reset_canvas()
        self.setup_plots()
        self.update_table_selection()
        self.species_table.selectRow(0)

    def setup_plots(self) -> None:
        """
        Set up the plots for displaying sample images.
        """
        if self.samples is None:
            return
        active_sample = self.samples[self.active_sample_id]
        if active_sample is None:
            return
        nsamples = len(self.samples)
        if nsamples == 1:
            self.ncols = 1
        dimensions = self.samples.dimensions()

        self.nrows = nsamples // self.ncols + (nsamples % self.ncols > 0)
        self.image_canvas_raw.setup(nrows=self.nrows, ncols=self.ncols, dimensions=dimensions)
        self.image_canvas_iso.setup(nrows=self.nrows, ncols=self.ncols, dimensions=dimensions)
        self.image_canvas_quant.setup(nrows=self.nrows, ncols=self.ncols, dimensions=dimensions)
        self.barplot_canvas.setup()
        self.spectrum_view.update_figure(active_sample.average_spectrum)
        # set height according to heuristic (multiply nrows by a factor that decreases by number of columns)
        self.scroll_area_raw_contents.setMinimumHeight(int((1 / self.ncols) * 800 * self.nrows))
        self.scroll_area_iso_contents.setMinimumHeight(int((1 / self.ncols) * 800 * self.nrows))
        self.scroll_area_quant_contents.setMinimumHeight(int((1 / self.ncols) * 800 * self.nrows))

    def update_plots(self) -> None:
        """
        Handle the event when the species selection is changed.
        """
        global_scale = self.action_global.isChecked()
        species_id = None
        if self.database is None:
            return

        index = self.species_table.selectionModel().selectedRows()[0].row()
        species_id = self.database.get_id(index)
        species = self.database.get(index)
        all_class_species = self.database.get_all_species_same_class(species_id)

        if species_id is None or self.samples is None:
            return

        active_sample = self.samples[self.active_sample_id]

        if self.image_canvas_raw is not None and active_sample is not None:
            self.image_canvas_raw.update_figure(
                samples=self.samples,
                species_id=species_id,
                active_sample_id=self.active_sample_id,
                global_scale=global_scale,
            )
            self.barplot_canvas.update_figure(
                sample=active_sample,
                species=all_class_species,
                image_type=self.current_tab_type,
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

        self.spectrum_view.update_target(target_mz=species.mz)

    def update_table_selection(self) -> None:
        """
        Sets the Export checkboxes in the species table based on the criteria
        in the settings
        """
        if self.samples:
            model = self.species_table.model()
            for i, species_check in enumerate(self.samples.criteria_check()):
                model.setData(model.index(i, 2), species_check)

    def select_all_species(self) -> None:
        """Mark every species row for export."""
        model = self.species_table.model()
        if model is None:
            return
        editable_model = cast(PandasModelEditable, model)
        for row in range(editable_model.rowCount()):
            if not editable_model.get_is_checked(row):
                editable_model.setData(
                    editable_model.index(row, 2),
                    Qt.CheckState.Checked,
                    Qt.ItemDataRole.CheckStateRole,
                )

    def deselect_all_species(self) -> None:
        """Clear the export flag on every species row."""
        model = self.species_table.model()
        if model is None:
            return
        editable_model = cast(PandasModelEditable, model)
        for row in range(editable_model.rowCount()):
            if editable_model.get_is_checked(row):
                editable_model.setData(
                    editable_model.index(row, 2),
                    Qt.CheckState.Unchecked,
                    Qt.ItemDataRole.CheckStateRole,
                )

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

        selected_sample = self.samples[image_id]
        if selected_sample is None:
            return

        self.barplot_canvas.update_figure(
            sample=selected_sample,
            species=all_class_species,
            image_type=self.current_tab_type,
        )

        self.spectrum_view.update_figure(selected_sample.average_spectrum)

    def copy_species_plot(self) -> None:
        self.barplot_canvas.copy_to_clipboard()

    def tab_changed(self) -> None:
        """
        Update the barplot on tab change.
        """
        match self.tab_widget.currentIndex():
            case 0:
                self.current_tab_type = ImageType.raw
            case 1:
                self.current_tab_type = ImageType.isotope
            case 2:
                self.current_tab_type = ImageType.quant

        self.current_tab_type
        if self.database is None or self.samples is None or self.species_table is None:
            return
        active_sample = self.samples[self.active_sample_id]
        if active_sample is None:
            return
        index = self.species_table.selectionModel().selectedRows()[0].row()

        species_id = self.database.get_id(index)
        all_class_species = self.database.get_all_species_same_class(species_id)

        self.barplot_canvas.update_figure(
            sample=active_sample,
            species=all_class_species,
            image_type=self.current_tab_type,
        )

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
        self.update_plots()

    def zoom_out(self) -> None:
        """
        Zoom out by increasing the number of columns and adjusting the layout.
        """
        self.ncols += 1
        self.reset_canvas()
        self.setup_plots()
        self.update_plots()

    def rotate_left(self) -> None:
        if self.samples is None:
            return
        active_sample = self.samples[self.active_sample_id]
        if active_sample is None:
            return
        active_sample.transform("rotate_left")
        self.update_plots()

    def rotate_right(self) -> None:
        if self.samples is None:
            return
        active_sample = self.samples[self.active_sample_id]
        if active_sample is None:
            return
        active_sample.transform("rotate_right")
        self.update_plots()

    def reflect_horizontal(self) -> None:
        if self.samples is None:
            return
        active_sample = self.samples[self.active_sample_id]
        if active_sample is None:
            return
        active_sample.transform("reflect_horizontal")
        self.update_plots()

    def reflect_vertical(self) -> None:
        if self.samples is None:
            return
        active_sample = self.samples[self.active_sample_id]
        if active_sample is None:
            return
        active_sample.transform("reflect_vertical")
        self.update_plots()
