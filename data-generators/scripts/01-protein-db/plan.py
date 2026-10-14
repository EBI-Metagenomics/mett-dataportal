"""Build the isolate manifest the rest of the pipeline reads."""

from __future__ import annotations

import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REFERENCE_DIR = SCRIPT_DIR.parents[1] / "data" / "reference"

FAA_TEMPLATE = "{root}/{isolate}/functional_annotation/prokka/{isolate}.faa"

BATCHES = {
    "hd": {
        "root": "/pub/databases/mett/annotations/v1_2024-04-15",
        "map_name": "gff-assembly-prefixes.tsv",
        "collection": "hd",
    },
    "20hm": {
        "root": "/pub/databases/metagenomics/temp/mett/20hm/v1/annotations",
        "map_name": "gff-assembly-prefixes-20hm.tsv",
        "collection": "20hm",
    },
}

SOURCE_FIELDS = (
    "isolate",
    "species",
    "faa",
    "type_strain",
    "collection",
    "scientific_name",
)


def load_species(path: Path) -> dict[str, dict[str, str]]:
    species: dict[str, dict[str, str]] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            acronym = (row.get("acronym") or "").strip()
            if acronym:
                species[acronym] = row
    return species


def load_isolates(path: Path) -> list[str]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames and "prefix" in reader.fieldnames:
            return [
                row["prefix"].strip()
                for row in reader
                if (row.get("prefix") or "").strip()
            ]
    isolates: list[str] = []
    for line in path.read_text().splitlines():
        isolate = line.split("\t", 1)[0].strip()
        if isolate and isolate.lower() != "prefix":
            isolates.append(isolate)
    return isolates


def faa_path(root: str, isolate: str, template: str = FAA_TEMPLATE) -> str:
    return template.format(root=root.rstrip("/"), isolate=isolate)


def plan_batches(
    batch_names: list[str],
    *,
    species_csv: Path,
    roots: dict[str, str] | None = None,
    maps: dict[str, Path] | None = None,
    template: str = FAA_TEMPLATE,
    skip_missing: bool = False,
) -> list[dict[str, str]]:
    species = load_species(species_csv)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for name in batch_names:
        if name not in BATCHES:
            known = ", ".join(BATCHES)
            raise ValueError(f"Unknown batch {name!r}. Choose from: {known}")
        spec = BATCHES[name]
        root = (roots or {}).get(name) or spec["root"]
        map_path = (maps or {}).get(name) or (REFERENCE_DIR / spec["map_name"])
        for isolate in load_isolates(map_path):
            if isolate in seen:
                continue
            seen.add(isolate)
            acronym = isolate.split("_", 1)[0]
            info = species.get(acronym, {})
            path = faa_path(root, isolate, template)
            if skip_missing and not Path(path).is_file():
                continue
            type_isolate = (info.get("type_strain_isolate") or "").strip()
            rows.append(
                {
                    "isolate": isolate,
                    "species": acronym,
                    "faa": path,
                    "type_strain": "true" if isolate == type_isolate else "false",
                    "collection": spec["collection"],
                    "scientific_name": (info.get("scientific_name") or "").strip(),
                }
            )
    return rows


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        missing = [
            field
            for field in ("isolate", "species", "faa", "type_strain")
            if field not in fields
        ]
        if missing:
            raise ValueError(f"Manifest is missing columns: {', '.join(missing)}")
        rows = []
        for row in reader:
            rows.append(
                {
                    "isolate": row["isolate"].strip(),
                    "species": row["species"].strip(),
                    "faa": row["faa"].strip(),
                    "type_strain": (
                        "true"
                        if row["type_strain"].strip().lower() == "true"
                        else "false"
                    ),
                    "collection": (row.get("collection") or "").strip(),
                    "scientific_name": (row.get("scientific_name") or "").strip(),
                }
            )
    return rows


def write_sources(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=SOURCE_FIELDS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
