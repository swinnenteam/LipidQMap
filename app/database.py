from enum import Enum
from pathlib import Path

import pandas as pd

from app.config import config_paths


class IonMode(str, Enum):
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

    def class_filtered_db(self, classes: list[str] | None) -> pd.DataFrame:
        if classes:
            return self.db[self.db["Class_Adduct"].isin(classes)]
        else:
            return self.db

    def get_ids_non_standards(self, classes: list[str] | None = None) -> list[str]:
        filtered = self.class_filtered_db(classes=classes)
        return filtered[filtered["IS amount ()"].isnull()].index.to_list()

    def get_standard(self, id: str) -> tuple[str, float]:
        classes = self.db.loc[id, "Class_Adduct"]
        filtered = self.class_filtered_db(classes=[classes])
        standard = filtered["IS amount ()"].dropna()
        if standard.shape[0] != 1:
            raise ValueError(f"There is no standard in the database for class {classes}")
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

    def get_all_species(self, classes: list[str] | None = None) -> list[tuple[str, float]]:
        filtered = self.class_filtered_db(classes)
        result = []
        for row in filtered.itertuples():
            result.append((row.ID_Adduct, row.mz))
        return result

    def get_table(self) -> pd.DataFrame:
        d = {"Species": self.db.index, "m/z": self.db["mz"], "Export": True}
        df = pd.DataFrame(data=d, index=self.db.index)
        return df

    def verify_ion_mode(self, ion_mode: IonMode) -> True:
        not_present_mode = IonMode.negative if ion_mode == IonMode.positive else IonMode.positive
        check_1 = self.db["Adduct"].str.endswith(ion_mode.value).all()
        check_2 = not self.db["Adduct"].str.endswith(not_present_mode).any()
        return check_1 and check_2
