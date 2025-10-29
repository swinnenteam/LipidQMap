import os

from PySide6.QtCore import Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QMessageBox,
    QWidget,
)

from app.config import Config, config_paths
from app.database import IonMode, LipidDB
from app.dataprocess import SampleCollection, SampleFiles, detect_imzml_ion_mode, load_database_image_collection
from app.generated.MsiImportDialog_ui import Ui_Dialog
from app.multithreading import Worker


def fetch_db_list() -> list[str]:
    dbs = os.listdir(config_paths["DATABASE_DIR"])
    dbs = list(filter(lambda f: f.endswith(".xlsx"), dbs))
    return [os.path.splitext(s)[0] for s in dbs]


class ImzmlImportWindow(QWidget, Ui_Dialog):
    """
    Window in which imzML import setting are configured.
    """

    finished_imzml_loading = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.threadpool = QThreadPool()
        self.sample_groups: list[SampleFiles] = []
        self.database: LipidDB | None = None
        self.samples: SampleCollection
        self.setupUi(self)
        self._init_imzml_table()
        self.database_combo_box.addItems(fetch_db_list())

        self.ppm_spinbox.setValue(self.config.settings.processing_settings.ppm)
        self.bin_size_spinbox.setValue(self.config.settings.processing_settings.bin_size)
        self.m2_iso_cor_checkbox.setChecked(
            self.config.settings.processing_settings.db_isotope_correction
        )
        self.na_iso_cor_checkbox.setChecked(
            self.config.settings.processing_settings.na_isotope_correction
        )
        self.cal_checkbox.setChecked(self.config.settings.processing_settings.online_calibration)
        self.cal_ppm_spinbox.setValue(self.config.settings.processing_settings.calibration_ppm)
        self.cal_int_spinbox.setValue(
            self.config.settings.processing_settings.calibration_min_intensity
        )
        self.calibrant_pos_spinbox.setValue(self.config.settings.processing_settings.pos_calibrant)
        self.calibrant_neg_spinbox.setValue(self.config.settings.processing_settings.neg_calibrant)
        self.imputation_checkbox.setChecked(self.config.settings.processing_settings.imputation)
        # set last used database
        index = self.database_combo_box.findText(
            self.config.settings.database_settings.last_used_database
        )
        if index >= 0:
            self.database_combo_box.setCurrentIndex(index)
        self.connect_signals_slots()
        self.toggle_cal_checked_value(self.cal_checkbox.isChecked())

    def connect_signals_slots(self) -> None:
        """
        Connect signals from UI widgets to their corresponding slots.
        """
        self.import_data_button.clicked.connect(self.process_imzml_files)
        self.open_imzml_button.clicked.connect(self.open_imzml_files)

        # UI state and interactivity
        self.cal_checkbox.toggled.connect(self.toggle_cal_checked_value)

        # Connect settings changes to their specific handler slots
        self.database_combo_box.currentTextChanged.connect(self._on_database_changed)
        self.ppm_spinbox.valueChanged.connect(self._on_ppm_changed)
        self.bin_size_spinbox.valueChanged.connect(self._on_bin_size_changed)
        self.calibrant_pos_spinbox.valueChanged.connect(self._on_calibrant_pos_changed)
        self.calibrant_neg_spinbox.valueChanged.connect(self._on_calibrant_neg_changed)
        self.cal_ppm_spinbox.valueChanged.connect(self._on_cal_ppm_changed)
        self.cal_int_spinbox.valueChanged.connect(self._on_cal_int_changed)
        self.na_iso_cor_checkbox.toggled.connect(self._on_na_iso_cor_changed)
        self.m2_iso_cor_checkbox.toggled.connect(self._on_m2_iso_cor_changed)
        self.cal_checkbox.toggled.connect(self._on_online_cal_changed)
        self.imputation_checkbox.toggled.connect(self._on_imputation_changed)

    def process_imzml_files(self) -> None:
        if not self.sample_groups:
            raise ValueError("Please open an imzML file first.")

        self.set_ui_components_status(False)

        db_name = self.database_combo_box.currentText()
        db_path = os.path.join(config_paths["DATABASE_DIR"], db_name + ".xlsx")
        if not db_name:
            self.set_ui_components_status(True)
            raise ValueError(
                "Please select a database file, the readme provides details on how to create a database."
            )
        worker = Worker(
            load_database_image_collection,
            database_path=db_path,
            imzml_paths=self.sample_groups,
            config=self.config,
        )
        worker.signals.progress_file.connect(self.handle_progress_file)
        worker.signals.progress_overall.connect(self.handle_progress_overall)
        worker.signals.result.connect(self.handle_finished)
        self.threadpool.start(worker)

    @Slot()
    def handle_progress_file(self, file_progress: int) -> None:
        """Update progressbar"""
        self.progress_bar_file.setValue(file_progress)

    @Slot()
    def handle_progress_overall(self, overall_progress: int) -> None:
        """Update progressbar"""
        self.progress_bar_overall.setValue(overall_progress)

    @Slot(LipidDB, SampleCollection)
    def handle_finished(self, database: LipidDB, samples: SampleCollection) -> None:
        """Emit results to main window"""
        self.samples = samples
        self.database = database
        self.finished_imzml_loading.emit()
        self.close()

    def open_imzml_files(self) -> None:
        """Open imzML files."""
        self._clear_imzml_table()
        self.sample_groups = []
        selected_paths, __ = QFileDialog.getOpenFileNames(
            self, "Select imzML file(s)", filter=";imzML(*.imzML)"
        )
        if not selected_paths:
            return
        groups_by_key: dict[str, list[SampleFiles]] = {}
        try:
            for path in selected_paths:
                filename = os.path.basename(path)
                ion_mode = detect_imzml_ion_mode(path)
                key = SampleFiles.normalized_key(filename)
                candidate_groups = groups_by_key.setdefault(key, [])
                group = self._find_or_create_group(
                    candidate_groups, ion_mode, filename
                )
                group.assign(ion_mode, path, filename)
                if group not in self.sample_groups:
                    self.sample_groups.append(group)
        except ValueError as exc:
            QMessageBox.warning(self, "Ion mode detection failed", str(exc))
            self.sample_groups = []
            self._clear_imzml_table()
            return

        for index, group in enumerate(self.sample_groups, start=1):
            self._add_imzml_row(index, group.pos_filename, group.neg_filename)

    def _find_or_create_group(
        self,
        candidates: list[SampleFiles],
        ion_mode: IonMode,
        filename: str,
    ) -> SampleFiles:
        for group in candidates:
            if group.can_accept(ion_mode):
                return group
        base_label = SampleFiles.derive_label(filename)
        existing_labels = {candidate.label for candidate in candidates}
        existing_labels.update(group.label for group in self.sample_groups)
        label = base_label
        suffix = 2
        while label in existing_labels:
            label = f"{base_label}_{suffix}"
            suffix += 1
        group = SampleFiles(label=label)
        candidates.append(group)
        return group

    def toggle_cal_checked_value(self, is_checked: bool):
        """Enables or disables calibration-related widgets."""
        self.calibrant_pos_spinbox.setEnabled(is_checked)
        self.calibrant_neg_spinbox.setEnabled(is_checked)
        self.cal_ppm_spinbox.setEnabled(is_checked)
        self.cal_int_spinbox.setEnabled(is_checked)

    @Slot(str)
    def _on_database_changed(self, db_name: str):
        """Saves the last used database name."""
        self.config.settings.database_settings.last_used_database = db_name
        self.config.save()

    @Slot(float)
    def _on_ppm_changed(self, value: float):
        """Saves the PPM tolerance."""
        self.config.settings.processing_settings.ppm = value
        self.config.save()

    @Slot(float)
    def _on_bin_size_changed(self, value: float):
        """Saves the bin size."""
        self.config.settings.processing_settings.bin_size = value
        self.config.save()

    @Slot(float)
    def _on_calibrant_pos_changed(self, value: float):
        """Persist the positive-ion calibrant m/z."""
        self.config.settings.processing_settings.pos_calibrant = value
        self.config.save()

    @Slot(float)
    def _on_calibrant_neg_changed(self, value: float):
        """Persist the negative-ion calibrant m/z."""
        self.config.settings.processing_settings.neg_calibrant = value
        self.config.save()

    @Slot(float)
    def _on_cal_ppm_changed(self, value: float):
        """Saves the calibration PPM."""
        self.config.settings.processing_settings.calibration_ppm = value
        self.config.save()

    @Slot(int)
    def _on_cal_int_changed(self, value: int):
        """Saves the calibration minimum intensity."""
        self.config.settings.processing_settings.calibration_min_intensity = value
        self.config.save()

    @Slot(bool)
    def _on_na_iso_cor_changed(self, is_checked: bool):
        """Saves the Na isotope correction setting."""
        self.config.settings.processing_settings.na_isotope_correction = is_checked
        self.config.save()

    @Slot(bool)
    def _on_m2_iso_cor_changed(self, is_checked: bool):
        """Saves the DB isotope correction setting."""
        self.config.settings.processing_settings.db_isotope_correction = is_checked
        self.config.save()

    @Slot(bool)
    def _on_online_cal_changed(self, is_checked: bool):
        """Saves the online calibration setting."""
        self.config.settings.processing_settings.online_calibration = is_checked
        self.config.save()

    @Slot(bool)
    def _on_imputation_changed(self, is_checked: bool):
        """Saves the imputation setting."""
        self.config.settings.processing_settings.imputation = is_checked
        self.config.save()

    def set_ui_components_status(self, active: bool) -> None:
        self.open_imzml_button.setEnabled(active)
        self.imzml_list_view.setEnabled(active)
        self.ppm_spinbox.setEnabled(active)
        self.bin_size_spinbox.setEnabled(active)
        self.database_combo_box.setEnabled(active)
        self.import_data_button.setEnabled(active)
        self.m2_iso_cor_checkbox.setEnabled(active)
        self.na_iso_cor_checkbox.setEnabled(active)
        self.cal_checkbox.setEnabled(active)
        self.cal_group_box.setEnabled(active)
        self.imputation_checkbox.setEnabled(active)

    def _init_imzml_table(self) -> None:
        """Configure the imzML table for positive/negative mode display."""
        self.imzml_model = QStandardItemModel(0, 3, self.imzml_list_view)
        self.imzml_model.setHorizontalHeaderLabels(["#", "Pos mode", "Neg mode"])
        self.imzml_list_view.setModel(self.imzml_model)
        self.imzml_list_view.verticalHeader().setVisible(False)
        header: QHeaderView = self.imzml_list_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.imzml_list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.imzml_list_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.imzml_list_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def _clear_imzml_table(self) -> None:
        """Remove all rows from the imzML table."""
        if hasattr(self, "imzml_model"):
            self.imzml_model.removeRows(0, self.imzml_model.rowCount())

    def _add_imzml_row(
        self,
        index: int,
        pos_filename: str | None,
        neg_filename: str | None,
    ) -> None:
        """Append a single imzML entry to the table."""
        pos_text = pos_filename or ""
        neg_text = neg_filename or ""
        items = [
            QStandardItem(str(index)),
            QStandardItem(pos_text),
            QStandardItem(neg_text),
        ]
        for item in items:
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        items[0].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.imzml_model.appendRow(items)
