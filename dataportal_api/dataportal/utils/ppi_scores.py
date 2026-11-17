"""Rollups shared by the PPI importer and the Elasticsearch document."""

from typing import Dict

from dataportal.utils.constants import PPI_EVIDENCE_CATEGORIES


def apply_ppi_v4_rollups(src: Dict) -> None:
    """Set category presence flags and evidence_count from v4 scores and network counts."""
    for count_field, score_field, flag_field in PPI_EVIDENCE_CATEGORIES:
        count = src.get(count_field)
        score = src.get(score_field)
        src[flag_field] = bool((count or 0) > 0 or (score or 0) > 0)

    if src.get("n_evidence_types") is not None:
        src["evidence_count"] = int(src["n_evidence_types"])
    elif src.get("n_networks_total") is not None and not any(
        src.get(flag) for _, _, flag in PPI_EVIDENCE_CATEGORIES
    ):
        # Pre-v4 files only have a network total (formerly n_sources).
        src["evidence_count"] = int(src["n_networks_total"])
    else:
        src["evidence_count"] = sum(1 for _, _, flag in PPI_EVIDENCE_CATEGORIES if src.get(flag))
