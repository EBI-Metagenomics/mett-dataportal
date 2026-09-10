from dataportal.elasticsearch.validation import (
    compare_expected_counts,
    list_skipped_checks,
    parse_family_counts,
)


def test_compare_skips_null_and_matches_ints():
    expected = {
        "species": {"total": 21, "enabled": 2},
        "strains": {"total": None, "by_species": {"bu": 59, "pv": None}},
    }
    actual = {
        "species": {"total": 21, "enabled": 2},
        "strains": {"total": 337, "by_species": {"bu": 59, "pv": 48}},
    }
    assert compare_expected_counts(expected, actual) == []


def test_compare_reports_mismatch_and_missing_bucket_as_zero():
    expected = {"species": {"total": 21}, "strains": {"by_species": {"bu": 59}}}
    actual = {"species": {"total": 20}, "strains": {"by_species": {}}}
    mismatches = compare_expected_counts(expected, actual)
    paths = {row["path"]: row for row in mismatches}
    assert paths["species.total"]["actual"] == 20
    assert paths["strains.by_species.bu"]["actual"] == 0
    assert paths["strains.by_species.bu"]["expected"] == 59


def test_compare_accepts_hyphen_family_keys_and_unknown_check():
    expected = {
        "feature-experiments": {"total": 10, "with_fitnes": 1},
    }
    actual = {"feature_experiments": {"total": 10, "with_fitness": 1}}
    mismatches = compare_expected_counts(expected, actual)
    assert mismatches[0]["path"] == "feature_experiments.with_fitnes"
    assert "unknown check" in mismatches[0]["reason"]


def test_compare_limits_to_requested_families():
    expected = {"species": {"total": 21}, "strains": {"total": 1}}
    actual = {"species": {"total": 21}, "strains": {"total": 99}}
    assert compare_expected_counts(expected, actual, families=["species"]) == []


def test_list_skipped_checks():
    expected = {
        "species": {"total": 21, "enabled": None},
        "strains": {"by_species": {"bu": None, "pv": 48}},
    }
    skipped = list_skipped_checks(expected)
    assert "species.enabled" in skipped
    assert "strains.by_species.bu" in skipped
    assert "species.total" not in skipped


def test_parse_species_and_feature_experiment_aggs():
    species = parse_family_counts(
        "species",
        {
            "hits": {"total": {"value": 21}},
            "aggregations": {
                "enabled": {"doc_count": 2},
                "by_species": {
                    "buckets": [
                        {"key": "BU", "doc_count": 1},
                        {"key": "PV", "doc_count": 1},
                    ]
                },
            },
        },
    )
    assert species["total"] == 21
    assert species["enabled"] == 2
    assert species["by_species"] == {"bu": 1, "pv": 1}

    feats = parse_family_counts(
        "feature-experiments",
        {
            "hits": {"total": 1254670},
            "aggregations": {
                "with_fitness": {"doc_count": 7151},
                "with_proteomics": {"doc_count": 10},
                "with_mutant_growth": {"doc_count": 0},
                "with_pooled_ttp": {"doc_count": 3},
                "with_gene_rx": {"doc_count": 4},
                "with_met_rx": {"doc_count": 5},
                "with_gpr": {"doc_count": 5},
                "by_species": {"buckets": [{"key": "bu", "doc_count": 100}]},
            },
        },
    )
    assert feats["total"] == 1254670
    assert feats["with_fitness"] == 7151
    assert feats["by_species"]["bu"] == 100


def test_parse_features_genes_and_type_strains():
    features = parse_family_counts(
        "features",
        {
            "hits": {"total": {"value": 648455}},
            "aggregations": {
                "genes": {"doc_count": 449621},
                "by_species_parent": {
                    "doc_count": 449621,
                    "by_species": {
                        "buckets": [
                            {"key": "bu", "doc_count": 235547},
                            {"key": "pv", "doc_count": 214074},
                        ]
                    },
                },
                "with_essentiality": {"doc_count": 8024},
                "with_string": {"doc_count": 7387},
            },
        },
    )
    assert features["genes"] == 449621
    assert features["by_species"]["pv"] == 214074
    assert features["with_string"] == 7387

    strains = parse_family_counts(
        "strains",
        {
            "hits": {"total": 337},
            "aggregations": {
                "by_species": {"buckets": [{"key": "bu", "doc_count": 200}]},
                "type_strains": {
                    "doc_count": 2,
                    "by_species": {
                        "buckets": [
                            {"key": "bu", "doc_count": 1},
                            {"key": "pv", "doc_count": 1},
                        ]
                    },
                },
            },
        },
    )
    assert strains["type_strains"] == {"bu": 1, "pv": 1}
