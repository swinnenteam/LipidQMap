import os

from PySide6.QtCore import Signal
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QWidget

from app.config import Config, config_paths
from app.database import DatabaseEditor
from app.generated.MsiStandardCalculatorDialog_ui import Ui_Dialog
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
        self.db_writer: DatabaseEditor
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

    def database_selection_changed(self) -> None:
        self.standards_list_view.clear()
        db_name = self.database_combo_box.currentText()
        db_path = os.path.join(config_paths["DATABASE_DIR"], db_name + ".xlsx")
        self.db_writer = DatabaseEditor(db_path)
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
        if current_row >= 0:
            selected_item = self.standards_list_view.item(current_row)
            if selected_item:
                is_amount = self.db_writer.get_IS_amount(selected_item.text())
                self.quantity_line_edit.setText(f"{is_amount:.4f}")

    def quantity_changed(self, text: str) -> None:
        """Triggered when the text in quantity_line_edit changes."""
        current_row = self.standards_list_view.currentRow()
        if current_row >= 0:
            selected_item = self.standards_list_view.item(current_row)
            if selected_item:
                self.db_writer.set_IS_amount(id=selected_item.text(), new_IS_amount=text)

    def save_and_close(self) -> None:
        self.db_writer.save()
        self.close()

    def close_window(self) -> None:
        self.close()
