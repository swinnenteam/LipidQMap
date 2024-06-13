from enum import Enum

import numpy as np
import pandas as pd


class IonMode(str, Enum):
    """
    Enum for specifying ion mode.
    """

    positive = "+"
    negative = "-"


class LipidDB:

    def __init__(self, path: str, ion_mode: IonMode) -> None:

        # load database
        self.db = pd.read_excel(path)
        self.db.rename(columns={"m/z": "mz"}, inplace=True)
        self.db["Class_Adduct"] = self.db.apply(self._add_adduct_to_id, axis=1, column="Class")
        self.db["ID_Adduct"] = self.db.apply(self._add_adduct_to_id, axis=1, column="ID")
        self.db["M-2"] = self.db.apply(self._add_adduct_to_id, axis=1, column="M-2")
        self.db.set_index("ID_Adduct", inplace=True, drop=False)

        # filter by ion mode
        self.db = self.db[self.db["Adduct"].str.endswith(ion_mode.value)]

    def _add_adduct_to_id(self, row: pd.Series, column: str):
        if not pd.isnull(row[column]):
            return row[column] + " " + row["Adduct"]

    def get_id(self, index: int) -> str:
        return self.db.index[index]

    def get_class(self, id: str) -> str:
        return self.db.loc[id, "Class_Adduct"]

    def class_filtered_db(self, classes: list[str] | None) -> pd.DataFrame:
        if classes:
            return self.db[self.db["Class_Adduct"].isin(classes)]
        else:
            return self.db

    def get_ids_non_standards(self, classes: list[str] | None = None) -> list[str]:
        filtered = self.class_filtered_db(classes=classes)
        return filtered[filtered["IS amount ()"].isnull()].index.to_list()

    def get_standard(self, id: str) -> tuple[str, float]:
        """Get standard id and amount for given species id"""
        class_adduct = self.db.loc[id, "Class_Adduct"]
        standard = self._get_standard_for_class_adduct(class_adduct)
        if standard is None:
            raise ValueError(f"There is no standard in the database for class {class_adduct}")
        return standard

    def _get_standard_for_class_adduct(self, class_adduct: str) -> tuple[str, float] | None:
        filtered = self.class_filtered_db(classes=[class_adduct])
        standard = filtered["IS amount ()"].dropna()
        if standard.shape[0] < 1:
            return None
        return (standard.index[0], float(standard[0]))

    def get_M2_isotope_ID(self, id: str) -> str | None:
        isotope_id = self.db.loc[id, "M-2"]
        if pd.isnull(isotope_id):
            return None
        return isotope_id

    def get_M2_isotope_percent(self, id: str) -> float:
        return self.db.loc[id, "M+2 % intensity"] / 100

    def get_ids_sorted_for_isotope(self, classes: list[str] | None = None) -> list[str]:
        filtered = self.class_filtered_db(classes)
        return filtered.sort_values(["Class_Adduct", "mz"], ascending=[True, True]).index.to_list()

    def get_sodium_coef_mzs(self) -> dict[str, tuple[str, str]]:
        """
        Return for all [M+H]+ classes the m/z of the standard of the class and the m/z
        of the standard of the [Na]+ adduct of that class.
        """
        lipid_classes = np.unique(self.db.loc[self.db["Adduct"] == "[M+H]+", "Class"].values)
        result = dict()
        for lipid_class in lipid_classes:
            hydrogen_adduct_std = self._get_standard_for_class_adduct(lipid_class + " [M+H]+")
            sodium_adduct_std = self._get_standard_for_class_adduct(lipid_class + " [M+Na]+")
            if hydrogen_adduct_std is not None and sodium_adduct_std is not None:
                result[str(lipid_class + " [M+H]+")] = (
                    hydrogen_adduct_std[0],
                    sodium_adduct_std[0],
                )
        return result

    def get_Na_isotope_ID(self, id: str) -> str | None:
        lipid_class = self.get_class(id=id)
        carbons = self.db.loc[id, "Carbons"] - 2
        dbonds = self.db.loc[id, "Double bonds"] - 3
        oxigens = self.db.loc[id, "Oxigens"]
        result = self.db.query(
            f'Carbons=={carbons} & `Double bonds`=={dbonds} & Oxigens=={oxigens} & Class_Adduct=="{lipid_class}"'
        )
        if result.shape[0] < 1:
            return None
        return result.index[0]

    def get_all_species(self, classes: list[str] | None = None) -> tuple[list[str], list[float]]:
        filtered = self.class_filtered_db(classes)
        return list(filtered.ID_Adduct), list(filtered.mz)

    def get_table(self) -> pd.DataFrame:
        d = {"Species": self.db.index, "m/z": self.db["mz"], "Export": True}
        df = pd.DataFrame(data=d, index=self.db.index)
        return df

    def verify_ion_mode(self, ion_mode: IonMode) -> True:
        not_present_mode = IonMode.negative if ion_mode == IonMode.positive else IonMode.positive
        check_1 = self.db["Adduct"].str.endswith(ion_mode.value).all()
        check_2 = not self.db["Adduct"].str.endswith(not_present_mode).any()
        return check_1 and check_2
