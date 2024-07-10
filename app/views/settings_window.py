from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from app.config import Config
from app.dataprocess import SampleCollection
from app.generated.MsiSettingsDialog_ui import Ui_Dialog


class SettingsWindow(QWidget, Ui_Dialog):
    """
    Settings Window
    """

    settings_changed = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.setupUi(self)
        self.config = config
        self.samples: SampleCollection | None
        self.button_cancel.clicked.connect(self.close_window)
        self.button_save.clicked.connect(self.save_and_apply)
        self.check_box_gaussian_filter.setChecked(config.settings.filter_settings.gaussian_filter)
        self.spinbox_winsor_quant.setValue(
            config.settings.filter_settings.quant_image_winsorizing_percentile
        )
        self.spinbox_winsor_raw.setValue(
            config.settings.filter_settings.raw_image_winsorizing_percentile
        )
        self.spinbox_min_pixels.setValue(config.settings.selection_settings.minimum_pixels)
        self.spinbox_min_intensity.setValue(config.settings.selection_settings.minimum_intensity)

    def close_window(self) -> None:
        self.close()

    def save_and_apply(self) -> None:
        self.config.settings.filter_settings.gaussian_filter = (
            self.check_box_gaussian_filter.isChecked()
        )
        self.config.settings.filter_settings.quant_image_winsorizing_percentile = (
            self.spinbox_winsor_quant.value()
        )
        self.config.settings.filter_settings.raw_image_winsorizing_percentile = (
            self.spinbox_winsor_raw.value()
        )
        self.config.settings.selection_settings.minimum_pixels = self.spinbox_min_pixels.value()
        self.config.settings.selection_settings.minimum_intensity = (
            self.spinbox_min_intensity.value()
        )
        self.config.save()
        self.settings_changed.emit()
