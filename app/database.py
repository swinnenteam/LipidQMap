from enum import Enum

import numpy as np
import pandas as pd
from molmass import Formula


class IonMode(str, Enum):
    """
    Enum for specifying ion mode.
    """

    positive = "+"
    negative = "-"


def adduct_furmula(formula: str, adduct: str) -> Formula:
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


class LipidDB:
    """
    Class for handling lipid databases and performing operations based on ion modes and adducts.

    Attributes:
        db (pd.DataFrame): The loaded lipid database.
    """

    def __init__(self, path: str, ion_mode: IonMode) -> None:
        """
        Initialize the LipidDB object by loading the database and setting up based on ion mode.

        Args:
            path (str): The file path to the lipid database (Excel file).
            ion_mode (IonMode): The ion mode to filter the database.
        """

        self.db = pd.read_excel(path)
        self.check_columns()
        self.setup_database(ion_mode=ion_mode)

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
            if not col in self.db.columns:
                raise ValueError(f"The excel database is missing the '{col}' column.")

    def setup_database(self, ion_mode: IonMode) -> None:
        """
        Set up the database by expanding adduct forms and calculating necessary values.
        Args:
            ion_mode (IonMode): The ion mode to filter the database.
        """

        # Add species with multiple adduct forms as individual rows for each adduct.
        self.db["Adducts"] = self.db["Adducts"].str.replace(" ", "")
        self.db["Adducts"] = self.db["Adducts"].str.split(",")
        self.db = self.db.explode("Adducts")

        # Add adduct str to the values of columns Class, ID, M-2 isotope and IS
        self.db["Class_Adduct"] = self.db.apply(self._add_adduct_to_id, axis=1, column="Class")
        self.db["ID_Adduct"] = self.db.apply(self._add_adduct_to_id, axis=1, column="ID")
        self.db["M-2 Isotope"] = self.db.apply(self._add_adduct_to_id, axis=1, column="M-2 Isotope")
        self.db["IS"] = self.db.apply(self._add_adduct_to_id, axis=1, column="IS")
        self.db.set_index("ID_Adduct", inplace=True, drop=False)

        # Add adduct Formula, mz and M+2 % intensity columns
        formula: Formula
        formulas: list[Formula] = []
        mz: list[float] = []
        m2_intensities: list[float] = []

        for str_formula, str_adduct in zip(
            self.db["Neutral Formula"].values, self.db["Adducts"].values
        ):
            formula = adduct_furmula(str_formula, str_adduct)
            formulas.append(formula)
            mz.append(formula.monoisotopic_mass)
            m2_intensities.append([item for (_, item) in formula.spectrum().items()][2].intensity)

        self.db["Formula"] = formulas
        self.db["mz"] = mz
        self.db["M+2 % intensity"] = m2_intensities

        # filter by ion mode
        self.db = self.db[self.db["Adducts"].str.endswith(ion_mode.value)]

    def get_id(self, index: int) -> str:
        """
        Returns the Lipid_id at the requested index
        """
        return self.db.index[index]

    def get_all_species_same_class(self, species_id: str) -> list[str]:
        class_adduct = self.db.loc[self.db.index == species_id, "Class_Adduct"]
        class_adduct = class_adduct.values[0]
        return self.db[self.db.Class_Adduct == class_adduct].index.to_list()

    def _add_adduct_to_id(self, row: pd.Series, column: str):
        """
        Append the adduct to the specified column value in the row.
        Args:
            row (pd.Series): A row from the DataFrame.
            column (str): The column to which the adduct should be appended.
        Returns:
            str: The modified column value with the adduct appended.
        """

        if not pd.isnull(row[column]):
            return row[column] + " " + row["Adducts"]

    def get_ids_non_standards(self) -> list[str]:
        """
        Get a list of IDs for non-standard species.
        Returns:
            list[str]: A list of non-standard species IDs.
        """

        return self.db[self.db["IS amount (pmol / mm2)"].isnull()].index.to_list()

    def get_standard(self, id: str) -> tuple[str, float] | tuple[None, None]:
        """
        Get the standard ID and amount for a given species ID.
        Args:
            id (str): The species ID.
        Returns:
            tuple[str, float]: The standard ID and its amount.
        Raises:
            ValueError: If there is no standard for the given species ID.
        """

        standard_id = self.db.loc[id, "IS"]
        if pd.isnull(standard_id):
            return (None, None)
        return (standard_id, self.db.loc[standard_id, "IS amount (pmol / mm2)"])

    def get_M2_isotope_ID(self, id: str) -> str | None:
        """
        Get the ID of the M-2 isotope for a given species ID.
        Args:
            id (str): The species ID.
        Returns:
            str | None: The M-2 isotope ID or None if not present.
        """

        isotope_id = self.db.loc[id, "M-2 Isotope"]
        if pd.isnull(isotope_id):
            return None
        return isotope_id

    def get_M2_isotope_percent(self, id: str) -> float:
        """
        Get the M+2 isotope percent intensity for a given species ID.
        Args:
            id (str): The species ID.
        Returns:
            float: The M+2 isotope percent intensity.
        """

        return self.db.loc[id, "M+2 % intensity"] / 100

    def get_ids_sorted_for_isotope(self) -> list[str]:
        """
        Get a list of species IDs sorted by lowest mz first.
        Returns:
            list[str]: A list of species IDs sorted by Class_Adduct and m/z.
        """

        return self.db.sort_values(["Class_Adduct", "mz"], ascending=[True, True]).index.to_list()

    def get_hydrogen_sodium_std_pairs(self) -> list[tuple[str, str]]:
        """
        Get all [M+H]+ and [M+Na]+ standard pairs.
        Returns:
            list[tuple[str, str]]: A list of tuples containing pairs of [M+H]+ and [M+Na]+ standard IDs.

        """

        standard_pairs = []
        # get all [M+H]+ standards
        h_standards = self.db.loc[self.db["Adducts"] == "[M+H]+", "IS"].values
        h_standards = [value for value in h_standards if value is not None]
        h_standards = np.unique(h_standards)
        # check if corresponding [M+H]+ standard is present
        for h_standard_id in h_standards:
            standard_id = self.db.loc[h_standard_id, "ID"]
            if standard_id + " [M+Na]+" in self.db.index:
                standard_pairs.append((h_standard_id, standard_id + " [M+Na]+"))
        return standard_pairs

    def get_Na_isotope_ID(self, id: str) -> str | None:
        """
        Get the Na+ isotope ID for a given species ID.
        Args:
            id (str): The species ID.
        Returns:
            str | None: The Na+ isotope ID or None if not present.
        """

        isotope_id = self.db.loc[id, "Na+ Isotope"]
        if pd.isnull(isotope_id):
            return None
        return isotope_id + " [M+Na]+"

    def get_all_species(self) -> tuple[list[str], list[float]]:
        """
        Get all species IDs and their m/z values.
        Returns:
            tuple[list[str], list[float]]: A tuple containing a list of species IDs and a list of their m/z values.
        """

        return list(self.db.ID_Adduct), list(self.db.mz)

    def get_table(self) -> pd.DataFrame:
        """
        Get a DataFrame of the LipidDB for representation in the gui.
        Returns:
            pd.DataFrame: A DataFrame containing species IDs and their m/z values, marked for export.
        """

        d = {"Species": self.db.index, "m/z": self.db["mz"], "Export": True}
        df = pd.DataFrame(data=d, index=self.db.index)
        return df

    def verify_ion_mode(self, ion_mode: IonMode) -> True:
        """
        Verify that the database contains only the specified ion mode.
        Args:
            ion_mode (IonMode): The ion mode to verify.
        Returns:
            bool: True if the database contains only the specified ion mode, False otherwise.
        """

        not_present_mode = IonMode.negative if ion_mode == IonMode.positive else IonMode.positive
        check_1 = self.db["Adducts"].str.endswith(ion_mode.value).all()
        check_2 = not self.db["Adducts"].str.endswith(not_present_mode).any()
        return check_1 and check_2
