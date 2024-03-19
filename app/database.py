from typing import Iterable

import pandas as pd

from app.config import config_paths


class LipidDB:

    def __init__(self, path: str) -> None:

        # load database
        self.db = pd.read_excel(path)
        self.db.rename(columns={"m/z": "mz"}, inplace=True)
        self.db["Class_Adduct"] = self.db.apply(self.add_adduct_to_id, axis=1, column="Class")
        self.db["ID_Adduct"] = self.db.apply(self.add_adduct_to_id, axis=1, column="ID")
        self.db["M-2"] = self.db.apply(self.add_adduct_to_id, axis=1, column="M-2")
        self.db.set_index("ID_Adduct", inplace=True, drop=False)

    def add_adduct_to_id(self, row: pd.Series, column: str):
        if not pd.isnull(row[column]):
            return row[column] + " " + row["Adduct"]

    def class_filtered_db(self, classes: list[str]) -> pd.DataFrame:
        return self.db[self.db["Class_Adduct"].isin(classes)]

    def get_ids_non_standards(self, classes: list[str]) -> list[str]:
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

    def get_ids_sorted_for_isotope(self, classes: list[str]) -> list[str]:
        filtered = self.class_filtered_db(classes)
        return filtered.sort_values(["Class_Adduct", "mz"], ascending=[True, True]).index.to_list()

    def get_all_species(self, classes: list[str]) -> Iterable[tuple[str, float]]:
        filtered = self.class_filtered_db(classes)
        for row in filtered.itertuples():
            yield (row.ID_Adduct, row.mz)


def load_database(
    database_path: str = config_paths["DATABASE_FILE"],
) -> LipidDB:
    return LipidDB(database_path)
