from dataportal.elasticsearch.names import (
    CURRENT_TOKEN,
    FAMILY_FEATURES,
    IndexNameError,
    coerce_family,
    current_alias_name,
    physical_index_name,
    release_alias_name,
)


def test_coerce_family_tokens_and_legacy_names():
    assert coerce_family("features") == FAMILY_FEATURES
    assert coerce_family("feature_index") == FAMILY_FEATURES
    assert coerce_family("strain-experiments") == "strain-experiments"
    assert coerce_family("strain_experiment_index") == "strain-experiments"
    assert coerce_family("fitness_correlation_index") == "fitness-correlations"


def test_resolve_read_index_current_vs_version(monkeypatch):
    from dataportal.elasticsearch import resolver

    monkeypatch.setattr(resolver, "_has_current_release", lambda: False)
    monkeypatch.setattr(resolver, "selected_release", lambda: "current")
    assert resolver.resolve_read_index("species") == "species_index"

    monkeypatch.setattr(resolver, "_has_current_release", lambda: True)
    assert resolver.resolve_read_index("species") == "mett-current-species"
    assert resolver.resolve_read_index("feature_index", release="v1") == "mett-v1-features"


def test_physical_and_alias_names():
    assert physical_index_name("v1", 1, "species") == "mett-v1-g001-species"
    assert physical_index_name("V2", 12, "feature_index") == "mett-v2-g012-features"
    assert release_alias_name("v1", "strains") == "mett-v1-strains"
    assert release_alias_name("current", "features") == "mett-current-features"
    assert current_alias_name("ppi") == "mett-current-ppi"


def test_current_is_not_a_physical_index():
    try:
        physical_index_name("current", 1, "species")
        assert False, "expected IndexNameError"
    except IndexNameError:
        pass


def test_invalid_release_and_family():
    try:
        release_alias_name("1.0", "species")
        assert False, "expected IndexNameError"
    except IndexNameError:
        pass
    try:
        coerce_family("unknown")
        assert False, "expected IndexNameError"
    except IndexNameError:
        pass
    assert CURRENT_TOKEN == "current"


def test_concrete_names_from_resolve_payload_follows_alias():
    from dataportal.elasticsearch.names import concrete_index_names_from_resolve

    alias_payload = {
        "indices": [
            {
                "name": "species_index-2025.09.03",
                "aliases": ["species_index"],
            }
        ],
        "aliases": [
            {
                "name": "species_index",
                "indices": ["species_index-2025.09.03"],
            }
        ],
    }
    assert concrete_index_names_from_resolve(alias_payload) == ["species_index-2025.09.03"]

    concrete_payload = {
        "indices": [{"name": "feature_index", "aliases": []}],
        "aliases": [],
    }
    assert concrete_index_names_from_resolve(concrete_payload) == ["feature_index"]
