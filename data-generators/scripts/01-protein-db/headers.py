"""Protein FASTA headers.

The sequence name is the representative locus tag (SSI key). Every other gene
that shares the sequence is listed in ``lt`` so a hit can still open the gene
viewer for each member.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    locus_tag: str
    species: str
    isolate: str
    is_type: bool
    product: str
    sequence: str
    collection: str = ""


def format_header(representative: Member, members: list[Member]) -> str:
    """One FASTA header line, without the leading '>'."""
    species = sorted({member.species for member in members})
    isolates = sorted({member.isolate for member in members})
    ordered = _member_order(representative, members)
    locus_tags = [member.locus_tag for member in ordered]
    product = _sanitize_product(representative.product)
    is_type = any(member.is_type for member in members)
    return (
        f"{representative.locus_tag} "
        f"sp={';'.join(species)} "
        f"st={';'.join(isolates)} "
        f"ty={1 if is_type else 0} "
        f"n={len(locus_tags)} "
        f"product={product} "
        f"lt={';'.join(locus_tags)}"
    )


def product_from_header(description: str) -> str:
    """Product text stored after ``product=`` and before ``lt=``."""
    match = re.search(r"product=(.*?)\s+lt=", description)
    if match:
        return match.group(1).strip()
    return description.strip()


def locus_tags_from_header(description: str) -> list[str]:
    match = re.search(r"\blt=(\S+)", description)
    if not match:
        return []
    return [tag for tag in match.group(1).split(";") if tag]


def choose_representative(members: list[Member]) -> Member:
    """Type-strain copy wins. Ties break on locus tag so the choice is stable."""

    def sort_key(member: Member) -> tuple[int, str]:
        return (0 if member.is_type else 1, member.locus_tag)

    return sorted(members, key=sort_key)[0]


def _member_order(representative: Member, members: list[Member]) -> list[Member]:
    rest = sorted(
        (member for member in members if member.locus_tag != representative.locus_tag),
        key=lambda member: member.locus_tag,
    )
    return [representative, *rest]


def _sanitize_product(product: str) -> str:
    cleaned = " ".join(product.replace("lt=", "lt ").split())
    return cleaned or "hypothetical protein"
