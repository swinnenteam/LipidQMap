from typing import cast

from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QDoubleSpinBox


class LocaleDoubleSpinBox(QDoubleSpinBox):
    """Decimal spin box that accepts either decimal mark without accepting grouping."""

    def _normalize_decimal_mark(self, text: str) -> str | None:
        if text.count(".") > 1 or text.count(",") > 1:
            return None
        if "." in text and "," in text:
            return None

        group_separator = self.locale().groupSeparator()
        if group_separator not in {".", ","} and group_separator in text:
            return None

        decimal_point = self.locale().decimalPoint()
        alternate_point = "," if decimal_point == "." else "."
        return text.replace(alternate_point, decimal_point)

    def validate(self, text: str, position: int) -> tuple[QValidator.State, str, int]:
        normalized = self._normalize_decimal_mark(text)
        if normalized is None:
            return QValidator.State.Invalid, text, position
        result = cast(tuple[QValidator.State, str, int], super().validate(normalized, position))
        return result[0], text, position

    def valueFromText(self, text: str) -> float:
        normalized = self._normalize_decimal_mark(text)
        if normalized is None:
            return self.value()
        return super().valueFromText(normalized)
