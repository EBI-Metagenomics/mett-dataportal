from types import SimpleNamespace

from dataportal.ingest.utils import (
    load_scientific_names_by_acronym,
    reset_species_name_cache,
    species_name_for_acronym,
    species_name_for_isolate,
)


def test_species_name_for_isolate_uses_elasticsearch_species_index(monkeypatch):
    reset_species_name_cache()
    hits = [
        SimpleNamespace(
            acronym="BU", scientific_name="Bacteroides uniformis", meta=SimpleNamespace(id="BU")
        ),
        SimpleNamespace(
            acronym="AR",
            scientific_name="Anaerostipes rhamnosivorans",
            meta=SimpleNamespace(id="AR"),
        ),
    ]
    calls = {"n": 0}

    def fake_fetch():
        calls["n"] += 1
        return {hit.acronym: hit.scientific_name for hit in hits}

    monkeypatch.setattr("dataportal.ingest.utils._fetch_species_name_map", fake_fetch)

    assert species_name_for_isolate("BU_ATCC8492") == "Bacteroides uniformis"
    assert species_name_for_isolate("AR_VPI0990") == "Anaerostipes rhamnosivorans"
    assert species_name_for_acronym("ar") == "Anaerostipes rhamnosivorans"
    assert species_name_for_isolate("XX_UNKNOWN") is None
    assert species_name_for_isolate("nounderscore") is None
    assert calls["n"] == 1
    assert load_scientific_names_by_acronym()["BU"] == "Bacteroides uniformis"
    reset_species_name_cache()
