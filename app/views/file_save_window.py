from PySide6.QtCore import QThreadPool, Slot
from PySide6.QtWidgets import QFileDialog, QWidget

from app.config import Config
from app.dataprocess import SampleCollection
from app.figures import save_image_collection
from app.generated.MsiSaveDialog_ui import Ui_MsiSaveDialog


class FileSaveWindow(QWidget, Ui_MsiSaveDialog):
    """
    Window in which the images can be saved.
    """

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.threadpool = QThreadPool()
        self.savepath: str | None = None
        self.samples: SampleCollection | None = None
        self.species_selection: list[str] | None = None
        self.nrows: int
        self.ncols: int
        self.global_scale: bool
        self.setupUi(self)
        self.connect_signals_slots()

        self.check_box_save_raw.setChecked(config.settings.save_settings.save_raw_images)
        self.check_box_save_iso.setChecked(config.settings.save_settings.save_iso_images)
        self.check_box_save_quant.setChecked(config.settings.save_settings.save_quant_images)
        self.check_box_save_individual.setChecked(
            config.settings.save_settings.save_individual_unfiltered
        )
        self.check_box_save_filtered.setChecked(
            config.settings.save_settings.save_individual_filtered_scaled
        )
        self.check_box_save_multi.setChecked(
            config.settings.save_settings.save_panel_filtered_scaled
        )

    def connect_signals_slots(self) -> None:

        self.button_choose_save_folder.clicked.connect(self.select_folder)
        self.button_save.clicked.connect(self.save_files)
        self.button_cancel.clicked.connect(self.exit)
        self.check_box_save_raw.clicked.connect(self.update_save_setting)
        self.check_box_save_iso.clicked.connect(self.update_save_setting)
        self.check_box_save_quant.clicked.connect(self.update_save_setting)
        self.check_box_save_individual.clicked.connect(self.update_save_setting)
        self.check_box_save_filtered.clicked.connect(self.update_save_setting)
        self.check_box_save_multi.clicked.connect(self.update_save_setting)

    def select_folder(self) -> None:
        self.savepath = QFileDialog.getExistingDirectory(self, "Select a Folder")
        if self.savepath is None:
            return
        self.line_edit_save_folder.setText(self.savepath)

    def save_files(self) -> None:

        if not self.savepath:
            raise ValueError("Please choose a folder to save to.")
        if self.samples is None:
            raise ValueError("No samples have been loaded.")
        if not self.species_selection:
            raise ValueError("No species have been selected.")

        self.set_ui_components_status(False)

        # start saving the files
        # ideally the saving would be on it's own thread, but Matplotlib is not thread safe and crashes
        """
        if self.savepath:
            worker = Worker(
                save_image_collection,
                savepath=self.savepath,
                samples=self.samples,
                species_selection=self.species_selection,
                config=config,
            )
            worker.signals.progress_overall.connect(self.handle_progress_overall)
            worker.signals.finished.connect(self.exit)
            self.threadpool.start(worker)
        """

        save_image_collection(
            savepath=self.savepath,
            samples=self.samples,
            species_selection=self.species_selection,
            global_scale=self.global_scale,
            nrows=self.nrows,
            ncols=self.ncols,
            config=self.config,
        )
        self.exit()

    @Slot()
    def handle_progress_overall(self, overall_progress: int) -> None:
        """Update progressbar"""
        self.progress_bar_save_images.setValue(overall_progress)

    def update_save_setting(self):
        sender = self.sender()
        if sender == self.check_box_save_raw:
            self.config.settings.save_settings.save_raw_images = sender.isChecked()
        elif sender == self.check_box_save_iso:
            self.config.settings.save_settings.save_iso_images = sender.isChecked()
        elif sender == self.check_box_save_quant:
            self.config.settings.save_settings.save_quant_images = sender.isChecked()
        elif sender == self.check_box_save_individual:
            self.config.settings.save_settings.save_individual_unfiltered = sender.isChecked()
        elif sender == self.check_box_save_filtered:
            self.config.settings.save_settings.save_individual_filtered_scaled = sender.isChecked()
        elif sender == self.check_box_save_multi:
            self.config.settings.save_settings.save_panel_filtered_scaled = sender.isChecked()
        self.config.save()

    def set_ui_components_status(self, active: bool) -> None:
        self.check_box_save_raw.setEnabled(active)
        self.check_box_save_iso.setEnabled(active)
        self.check_box_save_quant.setEnabled(active)
        self.check_box_save_individual.setEnabled(active)
        self.check_box_save_filtered.setEnabled(active)
        self.check_box_save_multi.setEnabled(active)
        self.button_choose_save_folder.setEnabled(active)

    @Slot()
    def exit(self):
        self.progress_bar_save_images.setValue(0)
        self.close()
