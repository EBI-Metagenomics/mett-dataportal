"""Exact-sequence dedup across isolates, then write the search FASTA and members table."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from headers import Member, choose_representative, format_header
from plan import load_species

MEMBER_FIELDS = (
    "seq_id",
    "sha256",
    "species",
    "isolate",
    "locus_tag",
    "is_type",
    "product",
    "collection",
)


def load_chunks(directory: Path) -> list[Member]:
    members: list[Member] = []
    for path in sorted(directory.glob("*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            members.append(
                Member(
                    locus_tag=row["locus_tag"],
                    species=row["species"],
                    isolate=row["isolate"],
                    is_type=bool(row["is_type"]),
                    product=row.get("product") or "",
                    sequence=row["sequence"],
                    collection=row.get("collection") or "",
                )
            )
    return members


def group_members(members: list[Member]) -> dict[str, list[Member]]:
    grouped: dict[str, list[Member]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for member in members:
        key = (member.sequence, member.locus_tag)
        if key in seen:
            continue
        seen.add(key)
        grouped[member.sequence].append(member)
    return grouped


def write_database(members: list[Member], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    faa_path = out_dir / "mett_proteins.faa"
    members_path = out_dir / "members.tsv"
    grouped = group_members(members)

    with faa_path.open("w") as faa, members_path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=MEMBER_FIELDS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for sequence in sorted(
            grouped, key=lambda seq: choose_representative(grouped[seq]).locus_tag
        ):
            group = grouped[sequence]
            representative = choose_representative(group)
            header = format_header(representative, group)
            faa.write(f">{header}\n")
            for index in range(0, len(sequence), 60):
                faa.write(sequence[index : index + 60] + "\n")
            for member in group:
                writer.writerow(
                    {
                        "seq_id": representative.locus_tag,
                        "sha256": hashlib.sha256(sequence.encode("ascii")).hexdigest(),
                        "species": member.species,
                        "isolate": member.isolate,
                        "locus_tag": member.locus_tag,
                        "is_type": "1" if member.is_type else "0",
                        "product": representative.product,
                        "collection": member.collection,
                    }
                )
    return faa_path, members_path


def write_catalog(members_path: Path, species_csv: Path, out_path: Path) -> None:
    species_info = load_species(species_csv) if species_csv.is_file() else {}
    counts: dict[str, dict] = {}
    with members_path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            acronym = row["species"]
            entry = counts.setdefault(
                acronym,
                {
                    "isolates": set(),
                    "type_strain": "",
                    "collection": row.get("collection") or "",
                },
            )
            entry["isolates"].add(row["isolate"])
            if row["is_type"] == "1" and not entry["type_strain"]:
                entry["type_strain"] = row["isolate"]
            if row.get("collection") == "hd":
                entry["collection"] = "hd"

    species_rows = []
    for acronym in sorted(counts):
        info = species_info.get(acronym, {})
        species_rows.append(
            {
                "acronym": acronym,
                "name": (info.get("scientific_name") or acronym).strip(),
                "isolates": len(counts[acronym]["isolates"]),
                "type_strain": counts[acronym]["type_strain"]
                or (info.get("type_strain_isolate") or ""),
                "collection": counts[acronym]["collection"],
            }
        )

    present = {row["acronym"] for row in species_rows}
    hd_species = [row["acronym"] for row in species_rows if row["collection"] == "hd"]
    catalog = {
        "id": "mett_proteins",
        "name": "METT proteins",
        "shortcuts": [
            {"id": "all", "label": "All species", "species": []},
            {
                "id": "hd",
                "label": _hd_label(species_rows),
                "species": hd_species,
            },
        ],
        "species": species_rows,
    }
    if not present:
        catalog["shortcuts"] = [catalog["shortcuts"][0]]
    out_path.write_text(json.dumps(catalog, indent=2) + "\n")


def _hd_label(species_rows: list[dict]) -> str:
    names = []
    for row in species_rows:
        if row["collection"] != "hd":
            continue
        parts = row["name"].split()
        if len(parts) >= 2:
            names.append(f"{parts[0][0]}. {parts[1]}")
        else:
            names.append(row["name"])
    return " + ".join(names) if names else "Flagship species"
