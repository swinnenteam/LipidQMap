from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from app.config import Config
from app.generated.MsiSettingsDialog_ui import Ui_Dialog
from app.msi_data import SampleCollection


class SettingsWindow(QWidget, Ui_Dialog):
    """
    Settings Window
    """

    settings_changed = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.setupUi(self)
        self.config = config
        self._samples: SampleCollection | None = None
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
        self.spinbox_feature_noise_sigma.setValue(
            config.settings.selection_settings.feature_noise_sigma
        )
        self.spinbox_feature_min_pixels.setValue(
            config.settings.selection_settings.feature_minimum_pixels
        )
        self.radio_selection_threshold.toggled.connect(self._refresh_selection_controls)
        self.radio_selection_feature.toggled.connect(self._refresh_selection_controls)
        self.check_box_scalebar_enabled.toggled.connect(self._refresh_scalebar_controls)
        self.radio_scalebar_auto.toggled.connect(self._update_scalebar_manual_state)
        self.radio_scalebar_manual.toggled.connect(self._update_scalebar_manual_state)
        self._load_config_values()

    def close_window(self) -> None:
        self.close()

    @property
    def samples(self) -> SampleCollection | None:
        return self._samples

    @samples.setter
    def samples(self, value: SampleCollection | None) -> None:
        self._samples = value
        self._refresh_scalebar_controls()

    def _load_config_values(self) -> None:
        selection_settings = self.config.settings.selection_settings
        if selection_settings.selection_method == "feature":
            self.radio_selection_feature.setChecked(True)
        else:
            self.radio_selection_threshold.setChecked(True)
        self._refresh_selection_controls()

        settings = self.config.settings.scalebar_settings
        self.check_box_scalebar_enabled.setChecked(settings.enabled)
        if settings.auto:
            self.radio_scalebar_auto.setChecked(True)
        else:
            self.radio_scalebar_manual.setChecked(True)
        self.spinbox_scalebar_manual.setValue(settings.manual_length_um)
        self._update_scalebar_manual_state()

    def _refresh_selection_controls(self) -> None:
        threshold_enabled = self.radio_selection_threshold.isChecked()
        feature_enabled = self.radio_selection_feature.isChecked()

        for widget in (
            self.label_3,
            self.spinbox_min_pixels,
            self.label_4,
            self.spinbox_min_intensity,
        ):
            widget.setEnabled(threshold_enabled)

        for widget in (
            self.label_feature_noise,
            self.spinbox_feature_noise_sigma,
            self.label_feature_sigma,
            self.label_feature_pixels,
            self.spinbox_feature_min_pixels,
        ):
            widget.setEnabled(feature_enabled)

    def _update_scalebar_manual_state(self) -> None:
        self._refresh_scalebar_controls()

    def _refresh_scalebar_controls(self) -> None:
        enabled = self.check_box_scalebar_enabled.isChecked()
        self.radio_scalebar_auto.setEnabled(enabled)
        self.radio_scalebar_manual.setEnabled(enabled)
        self.label_scalebar_auto_value.setEnabled(enabled)
        if not enabled:
            self.label_scalebar_auto_value.setText("Scale bars disabled")
            self.spinbox_scalebar_manual.setEnabled(False)
            return

        auto_length: int | None = None
        max_length: int | None = None
        if self._samples:
            auto_length = self._samples.get_scalebar_auto_length_um()
            max_length = self._samples.get_scalebar_max_length_um()

        if auto_length is None:
            self.label_scalebar_auto_value.setText("Auto length: unavailable")
        else:
            self.label_scalebar_auto_value.setText(f"Auto length: ~ {auto_length} um")

        if max_length is None:
            self.spinbox_scalebar_manual.setMaximum(100000)
        else:
            self.spinbox_scalebar_manual.setMaximum(max_length)
            if self.spinbox_scalebar_manual.value() > max_length:
                self.spinbox_scalebar_manual.setValue(max_length)

        # keep manual control state consistent with current selection
        self.spinbox_scalebar_manual.setEnabled(self.radio_scalebar_manual.isChecked())

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
        self.config.settings.selection_settings.selection_method = (
            "feature" if self.radio_selection_feature.isChecked() else "threshold"
        )
        self.config.settings.selection_settings.feature_noise_sigma = (
            self.spinbox_feature_noise_sigma.value()
        )
        self.config.settings.selection_settings.feature_minimum_pixels = (
            self.spinbox_feature_min_pixels.value()
        )
        self.config.settings.scalebar_settings.enabled = self.check_box_scalebar_enabled.isChecked()
        self.config.settings.scalebar_settings.auto = self.radio_scalebar_auto.isChecked()
        manual_value = self.spinbox_scalebar_manual.value()
        manual_value = max(10, (manual_value // 10) * 10)
        self.config.settings.scalebar_settings.manual_length_um = manual_value
        if self.spinbox_scalebar_manual.value() != manual_value:
            self.spinbox_scalebar_manual.setValue(manual_value)
        self.config.save()
        self.settings_changed.emit()
