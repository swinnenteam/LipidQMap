import os
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from app import scils_export
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


def test_connection_status_is_reported_before_scils_startup(monkeypatch) -> None:
    class UnavailableSession:
        def __init__(self, **_kwargs) -> None:
            raise RuntimeError("Remote license server is not reachable")

    monkeypatch.setattr(scils_export, "_load_local_session", lambda: UnavailableSession)
    statuses: list[str] = []

    with pytest.raises(ScilsExportError, match="license server"):
        scils_export.export_score_spot_images(
            dataset_path=Path("test.slx"),
            samples=SimpleNamespace(samples={"sample": object()}),
            sample_id="sample",
            species_ids=["lipid"],
            image_type=ImageType.quant,
            status_callback=statuses.append,
        )

    assert statuses == ["Connecting to SCiLS for sample 'sample'..."]


def test_aggregated_write_reports_each_completed_feature(monkeypatch) -> None:
    class FeatureTable:
        def create_empty_feature_list(self, *_args, **_kwargs) -> int:
            return 42

        def write_external_feature(self, *_args, **_kwargs) -> None:
            return None

    session = SimpleNamespace(
        dataset_proxy=SimpleNamespace(feature_table=FeatureTable()),
    )
    monkeypatch.setattr(
        scils_export, "_load_local_session", lambda: lambda **_kwargs: session
    )
    monkeypatch.setattr(scils_export, "_shutdown_session_async", lambda _session: None)
    progress: list[tuple[int, int]] = []

    scils_export.write_aggregated_features(
        dataset_path=Path("test.slx"),
        feature_list_label="features",
        image_type=ImageType.quant,
        aggregate={
            "lipid 1": [([1], [10.0])],
            "lipid 2": [([2], [20.0])],
        },
        progress_callback=lambda current, total: progress.append((current, total)),
    )

    assert progress == [(1, 2), (2, 2)]


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
        _kwargs["status_callback"]("Preparing sample...")
        return ScilsExportReport(
            exported_features=1,
            skipped_species=[],
            dataset_path=dataset_path,
            feature_list_id=-1,
        )

    def fail_aggregated_write(**_kwargs) -> ScilsExportReport:
        _kwargs["status_callback"]("Connecting to SCiLS...")
        raise ScilsExportError("All licenses are currently used by other instances")

    messages: list[str] = []
    monkeypatch.setattr(scils_export_window, "export_score_spot_images", export_sample)
    monkeypatch.setattr(
        scils_export_window, "write_aggregated_features", fail_aggregated_write
    )
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
    assert window.label_scils_status.text() == (
        "Export failed. Resolve the problem and try again."
    )
    assert len(messages) == 1
    assert "All licenses are currently used" in messages[0]
    assert "can be retried" in messages[0]
    window.close()
    app.processEvents()


def test_progress_includes_final_feature_writes(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    window = ScilsExportWindow()
    window.samples = SimpleNamespace(
        samples={"sample-1": object(), "sample-2": object()}
    )
    window.database = None
    window.species_ids = ["lipid-1", "lipid-2", "lipid-3"]
    window.all_species_ids = list(window.species_ids)
    window.quant_checkbox.setChecked(True)
    window.iso_checkbox.setChecked(False)
    window.raw_checkbox.setChecked(False)
    dataset_path = Path("test.slx")
    monkeypatch.setattr(window, "_select_dataset", lambda: dataset_path)

    def export_sample(**kwargs) -> ScilsExportReport:
        kwargs["progress_callback"](3, 3)
        for species_id in window.species_ids:
            kwargs["feature_aggregate"].setdefault(species_id, []).append(([1], [1.0]))
        return ScilsExportReport(3, [], dataset_path, -1)

    write_values: list[int] = []

    def write_features(**kwargs) -> ScilsExportReport:
        for current in range(1, 4):
            kwargs["progress_callback"](current, 3)
            write_values.append(window.scils_progressbar.value())
        return ScilsExportReport(3, [], dataset_path, 42)

    monkeypatch.setattr(scils_export_window, "export_score_spot_images", export_sample)
    monkeypatch.setattr(
        scils_export_window, "write_aggregated_features", write_features
    )
    monkeypatch.setattr(window, "_show_summary", lambda *_args: None)

    window.export()

    assert write_values == [7, 8, 9]
    window.close()
    app.processEvents()
