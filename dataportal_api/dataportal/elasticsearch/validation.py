"""Compare a release's Elasticsearch counts against ReleaseManifest.expected_counts.

Manifest JSON uses underscore family keys (`feature_experiments`). Index families
use hyphens (`feature-experiments`). Both are accepted. `null` or omitted keys
are skipped. Feature-experiment `with_*` values are document (gene/feature) counts.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from elasticsearch.exceptions import NotFoundError

from dataportal.elasticsearch.names import (
    INDEX_FAMILIES,
    coerce_family,
    release_alias_name,
)

FAMILY_CHECK_KEYS: dict[str, frozenset[str]] = {
    "species": frozenset({"total", "enabled", "by_species"}),
    "strains": frozenset({"total", "by_species", "type_strains"}),
    "strain-experiments": frozenset({"total", "with_mic", "with_metabolism", "by_species"}),
    "features": frozenset({"total", "genes", "by_species", "with_essentiality", "with_string"}),
    "feature-experiments": frozenset(
        {
            "total",
            "by_species",
            "with_fitness",
            "with_proteomics",
            "with_mutant_growth",
            "with_pooled_ttp",
            "with_gene_rx",
            "with_met_rx",
            "with_gpr",
        }
    ),
    "ppi": frozenset({"total", "by_species"}),
    "operons": frozenset({"total", "by_species"}),
    "orthologs": frozenset({"total", "by_species"}),
    "fitness-correlations": frozenset({"total", "by_species"}),
}

_TERMS_SIZE = 100


def manifest_family_key(family: str) -> str:
    return coerce_family(family).replace("-", "_")


def _skip_value(value: Any) -> bool:
    return value is None


def _nested_exists(path: str, field: Optional[str] = None) -> dict:
    return {
        "nested": {
            "path": path,
            "query": {"exists": {"field": field or path}},
        }
    }


def _filter_agg(query: dict, sub: Optional[dict] = None) -> dict:
    agg: dict[str, Any] = {"filter": query}
    if sub:
        agg["aggs"] = sub
    return agg


def _terms_agg(field: str) -> dict:
    return {"terms": {"field": field, "size": _TERMS_SIZE}}


def _hit_total(resp: dict) -> int:
    hits = (resp or {}).get("hits") or {}
    total = hits.get("total")
    if isinstance(total, dict):
        return int(total.get("value") or 0)
    if total is None:
        return 0
    return int(total)


def _bucket_map(agg: Optional[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for bucket in (agg or {}).get("buckets") or []:
        key = str(bucket.get("key") or "").strip().lower()
        if key:
            out[key] = int(bucket.get("doc_count") or 0)
    return out


def _filter_count(agg: Optional[dict]) -> int:
    if not agg:
        return 0
    return int(agg.get("doc_count") or 0)


def _search(index: str, *, query: Optional[dict] = None, aggs: Optional[dict] = None) -> dict:
    from dataportal.elasticsearch.release_ops import _as_dict, _es

    es = _es()
    body: dict[str, Any] = {
        "size": 0,
        "track_total_hits": True,
        "query": query or {"match_all": {}},
    }
    if aggs:
        body["aggs"] = aggs
    try:
        return _as_dict(es.search(index=index, body=body))
    except TypeError:
        kwargs: dict[str, Any] = {
            "index": index,
            "size": 0,
            "track_total_hits": True,
            "query": body["query"],
        }
        if aggs:
            kwargs["aggregations"] = aggs
        return _as_dict(es.search(**kwargs))


def _aggs_for_family(family: str, expected_family: Optional[dict] = None) -> dict[str, Any]:
    if family == "species":
        return {
            "enabled": _filter_agg({"term": {"enabled": True}}),
            "by_species": _terms_agg("acronym"),
        }
    if family == "strains":
        return {
            "by_species": _terms_agg("species_acronym"),
            "type_strains": _filter_agg(
                {"term": {"type_strain": True}},
                {"by_species": _terms_agg("species_acronym")},
            ),
        }
    if family == "strain-experiments":
        return {
            "with_mic": _filter_agg(_nested_exists("drug_mic")),
            "with_metabolism": _filter_agg(_nested_exists("drug_metabolism")),
            "by_species": _terms_agg("species_acronym"),
        }
    if family == "features":
        gene = {"term": {"feature_type": "gene"}}
        return {
            "genes": _filter_agg(gene),
            "by_species_parent": _filter_agg(gene, {"by_species": _terms_agg("species_acronym")}),
            "with_essentiality": _filter_agg(
                {"bool": {"must": [gene, {"term": {"has_essentiality": True}}]}}
            ),
            "with_string": _filter_agg(
                {
                    "bool": {
                        "must": [
                            gene,
                            {
                                "nested": {
                                    "path": "dbxref",
                                    "query": {"term": {"dbxref.db": "STRING"}},
                                }
                            },
                        ]
                    }
                }
            ),
        }
    if family == "feature-experiments":
        gene = {"term": {"feature_type": "gene"}}
        return {
            "by_species": _terms_agg("species_acronym"),
            "with_fitness": _filter_agg(
                {"bool": {"must": [gene, {"term": {"has_fitness": True}}]}}
            ),
            "with_proteomics": _filter_agg(
                {"bool": {"must": [gene, {"term": {"has_proteomics": True}}]}}
            ),
            "with_mutant_growth": _filter_agg({"term": {"has_mutant_growth": True}}),
            "with_pooled_ttp": _filter_agg(_nested_exists("protein_compound")),
            "with_gene_rx": _filter_agg({"exists": {"field": "reactions"}}),
            "with_met_rx": _filter_agg(
                _nested_exists("reaction_details", "reaction_details.metabolites")
            ),
            "with_gpr": _filter_agg(_nested_exists("reaction_details", "reaction_details.gpr")),
        }
    if family in ("ppi", "operons", "fitness-correlations"):
        return {"by_species": _terms_agg("species_acronym")}
    if family == "orthologs":
        aggs: dict[str, Any] = {
            "by_species_a": _terms_agg("species_a_acronym"),
            "by_species_b": _terms_agg("species_b_acronym"),
        }
        wanted = _expected_species_keys((expected_family or {}).get("by_species"))
        if wanted:
            aggs["by_species"] = {
                "filters": {
                    "filters": {
                        acr: {
                            "bool": {
                                "should": [
                                    {"term": {"species_a_acronym": acr}},
                                    {"term": {"species_b_acronym": acr}},
                                ],
                                "minimum_should_match": 1,
                            }
                        }
                        for acr in wanted
                    }
                }
            }
        return aggs
    return {}


def _expected_species_keys(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    keys: list[str] = []
    for raw, expected in value.items():
        if _skip_value(expected):
            continue
        key = str(raw).strip().lower()
        if key:
            keys.append(key)
    return keys


def parse_family_counts(family: str, resp: dict) -> dict[str, Any]:
    """Turn one size=0 search response into the manifest-shaped counts dict."""
    aggs = (resp or {}).get("aggregations") or (resp or {}).get("aggs") or {}
    counts: dict[str, Any] = {"total": _hit_total(resp)}
    if family == "species":
        counts["enabled"] = _filter_count(aggs.get("enabled"))
        counts["by_species"] = _bucket_map(aggs.get("by_species"))
    elif family == "strains":
        counts["by_species"] = _bucket_map(aggs.get("by_species"))
        type_agg = aggs.get("type_strains") or {}
        counts["type_strains"] = _bucket_map(type_agg.get("by_species"))
    elif family == "strain-experiments":
        counts["with_mic"] = _filter_count(aggs.get("with_mic"))
        counts["with_metabolism"] = _filter_count(aggs.get("with_metabolism"))
        counts["by_species"] = _bucket_map(aggs.get("by_species"))
    elif family == "features":
        counts["genes"] = _filter_count(aggs.get("genes"))
        parent = aggs.get("by_species_parent") or {}
        counts["by_species"] = _bucket_map(parent.get("by_species"))
        counts["with_essentiality"] = _filter_count(aggs.get("with_essentiality"))
        counts["with_string"] = _filter_count(aggs.get("with_string"))
    elif family == "feature-experiments":
        counts["by_species"] = _bucket_map(aggs.get("by_species"))
        counts["with_fitness"] = _filter_count(aggs.get("with_fitness"))
        counts["with_proteomics"] = _filter_count(aggs.get("with_proteomics"))
        counts["with_mutant_growth"] = _filter_count(aggs.get("with_mutant_growth"))
        counts["with_pooled_ttp"] = _filter_count(aggs.get("with_pooled_ttp"))
        counts["with_gene_rx"] = _filter_count(aggs.get("with_gene_rx"))
        counts["with_met_rx"] = _filter_count(aggs.get("with_met_rx"))
        counts["with_gpr"] = _filter_count(aggs.get("with_gpr"))
    elif family in ("ppi", "operons", "fitness-correlations"):
        counts["by_species"] = _bucket_map(aggs.get("by_species"))
    elif family == "orthologs":
        counts["by_species_a"] = _bucket_map(aggs.get("by_species_a"))
        counts["by_species_b"] = _bucket_map(aggs.get("by_species_b"))
        by_species_agg = aggs.get("by_species")
        if by_species_agg and isinstance(by_species_agg.get("buckets"), dict):
            counts["by_species"] = {
                str(key).strip().lower(): int((bucket or {}).get("doc_count") or 0)
                for key, bucket in by_species_agg["buckets"].items()
            }
    return counts


def collect_family_counts(
    alias: str,
    family: str,
    *,
    expected_family: Optional[dict] = None,
) -> dict[str, Any]:
    from dataportal.elasticsearch.release_ops import resolve_concrete_indices

    concrete = resolve_concrete_indices(alias)
    meta = {"_alias": alias, "_physical": concrete}
    if not concrete:
        return {**meta, "error": f"alias '{alias}' does not resolve to a concrete index"}
    try:
        resp = _search(alias, aggs=_aggs_for_family(family, expected_family))
    except NotFoundError:
        return {**meta, "error": f"index '{alias}' not found"}
    except Exception as exc:
        return {**meta, "error": str(exc)}
    counts = parse_family_counts(family, resp)
    counts.update(meta)
    return counts


def collect_release_counts(
    release: str,
    *,
    families: Optional[Iterable[str]] = None,
    expected: Optional[dict] = None,
) -> dict[str, Any]:
    fams = [coerce_family(f) for f in (families or INDEX_FAMILIES)]
    expected = expected or {}
    actual: dict[str, Any] = {}
    for family in fams:
        key = manifest_family_key(family)
        expected_family = expected.get(key)
        if expected_family is None:
            expected_family = expected.get(family)
        if not isinstance(expected_family, dict):
            expected_family = None
        alias = release_alias_name(release, family)
        actual[key] = collect_family_counts(alias, family, expected_family=expected_family)
    return actual


def list_skipped_checks(
    expected: dict,
    *,
    families: Optional[Iterable[str]] = None,
) -> list[str]:
    allowed = None
    if families is not None:
        allowed = {manifest_family_key(f) for f in families}
        allowed |= {coerce_family(f) for f in families}
    skipped: list[str] = []
    for fam_key, fam_expected in (expected or {}).items():
        if (
            allowed is not None
            and fam_key not in allowed
            and manifest_family_key(fam_key) not in allowed
        ):
            continue
        if _skip_value(fam_expected):
            skipped.append(fam_key)
            continue
        if not isinstance(fam_expected, dict):
            continue
        for check, value in fam_expected.items():
            path = f"{manifest_family_key(fam_key)}.{check}"
            if _skip_value(value):
                skipped.append(path)
                continue
            if isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    if _skip_value(sub_val):
                        skipped.append(f"{path}.{str(sub_key).lower()}")
    return skipped


def compare_expected_counts(
    expected: dict,
    actual: dict,
    *,
    families: Optional[Iterable[str]] = None,
) -> list[dict[str, Any]]:
    """Return mismatch dicts: path, expected, actual, reason."""
    allowed = None
    if families is not None:
        allowed = {coerce_family(f) for f in families}

    mismatches: list[dict[str, Any]] = []
    for fam_key, fam_expected in (expected or {}).items():
        if _skip_value(fam_expected):
            continue
        try:
            family = coerce_family(fam_key)
        except Exception:
            mismatches.append(
                {
                    "path": str(fam_key),
                    "expected": fam_expected,
                    "actual": None,
                    "reason": "unknown family",
                }
            )
            continue
        if allowed is not None and family not in allowed:
            continue
        key = manifest_family_key(family)
        fam_actual = actual.get(key) or actual.get(family) or {}
        _compare_family(family, key, fam_expected, fam_actual, mismatches)
    return mismatches


def _compare_family(
    family: str,
    key: str,
    fam_expected: Any,
    fam_actual: dict,
    mismatches: list[dict[str, Any]],
) -> None:
    if not isinstance(fam_expected, dict):
        mismatches.append(
            {
                "path": key,
                "expected": fam_expected,
                "actual": fam_actual,
                "reason": "expected family value must be an object",
            }
        )
        return
    if fam_actual.get("error"):
        mismatches.append(
            {
                "path": key,
                "expected": fam_expected,
                "actual": fam_actual.get("error"),
                "reason": "index missing or unreadable",
            }
        )
        return
    known = FAMILY_CHECK_KEYS.get(family, frozenset())
    for check, exp_val in fam_expected.items():
        path = f"{key}.{check}"
        if _skip_value(exp_val):
            continue
        if known and check not in known:
            mismatches.append(
                {
                    "path": path,
                    "expected": exp_val,
                    "actual": None,
                    "reason": f"unknown check '{check}' for family {family}",
                }
            )
            continue
        actual_val = fam_actual.get(check)
        if isinstance(exp_val, dict):
            if not isinstance(actual_val, dict):
                mismatches.append(
                    {
                        "path": path,
                        "expected": exp_val,
                        "actual": actual_val,
                        "reason": "expected a species/key breakdown",
                    }
                )
                continue
            for sub_key, sub_exp in exp_val.items():
                if _skip_value(sub_exp):
                    continue
                sub_path = f"{path}.{str(sub_key).lower()}"
                sub_actual = actual_val.get(str(sub_key).strip().lower())
                if sub_actual is None:
                    sub_actual = 0
                _compare_int(sub_path, sub_exp, sub_actual, mismatches)
            continue
        _compare_int(path, exp_val, actual_val, mismatches)


def _compare_int(
    path: str,
    expected: Any,
    actual: Any,
    mismatches: list[dict[str, Any]],
) -> None:
    try:
        exp_n = int(expected)
    except (TypeError, ValueError):
        mismatches.append(
            {
                "path": path,
                "expected": expected,
                "actual": actual,
                "reason": "expected count must be an integer (or null to skip)",
            }
        )
        return
    try:
        act_n = int(actual)
    except (TypeError, ValueError):
        mismatches.append(
            {
                "path": path,
                "expected": exp_n,
                "actual": actual,
                "reason": "actual count missing or not an integer",
            }
        )
        return
    if exp_n != act_n:
        mismatches.append(
            {
                "path": path,
                "expected": exp_n,
                "actual": act_n,
                "reason": "count mismatch",
            }
        )
