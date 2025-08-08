from __future__ import annotations

from enum import Enum
from functools import cached_property
from typing import Any

import pandas as pd
from molmass import Formula
from pydantic import BaseModel, ConfigDict


class IonMode(str, Enum):
    """
    Enum for specifying ion mode.
    """

    positive = "+"
    negative = "-"
    neutral = ""


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
            return IonMode.neutral

    def __repr__(self):
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
        return [s for s in self.species.values() if current_specie.class_adduct == s.class_adduct]

    def get_ids_non_standards(self) -> list[LipidSpecies]:
        """
        Get a list of IDs for non-standard species.
        Returns:
            list[LipidSpecies]: A list of non-standard species IDs.
        """
        return [
            s
            for s in self.species.values()
            if (not s.is_standard) and s.ion_mode != IonMode.neutral
        ]

    def get_species_sorted_for_isotope(self) -> list[LipidSpecies]:
        """
        Get a list of species IDs sorted by lowest mz first.
        Returns:
            list[LipidSpecies]: A list of species IDs sorted by Class_Adduct and m/z.
        """
        species = [s for s in self.species.values() if s.ion_mode != IonMode.neutral]
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
        return [s for s in self.species.values() if s.ion_mode == IonMode.neutral]

    def get_adduct_species_for_neutral(self, species: LipidSpecies) -> list[LipidSpecies]:
        """
        Given a species, returns the list of all adduct forms of this species
        """
        return [s for s in list(self.species.values()) if s.id == species.id and s.adduct != ""]

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
                if specie.ion_mode != IonMode.neutral
            ]
        ids, mzs = zip(*species_list)
        return list(ids), list(mzs)

    def get_table(self) -> pd.DataFrame:
        """
        Get a DataFrame of the LipidDB for representation in the gui.
        Returns:
            pd.DataFrame: A DataFrame containing species IDs and their m/z values, marked for export.
        """

        d = {
            "Species": self.index,
            "m/z": [specie.mz for specie in self.species.values()],
            "Export": True,
        }
        df = pd.DataFrame(data=d, index=self.index)
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
            (specie.ion_mode == ion_mode or specie.ion_mode == IonMode.neutral)
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
            "ID",
            "Neutral Formula",
            "Class",
            "Adducts",
            "M-2 Isotope",
            "Na+ Isotope",
            "IS",
            "IS amount (pmol / mm2)",
        }
        optional_cols = {"M-4 Isotope"}

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
        self.df.rename(columns={"IS amount (pmol / mm2)": "IS amount"}, inplace=True)
        self.df.rename(columns={"M-2 Isotope": "M2 Isotope"}, inplace=True)
        self.df.rename(columns={"M-4 Isotope": "M4 Isotope"}, inplace=True)
        self.df.rename(columns={"Na+ Isotope": "Na Isotope"}, inplace=True)
        self.df.columns = [c.replace(" ", "_") for c in self.df.columns]

        # add species with multiple adduct forms as individual rows for each adduct
        self.df["Adducts"] = self.df["Adducts"].str.replace(" ", "")
        self.df["Adducts"] = self.df["Adducts"].str.split(",")
        # add empty string adduct for neutral form
        self.df["Adducts"].apply(
            lambda lst: (
                lst.insert(0, "")
                if any([e for e in lst if e.endswith(self.ion_mode.value)])
                else lst
            )
        )
        self.df = self.df.explode("Adducts")

        # filter by ion mode
        ion_mode_filer = self.df["Adducts"].str.endswith(self.ion_mode.value)
        neutral_species_filter = self.df["Adducts"] == ""
        self.df = self.df[ion_mode_filer | neutral_species_filter]

    @staticmethod
    def none_if_nan(value) -> Any | None:
        """if value is nan returns None else return the value"""
        if value != value:
            return None
        else:
            return value

    def create_database(self) -> LipidDB:
        """creates a LipidDB"""

        species: dict[str, LipidSpecies] = dict()

        for row in self.df.itertuples():
            id = getattr(row, "ID")
            adduct = getattr(row, "Adducts")
            formula = adduct_formula(getattr(row, "Neutral_Formula"), adduct)
            attributes = dict(
                adduct=getattr(row, "Adducts"),
                id=id,
                lipid_class=getattr(row, "Class"),
                neutral_formula=Formula(getattr(row, "Neutral_Formula")),
                formula=formula,
                mz=formula.monoisotopic_mass,
                m2_rel_abundance=[i for (_, i) in formula.spectrum().items()][2].intensity / 100,
                m4_rel_abundance=[i for (_, i) in formula.spectrum().items()][4].intensity / 100,
                amount=self.none_if_nan(getattr(row, "IS_amount")),
                m2_isotope=None,
                m4_isotope=None,
                na_isotope=None,
                standard=None,
            )

            adduct_id = id_adduct(id, adduct)
            if attributes.get("amount") is None:
                species[adduct_id] = LipidSpecies(**attributes)
            else:
                species[adduct_id] = LipidStandard(**attributes)

        for i, row in enumerate(self.df.itertuples()):
            adduct = getattr(row, "Adducts")
            id = getattr(row, "ID")

            specie = species[id_adduct(id, adduct)]

            standard = self.none_if_nan(getattr(row, "IS"))
            try:
                standard = species[id_adduct(standard, adduct)] if standard is not None else None
            except Exception:
                raise (
                    ValueError(
                        f"Value '{standard}' found in column 'IS' on row {i+2} is not a species defined \
                        in column 'ID'. Check for typos in the IDs."
                    )
                )
            if standard is not None and not isinstance(standard, LipidStandard):
                raise (
                    ValueError(
                        f"On row {i+2} of column 'IS' the species '{standard}' has not been properly defined \
                        in the database as a standard. Check that '{standard}' has a value for 'IS amount \
                        (pmol / mm2)'."
                    )
                )
            specie.standard = standard

            m2_isotope = self.none_if_nan(getattr(row, "M2_Isotope"))
            try:
                m2_isotope = (
                    species[id_adduct(m2_isotope, adduct)] if m2_isotope is not None else None
                )
            except Exception:
                raise (
                    ValueError(
                        f"Value '{m2_isotope}' found in column 'M-2 Isotope' on row {i+2} is not a species defined \
                        in column 'ID'. Check for typos in the IDs."
                    )
                )
            specie.m2_isotope = m2_isotope

            m4_isotope = self.none_if_nan(getattr(row, "M4_Isotope"))
            try:
                m4_isotope = (
                    species[id_adduct(m4_isotope, adduct)] if m4_isotope is not None else None
                )
            except Exception:
                raise (
                    ValueError(
                        f"Value '{m4_isotope}' found in column 'M-4 Isotope' on row {i+2} is not a species defined \
                        in column 'ID'. Check for typos in the IDs."
                    )
                )
            specie.m4_isotope = m4_isotope

            na_isotope_id = self.none_if_nan(getattr(row, "Na_Isotope"))
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
        self.data = pd.read_excel(file_path, dtype={"IS amount (pmol / mm2)": float})
        self.updated_IS_amounts = {}

        # Check for duplicate IDs
        duplicated_rows = self.data[self.data.duplicated(subset=["ID", "Adducts"])]
        if not duplicated_rows.empty:
            duplicates = duplicated_rows[["ID", "Adducts"]].values.tolist()
            raise ValueError(
                f"Database is invalid: Duplicate ID + Adducts combination(s) found - {duplicates}"
            )

    def get_standard_ids(self):
        """Return a list of IDs where IS amount has a numeric value."""
        return self.data[self.data["IS amount (pmol / mm2)"].notna()]["ID"].tolist()

    def get_IS_amount(self, id: str):
        """Return the IS amount (as a float) for a given ID."""
        row = self.data[self.data["ID"] == id]
        if not row.empty:
            return float(row["IS amount (pmol / mm2)"].iloc[0])
        else:
            raise ValueError(f"ID {id} not found in database")

    def set_IS_amount(self, id: str, new_IS_amount: str):
        """Set the new IS amount for a given ID."""
        if id in self.data["ID"].values:
            self.updated_IS_amounts[id] = float(new_IS_amount)
        else:
            raise ValueError(f"ID {id} not found in database")

    def save(self):
        """Save updated IS amounts to the Excel file."""
        for ID, new_IS_amount in self.updated_IS_amounts.items():
            self.data.loc[self.data["ID"] == ID, "IS amount (pmol / mm2)"] = new_IS_amount

        # Save to the original file
        self.data.to_excel(self.file_path, index=False)
