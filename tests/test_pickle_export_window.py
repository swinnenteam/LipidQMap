from app.views.pickle_export_window import filter_species_by_summed_option


def _is_summed_stub(species_id: str) -> bool:
    return species_id.endswith(" (+)") or species_id.endswith(" (-)")


def test_filter_species_by_summed_option_keeps_summed_when_enabled() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)", "lipid2 [M-H]-"]

    filtered = filter_species_by_summed_option(
        species,
        include_summed=True,
        is_summed_fn=_is_summed_stub,
    )

    assert filtered == species


def test_filter_species_by_summed_option_excludes_summed_when_disabled() -> None:
    species = ["lipid1 (+)", "lipid1 [M+H]+", "lipid2 (-)", "lipid2 [M-H]-"]

    filtered = filter_species_by_summed_option(
        species,
        include_summed=False,
        is_summed_fn=_is_summed_stub,
    )

    assert filtered == ["lipid1 [M+H]+", "lipid2 [M-H]-"]
