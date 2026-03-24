from __future__ import annotations

import re
from enum import Enum
from functools import cached_property
from typing import Any

import pandas as pd
from molmass import Formula
from pydantic import BaseModel, ConfigDict


class IonMode(str, Enum):
    """
    Enum for specifying ion mode of a lipid species.
    """

    positive = "+"
    negative = "-"
    summed = ""


def id_adduct(id: str, adduct: str) -> str:
    """
    Returns the identifier concatenated with the adduct.
    Args:
        id (str): The identifier.
        adduct (str): The adduct.
    Returns:
        str: The identifier concatenated with the adduct.
    """
    if adduct == "":
        return id
    return id + " " + adduct


class LipidSpecies(BaseModel):
    """
    Pydantic data-oriented class to represent a lipid species
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str
    mz: float
    lipid_class: str
    adduct: str
    neutral_formula: Formula
    formula: Formula
    m2_isotope: LipidSpecies | None
    m2_rel_abundance: float
    m4_isotope: LipidSpecies | None
    m4_rel_abundance: float
    na_isotope: LipidSpecies | None
    standard: LipidStandard | None

    @cached_property
    def id_adduct(self) -> str:
        """Returns the identifier concatenated with the adduct."""
        return id_adduct(self.id, self.adduct)

    @cached_property
    def class_adduct(self) -> str:
        """Returns the lipid class concatenated with the adduct."""
        return id_adduct(self.lipid_class, self.adduct)

    @cached_property
    def is_standard(self) -> bool:
        """Checks if the current instance is a standard lipid species."""
        return self.__class__ is LipidStandard

    @cached_property
    def ion_mode(self) -> IonMode:
        """Determines the ion mode based on the adduct."""
        if self.adduct.endswith("+"):
            return IonMode.positive
        elif self.adduct.endswith("-"):
            return IonMode.negative
        else:
            return IonMode.summed

    def __repr__(self):
        return self.id_adduct

    def __str__(self) -> str:
        return self.id_adduct

    def __lt__(self, other) -> bool:
        return (self.adduct, self.mz) < (other.adduct, other.mz)

    def __eq__(self, other) -> bool:
        return self.id == other.id and self.adduct == other.adduct

    def __hash__(self):
        return hash((self.id, self.adduct))


class LipidStandard(LipidSpecies):
    """
    Subclass of LipidSpecies to represent a standard.
    """

    amount: float


class LipidDB:
    """
    Class that manages Lipid species and standards.
    """

    def __init__(self, species: dict[str, LipidSpecies]):
        self.species = species
        self.index: list[str] = list(species.keys())
        self.na_isotope_correction_skipped_classes: list[str] = []

    def get(self, index: int) -> LipidSpecies:
        """
        Returns the LipidSpecies at the requested index
        """
        return self.species[self.index[index]]

    def get_id(self, index: int) -> str:
        """
        Returns the Lipid_id at the requested index
        """
        return self.species[self.index[index]].id_adduct

    def get_all_species_same_class(self, id: str) -> list[LipidSpecies]:
        """
        Get a list of all the species belonging to the same class+adduct
        as species with given id
        """
        current_specie = self.species[id]
        if current_specie.adduct in {"(+)", "(-)"}:
            target_mode = IonMode.positive if current_specie.adduct == "(+)" else IonMode.negative
            related: list[LipidSpecies] = []
            for specie in self.species.values():
                if specie.lipid_class != current_specie.lipid_class:
                    continue
                if specie.adduct in {"(+)", "(-)"}:
                    if specie.adduct == current_specie.adduct:
                        related.append(specie)
                    continue
                if specie.ion_mode == target_mode:
                    related.append(specie)
            return related
        return [s for s in self.species.values() if current_specie.class_adduct == s.class_adduct]

    def get_ids_non_standards(self) -> list[LipidSpecies]:
        """
        Get a list of IDs for non-standard species.
        Returns:
            list[LipidSpecies]: A list of non-standard species IDs.
        """
        return [
            s for s in self.species.values() if (not s.is_standard) and s.ion_mode != IonMode.summed
        ]

    def get_standards_missing_amounts(self) -> list[str]:
        """
        Get standard IDs that are missing a standard amount.
        """
        missing_ids = {
            specie.id
            for specie in self.species.values()
            if specie.is_standard and pd.isna(specie.amount)
        }
        return sorted(missing_ids)

    def _species_order_neutral_first(self) -> list[LipidSpecies]:
        """
        Return species sorted so that entries are grouped by base ID with positive-mode
        neutral summaries and adducts preceding negative-mode entries.
        """

        grouped: dict[str, dict[str, list[LipidSpecies] | LipidSpecies | None]] = {}
        for specie in self.species.values():
            base_id = specie.id
            if base_id not in grouped:
                grouped[base_id] = {
                    "neutral_pos": None,
                    "neutral_neg": None,
                    "neutral_other": [],
                    "positive": [],
                    "negative": [],
                    "other": [],
                }
            bucket = grouped[base_id]
            if specie.adduct == "(+)":
                bucket["neutral_pos"] = specie
            elif specie.adduct == "(-)":
                bucket["neutral_neg"] = specie
            else:
                match specie.ion_mode:
                    case IonMode.positive:
                        bucket["positive"].append(specie)
                    case IonMode.negative:
                        bucket["negative"].append(specie)
                    case IonMode.summed:
                        bucket["neutral_other"].append(specie)
                    case _:
                        bucket["other"].append(specie)

        ordered: list[LipidSpecies] = []
        seen_ids: set[str] = set()
        for specie in self.species.values():
            base_id = specie.id
            if base_id in seen_ids:
                continue
            seen_ids.add(base_id)
            bucket = grouped[base_id]
            if bucket["neutral_pos"] is not None:
                ordered.append(bucket["neutral_pos"])  # type: ignore[arg-type]
            if bucket["positive"]:
                ordered.extend(sorted(bucket["positive"], key=lambda s: (s.adduct, s.mz)))
            if bucket["neutral_neg"] is not None:
                ordered.append(bucket["neutral_neg"])  # type: ignore[arg-type]
            if bucket["negative"]:
                ordered.extend(sorted(bucket["negative"], key=lambda s: (s.adduct, s.mz)))
            if bucket["neutral_other"]:
                ordered.extend(sorted(bucket["neutral_other"], key=lambda s: (s.adduct, s.mz)))
            if bucket["other"]:
                ordered.extend(sorted(bucket["other"], key=lambda s: (s.adduct, s.mz)))

        return ordered

    def species_ids_neutral_first(self) -> list[str]:
        """Return species IDs ordered for display (neutral form followed by all adducts)."""
        return [specie.id_adduct for specie in self._species_order_neutral_first()]

    def get_species_sorted_for_isotope(self) -> list[LipidSpecies]:
        """
        Get a list of species IDs sorted by lowest mz first.
        Returns:
            list[LipidSpecies]: A list of species IDs sorted by Class_Adduct and m/z.
        """
        species = [s for s in self.species.values() if s.ion_mode != IonMode.summed]
        species.sort()
        return species

    def get_hydrogen_sodium_std_pairs(self) -> list[tuple[str, str]]:
        """
        Get all [M+H]+ and [M+Na]+ standard pairs.
        Returns:
            list[tuple[str, str]]: A list of tuples containing pairs of [M+H]+ and [M+Na]+ standard IDs.

        """

        standard_pairs = []
        # get all [M+H]+ standards
        h_standards = [
            specie
            for specie in self.species.values()
            if specie.adduct == "[M+H]+" and specie.is_standard
        ]
        # check if corresponding [M+Na]+ standard is present
        for h_standard in h_standards:
            if h_standard.id + " [M+Na]+" in self.index:
                standard_pairs.append((h_standard.id_adduct, h_standard.id + " [M+Na]+"))
        return standard_pairs

    def get_neutral_species(self) -> list[LipidSpecies]:
        """
        Returns a list of neutral LipidSpecies
        """
        return [s for s in self.species.values() if s.ion_mode == IonMode.summed]

    def get_adduct_species_for_neutral(self, species: LipidSpecies) -> list[LipidSpecies]:
        """
        Given a species, returns the list of all adduct forms of this species
        """
        mode_filter: IonMode | None = None
        if species.adduct == "(+)":
            mode_filter = IonMode.positive
        elif species.adduct == "(-)":
            mode_filter = IonMode.negative

        adducts: list[LipidSpecies] = []
        for candidate in self.species.values():
            if candidate.id != species.id:
                continue
            if candidate.adduct == "":
                continue
            if candidate.adduct in {"(+)", "(-)"}:
                continue
            if mode_filter is None or candidate.ion_mode == mode_filter:
                adducts.append(candidate)
        return adducts

    def get_neutral_from_adduct(self, adduct_id: str) -> LipidSpecies | None:
        """
        Given an adduct species ID, return the corresponding neutral LipidSpecies.
        """
        specie = self.species.get(adduct_id)
        if specie is None or specie.adduct in {"", "(+)", "(-)"}:
            return None

        for candidate in self.species.values():
            if candidate.id != specie.id:
                continue
            if candidate.ion_mode == IonMode.summed or candidate.adduct in {"", "(+)", "(-)"}:
                return candidate
        return None

    def get_all_species(self, neutral=False) -> tuple[list[str], list[float]]:
        """
        Get all species IDs and their m/z values.
        Returns:
            tuple[list[str], list[float]]: A tuple containing a list of species IDs and a list of their m/z values.
        """
        if neutral:
            species_list = [(specie.id_adduct, specie.mz) for specie in self.species.values()]
        else:
            species_list = [
                (specie.id_adduct, specie.mz)
                for specie in self.species.values()
                if specie.ion_mode != IonMode.summed
            ]
        ids, mzs = zip(*species_list)
        return list(ids), list(mzs)

    def get_table(self) -> pd.DataFrame:
        """
        Get a DataFrame of the LipidDB for representation in the gui.
        Returns:
            pd.DataFrame: A DataFrame containing species IDs and their m/z values, marked for export.
        """

        ordered_species = self._species_order_neutral_first()
        species_ids = [specie.id_adduct for specie in ordered_species]
        self.index = species_ids
        d = {
            "Species": species_ids,
            "m/z": [specie.mz for specie in ordered_species],
            "Export": True,
        }
        df = pd.DataFrame(data=d, index=species_ids)
        return df

    def verify_ion_mode(self, ion_mode: IonMode) -> bool:
        """
        Verify that the database contains only the specified ion mode.
        Args:
            ion_mode (IonMode): The ion mode to verify.
        Returns:
            bool: True if the database contains only the specified ion mode, False otherwise.
        """
        return all(
            (specie.ion_mode == ion_mode or specie.ion_mode == IonMode.summed)
            for specie in self.species.values()
        )


def adduct_formula(formula: str, adduct: str) -> Formula:
    """
    Generate an adduct formula based on the given molecular formula and adduct type.
    Args:
        formula (str): The molecular formula of the compound.
        adduct (str): The type of adduct to add to the formula.
    Returns:
        Formula: The modified formula with the specified adduct.
    """

    match adduct:
        case "[M+H]+":
            return Formula(formula) + Formula("[H]+")
        case "[M+H-H2O]+":
            return Formula(formula) + Formula("[H]+") - Formula("[H2O]")
        case "[M.]+":
            return Formula(formula) + Formula("[]+")
        case "[M+2H]2+":
            return Formula(formula) + Formula("[H2]2+")
        case "[M+3H]3+":
            return Formula(formula) + Formula("[H3]3+")
        case "[M+4H]4+":
            return Formula(formula) + Formula("[H4]4+")
        case "[M+K]+":
            return Formula(formula) + Formula("[K]+")
        case "[M+2K]2+":
            return Formula(formula) + Formula("[K2]2+")
        case "[M+2K-H]+":
            return Formula(formula) + Formula("[K2]+") - Formula("[H]")
        case "[M+Na]+":
            return Formula(formula) + Formula("[Na]+")
        case "[M+2Na]2+":
            return Formula(formula) + Formula("[Na2]2+")
        case "[M+2Na-H]+":
            return Formula(formula) + Formula("[Na2]+") - Formula("[H]")
        case "[M+Li]+":
            return Formula(formula) + Formula("[Li]+")
        case "[M+2Li]2+":
            return Formula(formula) + Formula("[Li2]2+")
        case "[M+NH4]+":
            return Formula(formula) + Formula("[NH4]+")
        case "[M-H]-":
            return Formula(formula) - Formula("[H]+")
        case "[M-2H]2-":
            return Formula(formula) - Formula("[H2]2+")
        case "[M-3H]3-":
            return Formula(formula) - Formula("[H3]3+")
        case "[M-4H]4-":
            return Formula(formula) - Formula("[H4]4+")
        case "[M+Cl]-":
            return Formula(formula) + Formula("[Cl]-")
        case "[M+OAc]-":
            return Formula(formula) + Formula("[CH3OO]-")
        case "[M+HCOO]-":
            return Formula(formula) + Formula("[HCOO]-")
        case "[M-2H+Na]-":
            return Formula(formula) + Formula("[Na]") - Formula("[H2]+")
        case "[M-3H+2Na]-":
            return Formula(formula) + Formula("[Na2]") - Formula("[H3]+")
        case "[M-2H+K]-":
            return Formula(formula) + Formula("[K]") - Formula("[H2]+")
        case "[M-3H+2K]-":
            return Formula(formula) + Formula("[K2]") - Formula("[H3]+")
        case "":
            return Formula(formula)
        case _:
            raise ValueError(f"Unsupported adduct in database: {adduct}")


def to_attr(col: str) -> str:
    # Replace anything that isn't a letter, digit, or underscore with "_"
    col = re.sub(r"[^0-9a-zA-Z_]", "_", col)
    # Ensure it doesn't start with a digit
    if col and col[0].isdigit():
        col = "_" + col
    return col


ID = "ID"
NEUTRAL_FORMULA = "Neutral Formula"
CLASS = "Class"
ADDUCTS = "Adducts"
M2_ISOTOPE = "M-2 Isotope"
M4_ISOTOPE = "M-4 Isotope"
NA_ISOTOPE = "Na+ Isotope"
IS = "IS"
AMOUNT_COL = "Standard amount (pmol / mm2)"
STD_COL = "Is standard"

S_ID = to_attr(ID)
S_NEUTRAL_FORMULA = to_attr(NEUTRAL_FORMULA)
S_CLASS = to_attr(CLASS)
S_ADDUCTS = to_attr(ADDUCTS)
S_M2_ISOTOPE = to_attr(M2_ISOTOPE)
S_M4_ISOTOPE = to_attr(M4_ISOTOPE)
S_NA_ISOTOPE = to_attr(NA_ISOTOPE)
S_IS = to_attr(IS)
S_AMOUNT_COL = to_attr(AMOUNT_COL)
S_STD_COL = to_attr(STD_COL)


class DatabaseFactory:
    """
    Class to help create a LipidDB instance based on information in an excel file.
    """

    def __init__(self, path: str, ion_mode: IonMode) -> None:
        self.df = pd.read_excel(path)
        self.ion_mode = ion_mode
        self.check_columns()
        self.setup_dataframe()

    def check_columns(self) -> None:
        """
        Check if necessary columns are present, add optional ones, and raise
        a comprehensive error for missing required ones.
        """

        required_cols = {
            ID,
            NEUTRAL_FORMULA,
            CLASS,
            ADDUCTS,
            M2_ISOTOPE,
            NA_ISOTOPE,
            IS,
            STD_COL,
            AMOUNT_COL,
        }
        optional_cols = {M4_ISOTOPE}

        df_cols = set(self.df.columns)

        missing_required = required_cols - df_cols
        if missing_required:
            missing_list = ", ".join(sorted(list(missing_required)))
            raise ValueError(
                f"The database is missing required columns: '{missing_list}'. "
                "Please ensure you have a valid database and restart."
            )

        missing_optional = optional_cols - df_cols
        for col in missing_optional:
            self.df[col] = None

    def setup_dataframe(self) -> None:
        """
        Set up the dataframe by expanding adduct forms and filtering on ion mode.
        Args:
            ion_mode (IonMode): The ion mode to filter the database.
        """

        # replace spaces in column names with underscores and remove special characters +,-,/
        self.df.columns = [to_attr(c) for c in self.df.columns]

        # add species with multiple adduct forms as individual rows for each adduct
        self.df[S_ADDUCTS] = self.df[S_ADDUCTS].str.replace(" ", "")
        self.df[S_ADDUCTS] = self.df[S_ADDUCTS].str.split(",")
        # add empty string adduct for neutral form
        self.df[S_ADDUCTS].apply(
            lambda lst: (
                lst.insert(0, "")
                if any([e for e in lst if e.endswith(self.ion_mode.value)])
                else lst
            )
        )
        self.df = self.df.explode(S_ADDUCTS)

        # filter by ion mode
        ion_mode_filer = self.df[S_ADDUCTS].str.endswith(self.ion_mode.value)
        neutral_species_filter = self.df[S_ADDUCTS] == ""
        self.df = self.df[ion_mode_filer | neutral_species_filter]

    @staticmethod
    def none_if_nan(value) -> Any | None:
        """if value is nan returns None else return the value"""
        if value != value:
            return None
        else:
            return value

    @staticmethod
    def normalize_bool(v):
        if isinstance(v, bool):
            return v
        if pd.isna(v):
            return False
        s = str(v).strip().lower()
        return s in {"true", "1", "yes", "y"}

    def create_database(self) -> LipidDB:
        """creates a LipidDB"""

        species: dict[str, LipidSpecies] = dict()

        for row in self.df.itertuples():
            id = getattr(row, S_ID)
            adduct = getattr(row, S_ADDUCTS)
            formula = adduct_formula(getattr(row, S_NEUTRAL_FORMULA), adduct)
            attributes = dict(
                adduct=getattr(row, S_ADDUCTS),
                id=id,
                lipid_class=getattr(row, S_CLASS),
                neutral_formula=Formula(getattr(row, S_NEUTRAL_FORMULA)),
                formula=formula,
                mz=formula.monoisotopic_mass,
                m2_rel_abundance=[i for (_, i) in formula.spectrum().items()][2].intensity / 100,
                m4_rel_abundance=[i for (_, i) in formula.spectrum().items()][4].intensity / 100,
                amount=getattr(row, S_AMOUNT_COL),
                m2_isotope=None,
                m4_isotope=None,
                na_isotope=None,
                standard=None,
            )
            adduct_id = id_adduct(id, adduct)
            if getattr(row, S_STD_COL):
                species[adduct_id] = LipidStandard(**attributes)
            else:
                species[adduct_id] = LipidSpecies(**attributes)

        id_to_adducts: dict[str, set[str]] = {}
        id_to_standard: dict[str, LipidStandard] = {}
        id_to_species: dict[str, LipidSpecies] = {}
        for specie in species.values():
            id_to_adducts.setdefault(specie.id, set()).add(specie.adduct)
            if isinstance(specie, LipidStandard):
                id_to_standard.setdefault(specie.id, specie)
            id_to_species.setdefault(specie.id, specie)

        def create_adduct_specie(base_specie: LipidSpecies, adduct: str) -> LipidSpecies:
            neutral_formula = base_specie.neutral_formula
            neutral_formula_str = getattr(neutral_formula, "formula", str(neutral_formula))
            formula = adduct_formula(neutral_formula_str, adduct)
            spectrum = [i for (_, i) in formula.spectrum().items()]
            attributes = dict(
                adduct=adduct,
                id=base_specie.id,
                lipid_class=base_specie.lipid_class,
                neutral_formula=neutral_formula,
                formula=formula,
                mz=formula.monoisotopic_mass,
                m2_rel_abundance=spectrum[2].intensity / 100,
                m4_rel_abundance=spectrum[4].intensity / 100,
                amount=base_specie.amount if isinstance(base_specie, LipidStandard) else None,
                m2_isotope=None,
                m4_isotope=None,
                na_isotope=None,
                standard=None,
            )
            if isinstance(base_specie, LipidStandard):
                return LipidStandard(**attributes)
            return LipidSpecies(**attributes)

        for i, row in enumerate(self.df.itertuples()):
            adduct = getattr(row, S_ADDUCTS)
            id = getattr(row, S_ID)
            specie = species[id_adduct(id, adduct)]
            standard_id = self.none_if_nan(getattr(row, S_IS))

            if standard_id is None:
                standard = None
            else:
                standard_key = id_adduct(standard_id, adduct)
                standard = species.get(standard_key)
                if standard is None:
                    available_adducts = id_to_adducts.get(standard_id)
                    if not available_adducts:
                        raise ValueError(
                            f"Value '{standard_id}' found in column 'IS' on row {i+2} is not a species defined "
                            "in column 'ID'. Check for typos in the IDs."
                        )
                    base_standard = id_to_standard.get(standard_id)
                    if base_standard is None:
                        raise ValueError(
                            f"On row {i+2} of column 'IS' the species '{standard_id}' has not been properly defined "
                            f"in the database as a standard. Check that '{standard_id}' has a value for 'IS amount "
                            "(pmol / mm2)'."
                        )
                    standard = create_adduct_specie(base_standard, adduct)
                    species[standard_key] = standard
                    id_to_adducts[standard_id].add(adduct)
            if standard is not None and not isinstance(standard, LipidStandard):
                raise (
                    ValueError(
                        f"On row {i+2} of column 'IS' the species '{standard}' has not been properly defined \
                        in the database as a standard. Check that '{standard}' has a value for 'IS amount \
                        (pmol / mm2)'."
                    )
                )
            specie.standard = standard

            m2_isotope_id = self.none_if_nan(getattr(row, S_M2_ISOTOPE))
            if m2_isotope_id is None:
                m2_isotope = None
            else:
                m2_key = id_adduct(m2_isotope_id, adduct)
                m2_isotope = species.get(m2_key)
                if m2_isotope is None:
                    base_specie = id_to_species.get(m2_isotope_id)
                    if base_specie is None:
                        raise ValueError(
                            f"Value '{m2_isotope_id}' found in column 'M-2 Isotope' on row {i+2} is not a species defined "
                            "in column 'ID'. Check for typos in the IDs."
                        )
                    m2_isotope = create_adduct_specie(base_specie, adduct)
                    species[m2_key] = m2_isotope
                    id_to_adducts.setdefault(m2_isotope_id, set()).add(adduct)
            specie.m2_isotope = m2_isotope

            m4_isotope_id = self.none_if_nan(getattr(row, S_M4_ISOTOPE))
            if m4_isotope_id is None:
                m4_isotope = None
            else:
                m4_key = id_adduct(m4_isotope_id, adduct)
                m4_isotope = species.get(m4_key)
                if m4_isotope is None:
                    base_specie = id_to_species.get(m4_isotope_id)
                    if base_specie is None:
                        raise ValueError(
                            f"Value '{m4_isotope_id}' found in column 'M-4 Isotope' on row {i+2} is not a species defined "
                            "in column 'ID'. Check for typos in the IDs."
                        )
                    m4_isotope = create_adduct_specie(base_specie, adduct)
                    species[m4_key] = m4_isotope
                    id_to_adducts.setdefault(m4_isotope_id, set()).add(adduct)
            specie.m4_isotope = m4_isotope

            na_isotope_id = self.none_if_nan(getattr(row, S_NA_ISOTOPE))
            na_isotope = (
                species.get(id_adduct(na_isotope_id, "[M+H]+"))
                if na_isotope_id is not None
                else None
            )
            specie.na_isotope = na_isotope

        return LipidDB(species=species)


class DatabaseEditor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = pd.read_excel(file_path, dtype={AMOUNT_COL: float})
        self.updated_IS_amounts = {}

        # Validate required columns
        missing = {ID, ADDUCTS, AMOUNT_COL, STD_COL} - set(self.data.columns)
        if missing:
            raise ValueError(f"Database is missing required columns: {sorted(missing)}")

        # Check for duplicate IDs + Adducts (as before)
        duplicated_rows = self.data[self.data.duplicated(subset=[ID, ADDUCTS])]
        if not duplicated_rows.empty:
            duplicates = duplicated_rows[[ID, ADDUCTS]].values.tolist()
            raise ValueError(
                f"Database is invalid: Duplicate ID + Adducts combination(s) found - {duplicates}"
            )

        # Normalize flag to bool
        self.data[STD_COL] = self.data[STD_COL].astype(bool)

    def get_standard_ids(self):
        """Return IDs explicitly marked as standards, plus any with staged edits."""
        ids = self.data.loc[self.data[STD_COL], ID].tolist()
        for staged_id in self.updated_IS_amounts.keys():
            if staged_id not in ids:
                ids.append(staged_id)
        return ids

    def get_IS_amount(self, id: str):
        """Prefer staged edits; otherwise return stored amount."""
        if id in self.updated_IS_amounts:
            return float(self.updated_IS_amounts[id])
        row = self.data[self.data[ID] == id]
        if row.empty:
            raise ValueError(f"ID {id} not found in database")
        return float(row[AMOUNT_COL].iloc[0])

    def set_IS_amount(self, id: str, new_IS_amount: float | str):
        if id not in self.data[ID].values:
            raise ValueError(f"ID {id} not found in database")
        try:
            if isinstance(new_IS_amount, str):
                sanitized = new_IS_amount.strip()
                sanitized = sanitized.replace(",", ".")
                value = float(sanitized)
            else:
                value = float(new_IS_amount)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid amount for ID {id}: {new_IS_amount!r}") from exc
        self.updated_IS_amounts[id] = value

    def set_is_standard(self, id: str, is_standard: bool):
        if id not in self.data[ID].values:
            raise ValueError(f"ID {id} not found in database")
        self.data.loc[self.data[ID] == id, STD_COL] = bool(is_standard)

    def save(self):
        for id, new_IS_amount in self.updated_IS_amounts.items():
            self.data.loc[self.data[ID] == id, AMOUNT_COL] = new_IS_amount
        self.data.to_excel(self.file_path, index=False)
        self.updated_IS_amounts.clear()
