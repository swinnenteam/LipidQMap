import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from app.msi_data import ImageType
from app.scils_export import ScilsExportError, ScilsExportReport
from app.views import scils_export_window
from app.views.scils_export_window import (
    AdductSelection,
    ScilsExportWindow,
    filter_species_by_adduct_selection,
)


def _is_summed_stub(species_id: str) -> bool:
    return species_id.endswith(" (+)") or species_id.endswith(" (-)")


def test_filter_species_includes_all_for_combined_option() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)"]

    filtered = filter_species_by_adduct_selection(
        species,
        AdductSelection.adducts_and_summed,
        _is_summed_stub,
    )

    assert filtered == species


def test_filter_species_only_adducts_excludes_summed() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)", "lipid2 [M-H]-"]

    filtered = filter_species_by_adduct_selection(
        species,
        AdductSelection.adducts_only,
        _is_summed_stub,
    )

    assert filtered == ["lipid1 [M+H]+", "lipid2 [M-H]-"]


def test_filter_species_only_summed_includes_neutral_only() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)", "lipid2 [M-H]-"]

    filtered = filter_species_by_adduct_selection(
        species,
        AdductSelection.summed_only,
        _is_summed_stub,
    )

    assert filtered == ["lipid1 (+)", "lipid2 (-)"]


def test_export_reenables_dialog_after_aggregated_write_failure(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    window = ScilsExportWindow()
    window.samples = SimpleNamespace(samples={"sample": object()})
    window.database = None
    window.species_ids = ["lipid"]
    window.all_species_ids = ["lipid"]
    window.quant_checkbox.setChecked(True)
    window.iso_checkbox.setChecked(False)
    window.raw_checkbox.setChecked(False)
    window.selected_only_checkbox.setChecked(True)
    dataset_path = Path("test.slx")
    monkeypatch.setattr(window, "_select_dataset", lambda: dataset_path)

    def export_sample(**_kwargs) -> ScilsExportReport:
        return ScilsExportReport(
            exported_features=1,
            skipped_species=[],
            dataset_path=dataset_path,
            feature_list_id=-1,
        )

    def fail_aggregated_write(**_kwargs) -> ScilsExportReport:
        raise ScilsExportError("All licenses are currently used by other instances")

    messages: list[str] = []
    monkeypatch.setattr(scils_export_window, "export_score_spot_images", export_sample)
    monkeypatch.setattr(scils_export_window, "write_aggregated_features", fail_aggregated_write)
    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(message),
    )

    window.export()

    assert window.button_export.isEnabled()
    assert window.button_cancel.isEnabled()
    assert window.button_choose_file.isEnabled()
    assert window.quant_checkbox.isEnabled()
    assert window.lineEdit.isEnabled()
    assert window.scils_progressbar.value() == 0
    assert len(messages) == 1
    assert "All licenses are currently used" in messages[0]
    assert "can be retried" in messages[0]
    window.close()
    app.processEvents()
