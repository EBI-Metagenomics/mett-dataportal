"""Resolve a search filter and look up member locus tags.

The FASTA holds one record per distinct sequence. ``members.sqlite`` lists every
locus tag that sequence belongs to, which is what the gene viewer link needs.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from .constants import ALIASES, ISOLATE_DB_PREFIX


def resolve_scope(
    database: str,
    species: list[str] | None,
    type_only: bool,
    isolate: str | None,
) -> tuple[list[str], bool, str]:
    """Return species acronyms, type-strain flag, and isolate id.

    An empty species list means every species. An isolate id limits the search
    to that genome, which is what the gene viewer uses.
    """
    chosen = [item.strip().upper() for item in (species or []) if item and str(item).strip()]
    isolate_id = (isolate or "").strip()
    if database.startswith(ISOLATE_DB_PREFIX):
        return [], False, database[len(ISOLATE_DB_PREFIX) :]
    if not chosen and not isolate_id and database in ALIASES:
        alias_species, alias_type, alias_isolate = ALIASES[database]
        return list(alias_species), alias_type, alias_isolate
    return chosen, bool(type_only), isolate_id


def product_from_description(description: str) -> str:
    match = re.search(r"product=(.*?)\s+lt=", description)
    if match:
        return match.group(1).strip()
    return description.strip()


def members_db_path(faa_path: str) -> Path:
    return Path(faa_path).with_name("members.sqlite")


def catalog_path(faa_path: str) -> Path:
    return Path(faa_path).with_name("catalog.json")


def members_for_scope(
    faa_path: str,
    species: list[str],
    type_only: bool,
    isolate: str,
) -> dict[str, dict] | None:
    """Map representative seq id to the locus tags in scope.

    ``None`` means the membership index is not on disk, so search should use
    every sequence in the FASTA and keep the representative name as the hit.
    """
    path = members_db_path(faa_path)
    if not path.is_file():
        return None

    clauses = []
    params: list[str] = []
    if species:
        placeholders = ",".join("?" for _ in species)
        clauses.append(f"species IN ({placeholders})")
        params.extend(species)
    if type_only:
        clauses.append("is_type = 1")
    if isolate:
        clauses.append("isolate = ?")
        params.append(isolate)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    grouped: dict[str, dict] = {}
    connection = sqlite3.connect(path)
    try:
        rows = connection.execute(
            f"""
            SELECT m.seq_id, m.locus_tag, s.product
            FROM members AS m
            JOIN sequences AS s ON s.seq_id = m.seq_id
            {where}
            ORDER BY m.seq_id, m.locus_tag
            """,
            params,
        )
        for seq_id, locus_tag, product in rows:
            entry = grouped.setdefault(seq_id, {"locus_tags": [], "product": product or ""})
            entry["locus_tags"].append(locus_tag)
    finally:
        connection.close()
    return grouped
