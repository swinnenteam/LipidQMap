import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QLocale
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QApplication

from app.config import Config
from app.views import calculator_window
from app.views.calculator_window import CalculatorWindow


class FakeDatabaseEditor:
    def __init__(self, _path: str) -> None:
        self.amounts = {"STD": 1.5}
        self.saved = False

    def get_standard_ids(self) -> list[str]:
        return list(self.amounts)

    def get_IS_amount(self, id: str) -> float:
        return self.amounts[id]

    def set_IS_amount(self, id: str, new_IS_amount: float) -> None:
        self.amounts[id] = float(new_IS_amount)

    def save(self) -> None:
        self.saved = True


@pytest.fixture(scope="module")
def qapplication() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("locale_name", "decimal_separator", "alternate_separator"),
    [
        ("en_US", ".", ","),
        ("nl_BE", ",", "."),
        ("fr_BE", ",", "."),
        ("de_DE", ",", "."),
    ],
)
def test_calculator_decimal_locale_round_trip(
    qapplication: QApplication,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    locale_name: str,
    decimal_separator: str,
    alternate_separator: str,
) -> None:
    QLocale.setDefault(QLocale(locale_name))
    monkeypatch.setattr(calculator_window, "fetch_db_list", lambda: ["database"])
    monkeypatch.setattr(calculator_window, "DatabaseEditor", FakeDatabaseEditor)

    config_path = tmp_path / f"config-{locale_name}.toml"
    config = Config(path=str(config_path))
    window = CalculatorWindow(config)
    try:
        assert window.quantity_spinbox.text() == f"1{decimal_separator}5000"
        assert window.numeric_locale.numberOptions() & QLocale.NumberOption.RejectGroupSeparator

        validation_state, _, _ = window.quantity_spinbox.validate(f"3{alternate_separator}981", 0)
        assert validation_state == QValidator.State.Acceptable
        assert window.quantity_spinbox.valueFromText(f"3{alternate_separator}981") == pytest.approx(
            3.981
        )

        grouped_state, _, _ = window.quantity_spinbox.validate("1,234.56", 0)
        assert grouped_state == QValidator.State.Invalid

        window.quantity_spinbox.lineEdit().setText(f"3{alternate_separator}981")
        window.quantity_spinbox.interpretText()
        assert window.quantity_spinbox.value() == pytest.approx(3.981)
        assert window.db_writer is not None
        assert window.db_writer.amounts["STD"] == pytest.approx(3.981)

        calculated_amount = window.sprayrun.pmol_per_mm2
        window.apply_calculations()

        assert window.db_writer is not None
        assert window.db_writer.amounts["STD"] == pytest.approx(round(calculated_amount, 4))
        assert decimal_separator in window.quantity_spinbox.text()
        assert decimal_separator in window.label_surface_conc_result.text()

        window.spinbox_total_used_volume.setValue(0.123)
        window.save_and_close()

        loaded_config = Config(path=str(config_path))
        assert loaded_config.settings.sprayer_settings.total_used_volume_mL == pytest.approx(0.123)
        assert "total_used_volume_mL = 0.123" in config_path.read_text(encoding="utf8")
    finally:
        window.close()
        window.deleteLater()
        qapplication.processEvents()
        QLocale.setDefault(QLocale.system())
