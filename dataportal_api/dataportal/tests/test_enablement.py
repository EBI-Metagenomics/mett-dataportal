from dataportal.ingest.species.importer import parse_enabled_flag
from dataportal.utils import enablement


def test_parse_enabled_flag_handles_csv_booleans():
    assert parse_enabled_flag("true") is True
    assert parse_enabled_flag("false") is False
    assert parse_enabled_flag("FALSE") is False
    assert parse_enabled_flag("0") is False
    assert parse_enabled_flag("1") is True
    assert parse_enabled_flag(None) is True
    assert parse_enabled_flag("maybe") is True


def test_resolve_enabled_species_intersects_requested(monkeypatch):
    monkeypatch.setattr(enablement, "get_enabled_species_acronyms", lambda: {"BU", "PV"})

    assert enablement.resolve_enabled_species(None) == ["BU", "PV"]
    assert enablement.resolve_enabled_species("BU,BF") == ["BU"]
    assert enablement.resolve_enabled_species(["bf", "PV"]) == ["PV"]
    assert enablement.resolve_enabled_species("BF,EL") == []


def test_resolve_enabled_isolates_case_insensitive(monkeypatch):
    monkeypatch.setattr(
        enablement, "get_enabled_isolate_names", lambda: {"BU_ATCC8492", "PV_ATCC8482"}
    )

    assert enablement.resolve_enabled_isolates("bu_atcc8492,MISSING") == ["BU_ATCC8492"]
    assert sorted(enablement.resolve_enabled_isolates(None)) == [
        "BU_ATCC8492",
        "PV_ATCC8482",
    ]


def test_gene_visibility_blocks_when_species_disabled(monkeypatch):
    monkeypatch.setattr(enablement, "get_enabled_species_acronyms", lambda: {"BU"})
    monkeypatch.setattr(enablement, "get_enabled_isolate_names", lambda: {"BU_ATCC8492"})

    assert enablement.gene_visibility_blocks_all(species_acronym="BF") is True
    assert enablement.gene_visibility_blocks_all(species_acronym="BU") is False
    assert (
        enablement.gene_visibility_blocks_all(species_acronym="BU", isolates="BU_MISSING") is True
    )


def test_strain_not_disabled_clause_keeps_missing_enabled():
    clause = enablement.strain_not_disabled_clause()
    assert clause == {"bool": {"must_not": [{"term": {"enabled": False}}]}}
