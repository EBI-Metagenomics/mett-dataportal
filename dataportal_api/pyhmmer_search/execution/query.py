"""Turn a job's FASTA text into a digitized PyHMMER query."""

from __future__ import annotations

from pyhmmer.easel import TextSequence

from .schemas import QuerySequence


def digitize_query(fasta_text: str, alphabet):
    """Parse the job FASTA and digitize it for the search alphabet."""
    parsed = QuerySequence.parse_fasta(fasta_text)
    digital = TextSequence(name=parsed.name.encode("utf-8"), sequence=parsed.sequence).digitize(
        alphabet
    )
    return parsed, digital
