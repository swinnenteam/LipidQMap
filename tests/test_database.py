import pandas as pd
import pytest
from molmass import Formula

from app.database import DatabaseFactory, IonMode, LipidDB, adduct_formula


@pytest.fixture(name="database")
def fixture_database() -> LipidDB:
    database = DatabaseFactory(
        "tests/database/test_database.xlsx", ion_mode=IonMode.positive
    ).create_database()
    return database


@pytest.fixture(name="neg_database")
def fixture_neg_database() -> LipidDB:
    database = DatabaseFactory(
        "tests/database/test_database.xlsx", ion_mode=IonMode.negative
    ).create_database()
    return database


def test_load_database_positive() -> None:
    database = DatabaseFactory(
        "tests/database/test_database.xlsx", ion_mode=IonMode.positive
    ).create_database()
    assert database.verify_ion_mode(ion_mode=IonMode.positive)


def test_load_database_negative() -> None:
    database = DatabaseFactory(
        "tests/database/test_database.xlsx", ion_mode=IonMode.negative
    ).create_database()
    assert database.verify_ion_mode(ion_mode=IonMode.negative)


def test_load_database_column_missing() -> None:
    with pytest.raises(ValueError):
        DatabaseFactory(
            "tests/database/test_database_column_missing.xlsx", ion_mode=IonMode.negative
        )


def test_load_database_std_undefined() -> None:
    with pytest.raises(ValueError):
        DatabaseFactory(
            "tests/database/test_database_std_undefined.xlsx", ion_mode=IonMode.positive
        ).create_database()


def test_load_database_no_std_amount() -> None:
    with pytest.raises(ValueError):
        DatabaseFactory(
            "tests/database/test_database_no_std_amount.xlsx", ion_mode=IonMode.positive
        ).create_database()


def test_load_database_invalid_isotope_id() -> None:
    with pytest.raises(ValueError):
        DatabaseFactory(
            "tests/database/test_database_invalid_isotope_id.xlsx", ion_mode=IonMode.positive
        ).create_database()


def test_get(database: LipidDB) -> None:
    assert "PC 33:1 d7" == database.get(0).id


def test_get_id(database: LipidDB) -> None:
    assert "PC 33:1 d7 [M+H]+" == database.get_id(1)


def test_get_ids_non_standards(database: LipidDB) -> None:
    species_ids = [s.id_adduct for s in database.get_ids_non_standards()]
    assert "PC 32:1 [M+Na]+" in species_ids
    assert "PC 33:1 d7" not in species_ids
    assert "PC 28:0 " not in species_ids


def test_get_all_species_same_class(database: LipidDB) -> None:
    species = database.get_all_species_same_class("PC 32:1 [M+H]+")
    species_ids = [s.id_adduct for s in species]
    assert species_ids == [
        "PC 33:1 d7 [M+H]+",
        "PC 32:0 [M+H]+",
        "PC 32:1 [M+H]+",
        "PC 34:1 [M+H]+",
        "PC 36:1 [M+H]+",
        "PC 32:2 [M+H]+",
        "PC 34:2 [M+H]+",
        "PC 36:2 [M+H]+",
        "PC 32:4 [M+H]+",
        "PC 34:4 [M+H]+",
        "PC 36:4 [M+H]+",
        "PC 38:4 [M+H]+",
    ]


def test_neutral_species(database: LipidDB) -> None:
    species = database.get_neutral_species()
    assert 13 == len(species)


def test_get_standard(database: LipidDB) -> None:
    species = database.species["PC 32:1 [M+Na]+"]
    assert species.standard is not None
    assert species.standard.id_adduct == "PC 33:1 d7 [M+Na]+"
    assert species.standard.amount == 1.5


def test_get_standard_not_present(neg_database: LipidDB) -> None:
    species = neg_database.species["PE 32:1 [M-H]-"]
    assert species.standard is None


def test_get_M2_isotope_ID(database: LipidDB) -> None:
    species = database.species["PC 32:1 [M+Na]+"]
    assert species.m2_isotope is not None
    assert species.m2_isotope.id_adduct == "PC 32:2 [M+Na]+"


def test_get_M2_isotope_ID_None(database: LipidDB) -> None:
    species = database.species["PC 34:2 [M+Na]+"]
    assert species.m2_isotope is None


def test_get_M2_isotope_percent(database: LipidDB) -> None:
    assert pytest.approx(0.11457, rel=1e-3) == database.species["PC 32:1 [M+Na]+"].m2_rel_abundance


def test_get_M4_isotope_ID(database: LipidDB) -> None:
    species = database.species["PC 32:0 [M+H]+"]
    assert species.m4_isotope is not None
    assert species.m4_isotope.id_adduct == "PC 32:2 [M+H]+"


