from pyhmmer_search.catalog import build_catalog


def test_catalog_groups_enabled_strains_by_species():
    catalog = build_catalog(
        [
            {
                "species_acronym": "bu",
                "species_scientific_name": "Bacteroides uniformis",
                "isolate_name": "BU_ATCC8492",
                "type_strain": True,
                "enabled": True,
            },
            {
                "species_acronym": "BU",
                "species_scientific_name": "Bacteroides uniformis",
                "isolate_name": "BU_61",
                "type_strain": False,
                "enabled": None,
            },
            {
                "species_acronym": "PV",
                "species_scientific_name": "Phocaeicola vulgatus",
                "isolate_name": "PV_ATCC8482",
                "type_strain": True,
                "enabled": True,
            },
            {
                "species_acronym": "BF",
                "species_scientific_name": "Bacteroides fragilis",
                "isolate_name": "BF_HIDDEN",
                "type_strain": True,
                "enabled": False,
            },
            {
                "species_acronym": "BF",
                "species_scientific_name": "Bacteroides fragilis",
                "isolate_name": "BF_NCTC9343",
                "type_strain": True,
                "enabled": True,
            },
        ]
    )

    assert catalog["id"] == "mett_proteins"
    assert [
        (item["acronym"], item["isolates"], item["type_strain"])
        for item in catalog["species"]
    ] == [
        ("BF", 1, "BF_NCTC9343"),
        ("BU", 2, "BU_ATCC8492"),
        ("PV", 1, "PV_ATCC8482"),
    ]
    assert catalog["shortcuts"][1]["species"] == ["BU", "PV"]


def test_catalog_without_strains_offers_only_all_species():
    catalog = build_catalog([])

    assert catalog["species"] == []
    assert catalog["shortcuts"] == [
        {"id": "all", "label": "All species", "species": []}
    ]
