"""Turn each PyHMMER sequence hit into one stored hit.

Identical proteins are one FASTA record. The row uses the representative
locus tag when that gene is in scope, otherwise the first member in scope.
Copying every member locus tag would count the same domains again for each
isolate.
"""

from __future__ import annotations

import logging
import re

from ..constants import DEFAULT_INC_E, DEFAULT_INC_T, THRESHOLD_BITSCORE
from ..membership import product_from_description
from ..search.schemas import DomainSchema, HitSchema
from .alignment import (
    biopython_alignment_schema,
    create_simple_alignment_display,
    extract_pyhmmer_alignment,
)
from .schemas import QuerySequence

logger = logging.getLogger(__name__)


def domain_is_significant(
    score: float,
    ievalue: float,
    *,
    threshold: str,
    inc_e: float | None,
    inc_t: float | None,
) -> bool:
    if threshold == THRESHOLD_BITSCORE:
        return score > (inc_t if inc_t is not None else DEFAULT_INC_T)
    return ievalue < (inc_e if inc_e is not None else DEFAULT_INC_E)


def hit_is_significant(
    hit, *, threshold: str, inc_e: float | None, inc_t: float | None
):
    if hasattr(hit, "included"):
        return hit.included
    return domain_is_significant(
        hit.score, hit.evalue, threshold=threshold, inc_e=inc_e, inc_t=inc_t
    )


def _bias(value, hit_name: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        logger.warning(
            "Could not convert bias value %s to float for hit %s", value, hit_name
        )
        return None


def _domain_from_pyhmmer(domain, *, threshold: str, inc_e, inc_t) -> DomainSchema:
    alignment = getattr(domain, "alignment", None)
    return DomainSchema(
        env_from=domain.env_from,
        env_to=domain.env_to,
        bitscore=domain.score,
        ievalue=domain.i_evalue,
        cevalue=getattr(domain, "c_evalue", None),
        bias=getattr(domain, "bias", None),
        strand=getattr(domain, "strand", None),
        is_significant=domain_is_significant(
            domain.score,
            domain.i_evalue,
            threshold=threshold,
            inc_e=inc_e,
            inc_t=inc_t,
        ),
        alignment=extract_pyhmmer_alignment(alignment),
        alignment_display=create_simple_alignment_display(alignment),
    )


def _domain_from_sequences(
    hit, query: QuerySequence, target_sequence: str, *, hit_significant
) -> DomainSchema:
    detailed, simple = biopython_alignment_schema(
        query.name, query.sequence, hit.name.decode(), target_sequence
    )
    return DomainSchema(
        env_from=getattr(hit, "envelope_from", None),
        env_to=getattr(hit, "envelope_to", None),
        bitscore=hit.score,
        ievalue=hit.evalue,
        cevalue=getattr(hit, "c_evalue", None),
        bias=getattr(hit, "bias", None),
        strand=None,
        is_significant=hit_significant,
        alignment=detailed,
        alignment_display=simple,
    )


def build_hits(
    hit_list,
    *,
    query: QuerySequence,
    target_sequences: dict,
    threshold: str,
    inc_e: float | None,
    inc_t: float | None,
    membership: dict | None,
) -> list[HitSchema]:
    """One row per distinct sequence. Domain counts stay on that row."""
    if not hit_list:
        return []

    results: list[HitSchema] = []
    for hit in hit_list:
        hit_significant = hit_is_significant(
            hit, threshold=threshold, inc_e=inc_e, inc_t=inc_t
        )
        domains = _domains_for_hit(
            hit,
            query=query,
            target_sequences=target_sequences,
            threshold=threshold,
            inc_e=inc_e,
            inc_t=inc_t,
            hit_significant=hit_significant,
        )
        significant_domains = sum(
            1
            for domain in domains
            if domain_is_significant(
                domain.bitscore,
                domain.ievalue,
                threshold=threshold,
                inc_e=inc_e,
                inc_t=inc_t,
            )
        )
        seq_id = hit.name.decode()
        member_info = membership.get(seq_id) if membership else None
        results.append(
            HitSchema(
                target=_target_in_scope(seq_id, member_info),
                seq_id=seq_id,
                description=_description(hit, member_info),
                evalue=f"{hit.evalue:.2e}",
                score=f"{hit.score:.2f}",
                sequence=_display_sequence(domains),
                bias=_bias(getattr(hit, "bias", None), seq_id),
                num_hits=len(domains),
                num_significant=significant_domains,
                is_significant=hit_significant,
                domains=domains,
            )
        )
    return results


def _target_in_scope(seq_id: str, member_info: dict | None) -> str:
    """Gene to open. Prefer the representative when the filter includes it."""
    if not member_info:
        return seq_id
    locus_tags = member_info.get("locus_tags") or []
    if seq_id in locus_tags or not locus_tags:
        return seq_id
    return locus_tags[0]


def _domains_for_hit(
    hit, *, query, target_sequences, threshold, inc_e, inc_t, hit_significant
):
    if getattr(hit, "domains", None):
        return [
            _domain_from_pyhmmer(domain, threshold=threshold, inc_e=inc_e, inc_t=inc_t)
            for domain in hit.domains
        ]
    target = target_sequences.get(hit.name.decode())
    if target is None:
        return [_fallback_domain(hit, hit_significant)]
    try:
        return [
            _domain_from_sequences(
                hit, query, str(target.sequence), hit_significant=hit_significant
            )
        ]
    except Exception as exc:
        logger.warning("Biopython alignment failed for %s: %s", hit.name.decode(), exc)
        return [_fallback_domain(hit, hit_significant)]


def _fallback_domain(hit, hit_significant) -> DomainSchema:
    return DomainSchema(
        env_from=getattr(hit, "envelope_from", None),
        env_to=getattr(hit, "envelope_to", None),
        bitscore=hit.score,
        ievalue=hit.evalue,
        cevalue=getattr(hit, "c_evalue", None),
        bias=getattr(hit, "bias", None),
        strand=None,
        is_significant=hit_significant,
    )


def _description(hit, member_info) -> str:
    text = hit.description.decode() if hit.description else ""
    text = re.sub(r"\s*\[.*\]$", "", text)
    if member_info and member_info.get("product"):
        return member_info["product"]
    if "product=" in text:
        return product_from_description(text)
    return text


def _display_sequence(domains: list[DomainSchema]) -> str | None:
    if (
        not domains
        or not domains[0].alignment
        or not domains[0].alignment.target_sequence
    ):
        return None
    return domains[0].alignment.target_sequence.replace("-", "")