def test_get_M4_isotope_ID_None(database: LipidDB) -> None:
    species = database.species["PC 34:2 [M+Na]+"]
    assert species.m2_isotope is None


def test_get_M4_isotope_percent(database: LipidDB) -> None:
    assert pytest.approx(0.003186, rel=1e-3) == database.species["PC 32:1 [M+Na]+"].m4_rel_abundance


def test_get_Na_isotope_ID(database: LipidDB) -> None:
    species = database.species["PC 34:4 [M+H]+"]
    assert species.na_isotope is not None
    assert species.na_isotope.id_adduct == "PC 32:1 [M+H]+"


def test_get_Na_isotope_ID_None(database: LipidDB) -> None:
    species = database.species["PC 32:2 [M+H]+"]
    assert species.na_isotope is None


def test_get_hydrogen_sodium_std_pairs(database: LipidDB) -> None:
    assert database.get_hydrogen_sodium_std_pairs() == [("PC 33:1 d7 [M+H]+", "PC 33:1 d7 [M+Na]+")]


def test_get_species_sorted_for_isotope(database: LipidDB) -> None:

    species_ids = [s.id_adduct for s in database.get_species_sorted_for_isotope()]
    assert species_ids == [
        "SM 34:1 [M+H]+",
        "PC 32:4 [M+H]+",
        "PC 32:2 [M+H]+",
        "PC 32:1 [M+H]+",
        "PC 32:0 [M+H]+",
        "PC 33:1 d7 [M+H]+",
        "PC 34:4 [M+H]+",
        "PC 34:2 [M+H]+",
        "PC 34:1 [M+H]+",
        "PC 36:4 [M+H]+",
        "PC 36:2 [M+H]+",
        "PC 36:1 [M+H]+",
        "PC 38:4 [M+H]+",
        "PC 32:4 [M+K]+",
        "PC 32:2 [M+K]+",
        "PC 32:1 [M+K]+",
        "PC 32:0 [M+K]+",
        "PC 33:1 d7 [M+K]+",
        "PC 34:4 [M+K]+",
        "PC 34:2 [M+K]+",
        "PC 34:1 [M+K]+",
        "PC 36:4 [M+K]+",
        "PC 36:2 [M+K]+",
        "PC 36:1 [M+K]+",
        "PC 38:4 [M+K]+",
        "PC 32:4 [M+Na]+",
        "PC 32:2 [M+Na]+",
        "PC 32:1 [M+Na]+",
        "PC 32:0 [M+Na]+",
        "PC 33:1 d7 [M+Na]+",
        "PC 34:4 [M+Na]+",
        "PC 34:2 [M+Na]+",
        "PC 34:1 [M+Na]+",
        "PC 36:4 [M+Na]+",
        "PC 36:2 [M+Na]+",
        "PC 36:1 [M+Na]+",
        "PC 38:4 [M+Na]+",
    ]


def test_get_all_species(database: LipidDB) -> None:
    species_id, species_mz = database.get_all_species()
    assert 37 == len(species_id)
    assert species_id[0] == ("PC 33:1 d7 [M+H]+")
    assert species_mz[0] == pytest.approx(753.613368, rel=1e-3)


def test_get_table(database: LipidDB) -> None:
    table = database.get_table()
    assert type(table) is pd.DataFrame


def test_adduct_mh_plus():
    result = adduct_formula("C6H12O6", "[M+H]+")
    expected = Formula("C6H12O6") + Formula("[H]+")
    assert result.formula == expected.formula


def test_adduct_mh_h2o_plus():
    result = adduct_formula("C6H12O6", "[M+H-H2O]+")
    expected = Formula("C6H12O6") + Formula("[H]+") - Formula("[H2O]")
    assert result.formula == expected.formula


def test_adduct_m_dot_plus():
    result = adduct_formula("C6H12O6", "[M.]+")
    expected = Formula("C6H12O6") + Formula("[]+")
    assert result.formula == expected.formula


def test_adduct_m2h_2plus():
    result = adduct_formula("C6H12O6", "[M+2H]2+")
    expected = Formula("C6H12O6") + Formula("[H2]2+")
    assert result.formula == expected.formula


def test_adduct_m3h_3plus():
    result = adduct_formula("C6H12O6", "[M+3H]3+")
    expected = Formula("C6H12O6") + Formula("[H3]3+")
    assert result.formula == expected.formula


def test_adduct_m4h_4plus():
    result = adduct_formula("C6H12O6", "[M+4H]4+")
    expected = Formula("C6H12O6") + Formula("[H4]4+")
    assert result.formula == expected.formula


