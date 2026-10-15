"""Convert PyHMMER and Biopython alignments into the schemas the UI stores."""

from __future__ import annotations

import logging
from typing import Optional

from Bio import pairwise2

from ..search.schemas import AlignmentDisplay, PyhmmerAlignmentSchema
from .alignment_math import AlignmentCalculator

logger = logging.getLogger(__name__)


def _text(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode()
    return str(value)


def extract_pyhmmer_alignment(alignment) -> Optional[PyhmmerAlignmentSchema]:
    if alignment is None:
        return None
    try:
        return PyhmmerAlignmentSchema(
            hmm_name=_text(alignment.hmm_name) or "",
            hmm_accession=_text(alignment.hmm_accession),
            hmm_from=alignment.hmm_from,
            hmm_to=alignment.hmm_to,
            hmm_length=getattr(alignment, "hmm_length", None),
            hmm_sequence=alignment.hmm_sequence,
            target_name=_text(alignment.target_name) or "",
            target_from=alignment.target_from,
            target_to=alignment.target_to,
            target_length=getattr(alignment, "target_length", None),
            target_sequence=alignment.target_sequence,
            identity_sequence=alignment.identity_sequence,
            posterior_probabilities=getattr(alignment, "posterior_probabilities", None),
        )
    except Exception as exc:
        logger.warning("Failed to extract pyhmmer alignment: %s", exc)
        return None


def create_simple_alignment_display(alignment) -> Optional[AlignmentDisplay]:
    if alignment is None:
        return None
    try:
        mline = AlignmentCalculator.create_match_line(
            alignment.hmm_sequence, alignment.target_sequence
        )
        (identity_pct, number_of_identical), (
            similarity_pct,
            number_of_identical_and_similar,
        ) = AlignmentCalculator.calculate_identity_and_similarity_from_match_line(
            alignment.hmm_sequence, mline, alignment.target_sequence
        )
        return AlignmentDisplay(
            hmmfrom=alignment.hmm_from,
            hmmto=alignment.hmm_to,
            sqfrom=alignment.target_from,
            sqto=alignment.target_to,
            model=alignment.hmm_sequence,
            aseq=alignment.target_sequence,
            mline=mline,
            ppline=getattr(alignment, "posterior_probabilities", None),
            identity=(identity_pct, number_of_identical),
            similarity=(similarity_pct, number_of_identical_and_similar),
        )
    except Exception as exc:
        logger.warning("Failed to create simple alignment display: %s", exc)
        return None


def parse_biopython_alignment(query: str, target: str) -> Optional[AlignmentDisplay]:
    """Pairwise alignment used when phmmer does not attach domain alignments."""
    try:
        pair = _align_pair(query, target)
        if pair is None:
            return None
        return _display_from_pair(*pair)
    except Exception as exc:
        logger.warning("Biopython alignment parsing failed: %s", exc)
        return None


def biopython_alignment_schema(query_name: str, query: str, target_name: str, target: str):
    """Full alignment record for a phmmer hit that has no domain alignment."""
    pair = _align_pair(query, target)
    if pair is None:
        return None, None
    aligned_query, aligned_target = pair
    detailed = PyhmmerAlignmentSchema(
        hmm_name=query_name,
        hmm_accession=None,
        hmm_from=1,
        hmm_to=len(query),
        hmm_length=len(query),
        hmm_sequence=aligned_query,
        target_name=target_name,
        target_from=1,
        target_to=len(target),
        target_length=len(target),
        target_sequence=aligned_target,
        identity_sequence=AlignmentCalculator.create_match_line(aligned_query, aligned_target),
        posterior_probabilities=None,
    )
    return detailed, _display_from_pair(aligned_query, aligned_target)


def _align_pair(query: str, target: str):
    alignments = pairwise2.align.globalxx(query, target)
    if not alignments:
        return None
    aligned_query, aligned_target, _score, _begin, _end = alignments[0]
    return aligned_query, aligned_target


def _display_from_pair(aligned_query: str, aligned_target: str) -> AlignmentDisplay:
    mline = AlignmentCalculator.create_match_line(aligned_query, aligned_target)
    (identity_pct, number_of_identical), (
        similarity_pct,
        number_of_identical_and_similar,
    ) = AlignmentCalculator.calculate_identity_and_similarity_from_sequences(
        aligned_query, aligned_target
    )
    return AlignmentDisplay(
        hmmfrom=_first_residue(aligned_query),
        hmmto=_last_residue(aligned_query),
        sqfrom=_first_residue(aligned_target),
        sqto=_last_residue(aligned_target),
        model=aligned_query,
        aseq=aligned_target,
        mline=mline,
        ppline=None,
        identity=(identity_pct, number_of_identical),
        similarity=(similarity_pct, number_of_identical_and_similar),
    )


def _first_residue(seq: str) -> int:
    for index, char in enumerate(seq):
        if char != "-":
            return index + 1
    return 1


def _last_residue(seq: str) -> int:
    for index in range(len(seq) - 1, -1, -1):
        if seq[index] != "-":
            return index + 1
    return len(seq)
