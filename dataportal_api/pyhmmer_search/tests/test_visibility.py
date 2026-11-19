from pyhmmer_search.visibility import limit_search_species, visible_catalog, visible_hits


def test_visible_hits_keep_only_enabled_species(monkeypatch):
    monkeypatch.setattr(
        "pyhmmer_search.visibility.get_enabled_species_acronyms",
        lambda: {"BU", "PV"},
    )
    monkeypatch.setattr(
        "pyhmmer_search.visibility.is_species_enabled",
        lambda acronym: str(acronym).upper() in {"BU", "PV"},
    )

    hits = visible_hits(
        [
            {"target": "BU_ATCC8492_00001"},
            {"target": "BF_NCTC9343_00002"},
            {"target": "PV_ATCC8482_00003"},
        ]
    )

    assert [hit["target"] for hit in hits] == [
        "BU_ATCC8492_00001",
        "PV_ATCC8482_00003",
    ]


def test_visible_hits_stay_unchanged_when_no_species_are_registered(monkeypatch):
    monkeypatch.setattr(
        "pyhmmer_search.visibility.get_enabled_species_acronyms",
        lambda: set(),
    )
    hits = [{"target": "BF_NCTC9343_00002"}]

    assert visible_hits(hits) == hits


def test_empty_search_uses_the_enabled_species(monkeypatch):
    monkeypatch.setattr(
        "pyhmmer_search.visibility.get_enabled_species_acronyms",
        lambda: {"BU", "PV"},
    )
    monkeypatch.setattr(
        "pyhmmer_search.visibility.resolve_enabled_species",
        lambda requested: ["BU", "PV"] if not requested else [],
    )

    assert limit_search_species([]) == ["BU", "PV"]
    assert limit_search_species(["BF"]) == []


def test_catalog_lists_only_enabled_species(monkeypatch):
    monkeypatch.setattr(
        "pyhmmer_search.visibility.get_enabled_species_acronyms",
        lambda: {"BU", "PV"},
    )
    monkeypatch.setattr(
        "pyhmmer_search.visibility.is_species_enabled",
        lambda acronym: str(acronym).upper() in {"BU", "PV"},
    )

    catalog = visible_catalog(
        {
            "species": [
                {"acronym": "BU", "name": "Bacteroides uniformis"},
                {"acronym": "BF", "name": "Bacteroides fragilis"},
                {"acronym": "PV", "name": "Phocaeicola vulgatus"},
            ],
            "shortcuts": [
                {"id": "all", "label": "All species", "species": []},
                {"id": "hd", "label": "B. uniformis + P. vulgatus", "species": ["BU", "PV"]},
                {"id": "bf", "label": "B. fragilis", "species": ["BF"]},
            ],
        }
    )

    assert [item["acronym"] for item in catalog["species"]] == ["BU", "PV"]
    assert catalog["shortcuts"] == [
        {"id": "all", "label": "All species", "species": []},
        {"id": "hd", "label": "B. uniformis + P. vulgatus", "species": ["BU", "PV"]},
    ]