def test_adduct_mk_plus():
    result = adduct_formula("C6H12O6", "[M+K]+")
    expected = Formula("C6H12O6") + Formula("[K]+")
    assert result.formula == expected.formula


def test_adduct_m2k_2plus():
    result = adduct_formula("C6H12O6", "[M+2K]2+")
    expected = Formula("C6H12O6") + Formula("[K2]2+")
    assert result.formula == expected.formula


def test_adduct_m2k_h_plus():
    result = adduct_formula("C6H12O6", "[M+2K-H]+")
    expected = Formula("C6H12O6") + Formula("[K2]+") - Formula("[H]")
    assert result.formula == expected.formula


def test_adduct_mna_plus():
    result = adduct_formula("C6H12O6", "[M+Na]+")
    expected = Formula("C6H12O6") + Formula("[Na]+")
    assert result.formula == expected.formula


def test_adduct_m2na_2plus():
    result = adduct_formula("C6H12O6", "[M+2Na]2+")
    expected = Formula("C6H12O6") + Formula("[Na2]2+")
    assert result.formula == expected.formula


def test_adduct_m2na_h_plus():
    result = adduct_formula("C6H12O6", "[M+2Na-H]+")
    expected = Formula("C6H12O6") + Formula("[Na2]+") - Formula("[H]")
    assert result.formula == expected.formula


def test_adduct_mli_plus():
    result = adduct_formula("C6H12O6", "[M+Li]+")
    expected = Formula("C6H12O6") + Formula("[Li]+")
    assert result.formula == expected.formula


def test_adduct_m2li_2plus():
    result = adduct_formula("C6H12O6", "[M+2Li]2+")
    expected = Formula("C6H12O6") + Formula("[Li2]2+")
    assert result.formula == expected.formula


def test_adduct_mnh4_plus():
    result = adduct_formula("C6H12O6", "[M+NH4]+")
    expected = Formula("C6H12O6") + Formula("[NH4]+")
    assert result.formula == expected.formula


def test_adduct_mh_minus():
    result = adduct_formula("C6H12O6", "[M-H]-")
    expected = Formula("C6H12O6") - Formula("[H]+")
    assert result.formula == expected.formula


def test_adduct_m2h_2minus():
    result = adduct_formula("C6H12O6", "[M-2H]2-")
    expected = Formula("C6H12O6") - Formula("[H2]2+")
    assert result.formula == expected.formula


def test_adduct_m3h_3minus():
    result = adduct_formula("C6H12O6", "[M-3H]3-")
    expected = Formula("C6H12O6") - Formula("[H3]3+")
    assert result.formula == expected.formula


def test_adduct_m4h_4minus():
    result = adduct_formula("C6H12O6", "[M-4H]4-")
    expected = Formula("C6H12O6") - Formula("[H4]4+")
    assert result.formula == expected.formula


def test_adduct_mcl_minus():
    result = adduct_formula("C6H12O6", "[M+Cl]-")
    expected = Formula("C6H12O6") + Formula("[Cl]-")
    assert result.formula == expected.formula


def test_adduct_moac_minus():
    result = adduct_formula("C6H12O6", "[M+OAc]-")
    expected = Formula("C6H12O6") + Formula("[CH3OO]-")
    assert result.formula == expected.formula


def test_adduct_mhcoo_minus():
    result = adduct_formula("C6H12O6", "[M+HCOO]-")
    expected = Formula("C6H12O6") + Formula("[HCOO]-")
    assert result.formula == expected.formula


def test_adduct_m2hna_minus():
    result = adduct_formula("C6H12O6", "[M-2H+Na]-")
    expected = Formula("C6H12O6") + Formula("[Na]") - Formula("[H2]+")
    assert result.formula == expected.formula


def test_adduct_m3h2na_minus():
    result = adduct_formula("C6H12O6", "[M-3H+2Na]-")
    expected = Formula("C6H12O6") + Formula("[Na2]") - Formula("[H3]+")
    assert result.formula == expected.formula


def test_adduct_m2hk_minus():
    result = adduct_formula("C6H12O6", "[M-2H+K]-")
    expected = Formula("C6H12O6") + Formula("[K]") - Formula("[H2]+")
    assert result.formula == expected.formula


def test_adduct_m3h2k_minus():
    result = adduct_formula("C6H12O6", "[M-3H+2K]-")
    expected = Formula("C6H12O6") + Formula("[K2]") - Formula("[H3]+")
    assert result.formula == expected.formula


def test_unsupported_adduct():
    with pytest.raises(ValueError) as exc_info:
        adduct_formula("C6H12O6", "[M+Unsupported]+")
    assert str(exc_info.value) == "Unsupported adduct in database: [M+Unsupported]+"
