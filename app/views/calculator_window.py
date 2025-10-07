import os
from typing import Optional

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QMessageBox, QWidget

from app.config import Config, config_paths
from app.database import DatabaseEditor
from app.generated.MsiStandardCalculatorDialog_ui import Ui_Dialog
from app.sprayer import SprayRun
from app.views.imzml_import_window import fetch_db_list


class CalculatorWindow(QWidget, Ui_Dialog):
    """
    Standards calculator Window
    """

    settings_changed = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.setupUi(self)
        self.config = config
        self.db_writer: Optional[DatabaseEditor] = None
        self._last_valid_db_index: Optional[int] = None
        self.sprayrun: SprayRun
        self.setup_combo_box()
        self.database_combo_box.currentIndexChanged.connect(self.database_selection_changed)
        self.standards_list_view.currentRowChanged.connect(self.standards_selection_changed)
        self.database_selection_changed()
        self.quantity_line_edit.textChanged.connect(self.quantity_changed)
        self.cancel_button.clicked.connect(self.close_window)
        self.save_button.clicked.connect(self.save_and_close)
        # Ensure quantity_line_edit accepts only float numbers
        float_validator = QDoubleValidator()
        float_validator.setDecimals(4)  # Limit to 4 decimal places
        float_validator.setBottom(0.0)  # Set minimum value to 0
        self.quantity_line_edit.setValidator(float_validator)

        self.label_area_template = "1. Area: {} mm²"
        self.label_volume_template = "2. Volume sprayed: {} mL"
        self.label_mix_conc_template = "3. Spraying mix concentration: {} pmol/mL"
        self.label_surface_conc_template = "4. Sprayed on surface"
        self.label_surface_conc_result_template = "{} pmol/mm²"

        self.spinbox_x_left.setValue(self.config.settings.sprayer_settings.x_left)
        self.spinbox_x_right.setValue(self.config.settings.sprayer_settings.x_right)
        self.spinbox_y_bottom.setValue(self.config.settings.sprayer_settings.y_bottom)
        self.spinbox_y_top.setValue(self.config.settings.sprayer_settings.y_top)
        self.spinbox_margin.setValue(self.config.settings.sprayer_settings.margin)
        self.spinbox_total_used_volume.setValue(
            self.config.settings.sprayer_settings.total_used_volume_mL
        )
        self.spinbox_syringe_flow.setValue(
            self.config.settings.sprayer_settings.syringe_flow_mL_per_min
        )
        self.spinbox_drying_time.setValue(self.config.settings.sprayer_settings.drying_time_min)
        self.spinbox_drying_cycles.setValue(self.config.settings.sprayer_settings.drying_cycles)
        self.spinbox_initial_equilibration.setValue(
            self.config.settings.sprayer_settings.initial_equilibration_min
        )
        self.spinbox_stock_conc.setValue(self.config.settings.sprayer_settings.stock_conc_mg_per_mL)
        self.spinbox_working_dilution_factor.setValue(
            self.config.settings.sprayer_settings.working_dilution_factor
        )
        self.spinbox_volume_working_stock.setValue(
            self.config.settings.sprayer_settings.volume_working_stock_uL
        )
        self.spinbox_final_mix_volume.setValue(
            self.config.settings.sprayer_settings.final_mix_volume_mL
        )
        self.spinbox_molecular_weight.setValue(
            self.config.settings.sprayer_settings.molecular_weight_ug_per_umol
        )

        self.connect_signals_slots()

        self.update_data_model()

    def connect_signals_slots(self) -> None:
        """
        Connect signals from UI widgets to their corresponding slots.
        """

        self.spinbox_x_left.valueChanged.connect(self.update_data_model)
        self.spinbox_x_right.valueChanged.connect(self.update_data_model)
        self.spinbox_y_bottom.valueChanged.connect(self.update_data_model)
        self.spinbox_y_top.valueChanged.connect(self.update_data_model)
        self.spinbox_margin.valueChanged.connect(self.update_data_model)
        self.spinbox_total_used_volume.valueChanged.connect(self.update_data_model)
        self.spinbox_syringe_flow.valueChanged.connect(self.update_data_model)
        self.spinbox_drying_time.valueChanged.connect(self.update_data_model)
        self.spinbox_drying_cycles.valueChanged.connect(self.update_data_model)
        self.spinbox_initial_equilibration.valueChanged.connect(self.update_data_model)
        self.spinbox_stock_conc.valueChanged.connect(self.update_data_model)
        self.spinbox_working_dilution_factor.valueChanged.connect(self.update_data_model)
        self.spinbox_volume_working_stock.valueChanged.connect(self.update_data_model)
        self.spinbox_final_mix_volume.valueChanged.connect(self.update_data_model)
        self.spinbox_molecular_weight.valueChanged.connect(self.update_data_model)
        self.apply_button.clicked.connect(self.apply_calculations)

    def database_selection_changed(self) -> None:
        self.standards_list_view.clear()
        db_name = self.database_combo_box.currentText()
        db_path = os.path.join(config_paths["DATABASE_DIR"], db_name + ".xlsx")
        try:
            self.db_writer = DatabaseEditor(db_path)
        except ValueError as exc:
            QMessageBox.critical(
                self,
                "Invalid Database",
                f"Failed to open '{db_name}.xlsx'.\n\n{exc}",
            )
            self.db_writer = None
            if self._last_valid_db_index is not None:
                blocker = QSignalBlocker(self.database_combo_box)
                try:
                    self.database_combo_box.setCurrentIndex(self._last_valid_db_index)
                finally:
                    del blocker
            return
        self._last_valid_db_index = self.database_combo_box.currentIndex()
        self.standards_list_view.addItems(self.db_writer.get_standard_ids())
        # Set the first item as selected
        if self.standards_list_view.count() > 0:
            self.standards_list_view.setCurrentRow(0)

    def setup_combo_box(self) -> None:
        self.database_combo_box.addItems(fetch_db_list())
        # set last used database
        index = self.database_combo_box.findText(
            self.config.settings.database_settings.last_used_database
        )
        if index >= 0:
            self.database_combo_box.setCurrentIndex(index)

    def standards_selection_changed(self, current_row: int) -> None:
        """Triggered when the selection in standards_list_view is changed."""
        if current_row < 0:
            return
        if self.db_writer is None:
            return
        item = self.standards_list_view.item(current_row)
        if not item:
            return
        is_amount = self.db_writer.get_IS_amount(item.text())
        blocker = QSignalBlocker(self.quantity_line_edit)
        try:
            self.quantity_line_edit.setText(f"{is_amount:.4f}")
        finally:
            del blocker

    def quantity_changed(self, text: str) -> None:
        """Triggered when the text in quantity_line_edit changes."""
        current_row = self.standards_list_view.currentRow()
        if current_row >= 0:
            selected_item = self.standards_list_view.item(current_row)
            if selected_item:
                if self.db_writer is None:
                    return
                self.db_writer.set_IS_amount(id=selected_item.text(), new_IS_amount=text)

    def update_data_model(self) -> None:
        """Update the SprayRun data model based on current UI values and refresh labels."""
        self.sprayrun = SprayRun(
            x_left=self.spinbox_x_left.value(),
            x_right=self.spinbox_x_right.value(),
            y_bottom=self.spinbox_y_bottom.value(),
            y_top=self.spinbox_y_top.value(),
            margin=self.spinbox_margin.value(),
            total_used_volume_mL=self.spinbox_total_used_volume.value(),
            syringe_flow_mL_per_min=self.spinbox_syringe_flow.value(),
            drying_time_min=self.spinbox_drying_time.value(),
            drying_cycles=self.spinbox_drying_cycles.value(),
            initial_equilibration_min=self.spinbox_initial_equilibration.value(),
            stock_conc_mg_per_mL=self.spinbox_stock_conc.value(),
            working_dilution_factor=self.spinbox_working_dilution_factor.value(),
            volume_working_stock_uL=self.spinbox_volume_working_stock.value(),
            final_mix_volume_mL=self.spinbox_final_mix_volume.value(),
            molecular_weight_ug_per_umol=self.spinbox_molecular_weight.value(),
        )
        self.label_area.setText(self.label_area_template.format(f"{self.sprayrun.area_mm2:.0f}"))
        self.label_volume.setText(
            self.label_volume_template.format(f"{self.sprayrun.delivered_volume_mL:.3f}")
        )
        self.label_mix_conc.setText(
            self.label_mix_conc_template.format(f"{self.sprayrun.spray_mix_conc:.1f}")
        )
        self.label_surface_conc_result.setText(
            self.label_surface_conc_result_template.format(f"{self.sprayrun.pmol_per_mm2:.3f}")
        )

    def apply_calculations(self) -> None:
        self.quantity_line_edit.setText(f"{self.sprayrun.pmol_per_mm2:.3f}")

    def save_and_close(self) -> None:
        if self.db_writer is None:
            QMessageBox.warning(
                self,
                "No Database Loaded",
                "Cannot save because the selected database could not be opened.",
            )
            return
        self.db_writer.save()
        self.config.settings.sprayer_settings.x_left = self.spinbox_x_left.value()
        self.config.settings.sprayer_settings.x_right = self.spinbox_x_right.value()
        self.config.settings.sprayer_settings.y_bottom = self.spinbox_y_bottom.value()
        self.config.settings.sprayer_settings.y_top = self.spinbox_y_top.value()
        self.config.settings.sprayer_settings.margin = self.spinbox_margin.value()
        self.config.settings.sprayer_settings.total_used_volume_mL = (
            self.spinbox_total_used_volume.value()
        )
        self.config.settings.sprayer_settings.syringe_flow_mL_per_min = (
            self.spinbox_syringe_flow.value()
        )
        self.config.settings.sprayer_settings.drying_time_min = self.spinbox_drying_time.value()
        self.config.settings.sprayer_settings.drying_cycles = self.spinbox_drying_cycles.value()
        self.config.settings.sprayer_settings.initial_equilibration_min = (
            self.spinbox_initial_equilibration.value()
        )
        self.config.settings.sprayer_settings.stock_conc_mg_per_mL = self.spinbox_stock_conc.value()
        self.config.settings.sprayer_settings.working_dilution_factor = (
            self.spinbox_working_dilution_factor.value()
        )
        self.config.settings.sprayer_settings.volume_working_stock_uL = (
            self.spinbox_volume_working_stock.value()
        )
        self.config.settings.sprayer_settings.final_mix_volume_mL = (
            self.spinbox_final_mix_volume.value()
        )
        self.config.settings.sprayer_settings.molecular_weight_ug_per_umol = (
            self.spinbox_molecular_weight.value()
        )

        self.config.save()
        self.close()

    def close_window(self) -> None:
        self.close()
