from app.database import IonMode, LipidDB, LipidSpecies


def _combine_mode_databases(
    databases_by_mode: dict[IonMode, LipidDB],
    skipped_na_correction_classes: set[str] | None = None,
) -> LipidDB:
    """Create the display database used for one or more acquisition modes."""
    combined_species: dict[str, LipidSpecies] = {}
    for mode in (IonMode.positive, IonMode.negative):
        db = databases_by_mode.get(mode)
        if db is None:
            continue
        for specie in db.species.values():
            if specie.adduct == "":
                neutral_copy = specie.model_copy(deep=True)
                neutral_copy.adduct = "(+)" if mode == IonMode.positive else "(-)"
                for attr in ("id_adduct", "class_adduct", "ion_mode"):
                    neutral_copy.__dict__.pop(attr, None)
                combined_species[neutral_copy.id_adduct] = neutral_copy
            else:
                combined_species.setdefault(specie.id_adduct, specie)

    combined_database = LipidDB(combined_species)
    species_order = combined_database.species_ids_neutral_first()
    combined_database.index = species_order
    combined_database.na_isotope_correction_skipped_classes = sorted(
        skipped_na_correction_classes or set()
    )
    return combined_database
