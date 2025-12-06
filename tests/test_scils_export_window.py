from app.views.scils_export_window import (
    AdductSelection,
    filter_species_by_adduct_selection,
)


def _is_summed_stub(species_id: str) -> bool:
    return species_id.endswith(" (+)") or species_id.endswith(" (-)")


def test_filter_species_includes_all_for_combined_option() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)"]

    filtered = filter_species_by_adduct_selection(
        species,
        AdductSelection.adducts_and_summed,
        _is_summed_stub,
    )

    assert filtered == species


def test_filter_species_only_adducts_excludes_summed() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)", "lipid2 [M-H]-"]

    filtered = filter_species_by_adduct_selection(
        species,
        AdductSelection.adducts_only,
        _is_summed_stub,
    )

    assert filtered == ["lipid1 [M+H]+", "lipid2 [M-H]-"]


def test_filter_species_only_summed_includes_neutral_only() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)", "lipid2 [M-H]-"]

    filtered = filter_species_by_adduct_selection(
        species,
        AdductSelection.summed_only,
        _is_summed_stub,
    )

    assert filtered == ["lipid1 (+)", "lipid2 (-)"]
