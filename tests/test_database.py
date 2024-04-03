import pandas as pd
import pytest

from app.database import IonMode, LipidDB


@pytest.fixture(name="database")
def fixture_database() -> LipidDB:
    return LipidDB("tests/database/test_database.xlsx", ion_mode=IonMode.positive)


def test_load_database_positive() -> None:
    database = LipidDB("tests/database/test_database.xlsx", ion_mode=IonMode.positive)
    assert database.verify_ion_mode(ion_mode=IonMode.positive)


def test_load_database_negative() -> None:
    database = LipidDB("tests/database/test_database.xlsx", ion_mode=IonMode.negative)
    assert database.verify_ion_mode(ion_mode=IonMode.negative)


def test_get_id(database: LipidDB) -> None:
    assert database.get_id(1) == "PC 28:0 [M+K]+"


def test_get_ids_non_standards(database: LipidDB) -> None:
    species_ids = database.get_ids_non_standards()
    assert "PC 28:0 [M+K]+" in species_ids
    assert not "PC 33:1 d7" in species_ids


def test_get_standard(database: LipidDB) -> None:
    assert ("PC 33:1 d7 [M+K]+", 1.5) == database.get_standard("PC 28:0 [M+K]+")


def test_get_M2_isotope_ID(database: LipidDB) -> None:
    assert "PC 32:1 [M+K]+" == database.get_M2_isotope_ID("PC 32:0 [M+K]+")


def test_get_M2_isotope_percent(database: LipidDB) -> None:
    assert pytest.approx(0.1869062, rel=1e-3) == database.get_M2_isotope_percent("PC 32:0 [M+K]+")


def test_get_ids_sorted_for_isotope(database: LipidDB) -> None:
    assert [
        "PC 28:0 [M+K]+",
        "PC 30:0 [M+K]+",
        "PC 32:2 [M+K]+",
        "PC 32:1 [M+K]+",
        "PC 32:0 [M+K]+",
        "PC 33:1 d7 [M+K]+",
        "PC 34:2 [M+K]+",
        "PC 34:1 [M+K]+",
        "PC 36:2 [M+K]+",
        "PC 36:1 [M+K]+",
        "PC 32:1 [M+Na]+",
        "PC 32:0 [M+Na]+",
        "PC 34:1 [M+Na]+",
        "PC 33:1 d7 [M+Na]+",
        "PC 36:1 [M+Na]+",
    ] == database.get_ids_sorted_for_isotope()


def test_get_all_species(database: LipidDB) -> None:
    species = database.get_all_species()
    assert 15 == len(species)
    assert species[0] == ("PC 33:1 d7 [M+K]+", pytest.approx(791.56925, rel=1e-3))


def test_get_table(database: LipidDB) -> None:
    table = database.get_table()
    assert type(table) is pd.DataFrame
