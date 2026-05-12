import os

from PySide6.QtCore import QThreadPool, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from app.config import Config, config_paths
from app.database import LipidDB
from app.generated.MsiAnndataImportDialog_ui import Ui_Dialog
from app.importers.anndata import get_anndata_matrix_choices, load_database_anndata_collection
from app.msi_data import AnnDataMatrixChoice, SampleCollection
from app.multithreading import Worker


def fetch_db_list() -> list[str]:
    dbs = os.listdir(config_paths["DATABASE_DIR"])
    dbs = list(filter(lambda f: f.endswith(".xlsx"), dbs))
    return [os.path.splitext(s)[0] for s in dbs]


class AnndataImportWindow(QWidget, Ui_Dialog):
    """Window in which AnnData import settings are configured."""

    finished_anndata_loading = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config
        self.threadpool = QThreadPool()
        self.anndata_path: str = ""
        self.database: LipidDB | None = None
        self.samples: SampleCollection
        self.setupUi(self)
        self.database_combo_box.addItems(fetch_db_list())
        self._reset_matrix_choices()

        self.ppm_spinbox.setValue(self.config.settings.processing_settings.ppm)
        self.m2_iso_cor_checkbox.setChecked(
            self.config.settings.processing_settings.db_isotope_correction
        )
        self.na_iso_cor_checkbox.setChecked(
            self.config.settings.processing_settings.na_isotope_correction
        )
        self.imputation_checkbox.setChecked(self.config.settings.processing_settings.imputation)

        index = self.database_combo_box.findText(
            self.config.settings.database_settings.last_used_database
        )
        if index >= 0:
            self.database_combo_box.setCurrentIndex(index)
        self.connect_signals_slots()

    def connect_signals_slots(self) -> None:
        self.import_data_button.clicked.connect(self.process_anndata_file)
        self.open_anndata_button.clicked.connect(self.open_anndata_file)
        self.database_combo_box.currentTextChanged.connect(self._on_database_changed)
        self.ppm_spinbox.valueChanged.connect(self._on_ppm_changed)
        self.na_iso_cor_checkbox.toggled.connect(self._on_na_iso_cor_changed)
        self.m2_iso_cor_checkbox.toggled.connect(self._on_m2_iso_cor_changed)
        self.imputation_checkbox.toggled.connect(self._on_imputation_changed)

    def open_anndata_file(self) -> None:
        selected_path, _ = QFileDialog.getOpenFileName(
            self, "Select AnnData file", filter="AnnData (*.h5ad)"
        )
        if not selected_path:
            return
        self.anndata_path = selected_path
        self.anndata_path_line_edit.setText(selected_path)
        try:
            self._populate_matrix_choices(get_anndata_matrix_choices(selected_path))
        except Exception as exc:
            self.anndata_path = ""
            self.anndata_path_line_edit.clear()
            self._reset_matrix_choices()
            QMessageBox.critical(self, "AnnData import failed", str(exc))

    def process_anndata_file(self) -> None:
        if not self.anndata_path:
            raise ValueError("Please open an AnnData file first.")

        db_name = self.database_combo_box.currentText()
        if not db_name:
            raise ValueError(
                "Please select a database file, the readme provides details on how to create a database."
            )

        matrix_choice = self.matrix_combo_box.currentData()
        if matrix_choice is None:
            raise ValueError("Please select an AnnData matrix to import.")

        self.set_ui_components_status(False)
        db_path = os.path.join(config_paths["DATABASE_DIR"], db_name + ".xlsx")
        worker = Worker(
            load_database_anndata_collection,
            database_path=db_path,
            anndata_path=self.anndata_path,
            matrix_choice=matrix_choice,
            config=self.config,
        )
        worker.signals.progress_file.connect(self.handle_progress_file)
        worker.signals.progress_overall.connect(self.handle_progress_overall)
        worker.signals.result.connect(self.handle_finished)
        worker.signals.error.connect(self.handle_error)
        self.threadpool.start(worker)

    @Slot(int)
    def handle_progress_file(self, file_progress: int) -> None:
        self.progress_bar_file.setValue(file_progress)

    @Slot(int)
    def handle_progress_overall(self, overall_progress: int) -> None:
        self.progress_bar_overall.setValue(overall_progress)

    @Slot(LipidDB, SampleCollection)
    def handle_finished(self, database: LipidDB, samples: SampleCollection) -> None:
        self.samples = samples
        self.database = database
        missing_standards = database.get_standards_missing_amounts()
        if missing_standards:
            QMessageBox.warning(
                self,
                "Database warning",
                "Standard amount values are missing for the following standards:\n"
                f"{', '.join(missing_standards)}\n\n"
                "Please populate 'Standard amount (pmol / mm2)' in the Excel database or use the built-in "
                "standard calculator.",
            )
        skipped_classes = getattr(database, "na_isotope_correction_skipped_classes", [])
        if self.config.settings.processing_settings.na_isotope_correction and skipped_classes:
            QMessageBox.warning(
                self,
                "Database warning",
                "H/Na overlap correction was skipped for the following lipid classes because the "
                "database does not define the required [M+H]+/[M+Na]+ adduct forms for them:\n"
                f"{', '.join(skipped_classes)}\n\n"
                "Processing continued for all other supported classes.",
            )
        self.finished_anndata_loading.emit()
        self.close()

    @Slot(str)
    def handle_error(self, message: str) -> None:
        self.set_ui_components_status(True)
        QMessageBox.critical(self, "AnnData import failed", message)

    def set_ui_components_status(self, active: bool) -> None:
        self.open_anndata_button.setEnabled(active)
        self.anndata_path_line_edit.setEnabled(active)
        self.ppm_spinbox.setEnabled(active)
        self.matrix_combo_box.setEnabled(active)
        self.database_combo_box.setEnabled(active)
        self.import_data_button.setEnabled(active)
        self.m2_iso_cor_checkbox.setEnabled(active)
        self.na_iso_cor_checkbox.setEnabled(active)
        self.imputation_checkbox.setEnabled(active)

    def _reset_matrix_choices(self) -> None:
        self.matrix_combo_box.clear()
        self.matrix_combo_box.addItem("Raw", AnnDataMatrixChoice.raw.value)

    def _populate_matrix_choices(self, choices: list[AnnDataMatrixChoice]) -> None:
        self.matrix_combo_box.clear()
        if AnnDataMatrixChoice.raw in choices:
            self.matrix_combo_box.addItem("Raw", AnnDataMatrixChoice.raw.value)
        if AnnDataMatrixChoice.batch_corrected in choices:
            self.matrix_combo_box.addItem(
                "Batch corrected", AnnDataMatrixChoice.batch_corrected.value
            )

    @Slot(str)
    def _on_database_changed(self, db_name: str):
        self.config.settings.database_settings.last_used_database = db_name
        self.config.save()

    @Slot(float)
    def _on_ppm_changed(self, value: float):
        self.config.settings.processing_settings.ppm = value
        self.config.save()

    @Slot(bool)
    def _on_na_iso_cor_changed(self, is_checked: bool):
        self.config.settings.processing_settings.na_isotope_correction = is_checked
        self.config.save()

    @Slot(bool)
    def _on_m2_iso_cor_changed(self, is_checked: bool):
        self.config.settings.processing_settings.db_isotope_correction = is_checked
        self.config.save()

    @Slot(bool)
    def _on_imputation_changed(self, is_checked: bool):
        self.config.settings.processing_settings.imputation = is_checked
        self.config.save()
