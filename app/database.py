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
    na_isotope: LipidSpecies | None
    standard: LipidStandard | None

    @cached_property
    def id_adduct(self) -> str:
        """Returns the identifier concatenated with the adduct."""
        return self.id + " " + self.adduct

    @cached_property
    def class_adduct(self) -> str:
        """Returns the lipid class concatenated with the adduct."""
        return self.lipid_class + " " + self.adduct

    @cached_property
    def is_standard(self) -> bool:
        """Checks if the current instance is a standard lipid species."""
        return self.__class__ is LipidStandard

    @cached_property
    def ion_mode(self) -> IonMode:
        """Determines the ion mode based on the adduct."""
        if self.adduct.endswith("+"):
            return IonMode.positive
        else:
            return IonMode.negative

    def __lt__(self, other):
        return (self.adduct, self.mz) < (other.adduct, other.mz)


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
        return [s for s in self.species.values() if not s.is_standard]

    def get_species_sorted_for_isotope(self) -> list[LipidSpecies]:
        """
        Get a list of species IDs sorted by lowest mz first.
        Returns:
            list[LipidSpecies]: A list of species IDs sorted by Class_Adduct and m/z.
        """
        species = list(self.species.values())
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

    def get_all_species(self) -> tuple[list[str], list[float]]:
        """
        Get all species IDs and their m/z values.
        Returns:
            tuple[list[str], list[float]]: A tuple containing a list of species IDs and a list of their m/z values.
        """
        mzs = [specie.mz for specie in self.species.values()]
        return (self.index, mzs)

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
        return all(specie.ion_mode == ion_mode for specie in self.species.values())


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
        Check if the necessary columns are present in the database.
        """

        columns = [
            "ID",
            "Neutral Formula",
            "Class",
            "Adducts",
            "M-2 Isotope",
            "Na+ Isotope",
            "IS",
            "IS amount (pmol / mm2)",
        ]
        for col in columns:
            if not col in self.df.columns:
                raise ValueError(f"The excel database is missing the '{col}' column.")

    def setup_dataframe(self) -> None:
        """
        Set up the dataframe by expanding adduct forms and filtering on ion mode.
        Args:
            ion_mode (IonMode): The ion mode to filter the database.
        """

        # replace spaces in column names with underscores and remove special characters +,-,/
        self.df.rename(columns={"IS amount (pmol / mm2)": "IS amount"}, inplace=True)
        self.df.rename(columns={"M-2 Isotope": "M2 Isotope"}, inplace=True)
        self.df.rename(columns={"Na+ Isotope": "Na Isotope"}, inplace=True)
        self.df.columns = [c.replace(" ", "_") for c in self.df.columns]

        # Add species with multiple adduct forms as individual rows for each adduct.
        self.df["Adducts"] = self.df["Adducts"].str.replace(" ", "")
        self.df["Adducts"] = self.df["Adducts"].str.split(",")
        self.df = self.df.explode("Adducts")

        # filter by ion mode
        self.df = self.df[self.df["Adducts"].str.endswith(self.ion_mode.value)]

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
                amount=self.none_if_nan(getattr(row, "IS_amount")),
                m2_isotope=None,
                na_isotope=None,
                standard=None,
            )

            if attributes.get("amount") is None:
                species[id + " " + adduct] = LipidSpecies(**attributes)
            else:
                species[id + " " + adduct] = LipidStandard(**attributes)

        for i, row in enumerate(self.df.itertuples()):
            adduct = getattr(row, "Adducts")
            id = getattr(row, "ID")
            specie = species[id + " " + adduct]

            standard = self.none_if_nan(getattr(row, "IS"))
            try:
                standard = species[standard + " " + adduct] if standard is not None else None
            except:
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
                m2_isotope = species[m2_isotope + " " + adduct] if m2_isotope is not None else None
            except:
                raise (
                    ValueError(
                        f"Value '{m2_isotope}' found in column 'M-2 Isotope' on row {i+2} is not a species defined \
                        in column 'ID'. Check for typos in the IDs."
                    )
                )
            specie.m2_isotope = m2_isotope

            na_isotope_id = self.none_if_nan(getattr(row, "Na_Isotope"))
            na_isotope = (
                species.get(na_isotope_id + " " + "[M+Na]+") if na_isotope_id is not None else None
            )
            specie.na_isotope = na_isotope

        return LipidDB(species=species)
