import pytest

from app.utils import format_species_selection_clipboard, parse_species_selection_clipboard


def test_species_selection_clipboard_round_trip() -> None:
    species_ids = ["PC 30:1 [M+H]+", "PC 30:1 [M+K]+", "PC 30:1 (+)"]
    checked_values = [True, False, True]

    text = format_species_selection_clipboard(species_ids, checked_values)
    result = parse_species_selection_clipboard(text, expected_ids=species_ids)

    assert text.splitlines()[0] == "Species\tExport"
    assert result == checked_values


def test_parse_species_selection_clipboard_accepts_excel_style_values() -> None:
    text = "Species\tExport\nA\t1\nB\tno\nC\tx"

    result = parse_species_selection_clipboard(text, expected_ids=["A", "B", "C"])

    assert result == [True, False, True]


def test_parse_species_selection_clipboard_rejects_wrong_row_count() -> None:
    text = "Species\tExport\nA\tTRUE"

    with pytest.raises(ValueError, match="contains 1 rows"):
        parse_species_selection_clipboard(text, expected_ids=["A", "B"])


def test_parse_species_selection_clipboard_rejects_mismatched_ids() -> None:
    text = "Species\tExport\nA\tTRUE\nC\tFALSE"

    with pytest.raises(ValueError, match="Species ID mismatch on row 2"):
        parse_species_selection_clipboard(text, expected_ids=["A", "B"])


def test_parse_species_selection_clipboard_rejects_invalid_bool() -> None:
    text = "Species\tExport\nA\tmaybe"

    with pytest.raises(ValueError, match="Invalid Export value"):
        parse_species_selection_clipboard(text, expected_ids=["A"])
