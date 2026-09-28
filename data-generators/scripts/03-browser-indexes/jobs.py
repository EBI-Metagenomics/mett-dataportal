"""Resolve FASTA and GFF inputs into one index job per file.

HD assemblies and the 20hm batch share the annotation directory template.
They differ by root path, FASTA suffix (`.fa` vs `.fna`), and the assembly
filename, which is not always the isolate name. The mapping TSV is the
same file `import_strains --map-tsv` uses (`prefix` is the isolate).
"""

from __future__ import annotations

import csv
from pathlib import Path

DEFAULT_GFF_DIR_TEMPLATE = "{base}/{isolate}/functional_annotation/merged_gff"
JOB_FIELDS = (
    "kind",
    "isolate",
    "species",
    "assembly_folder",
    "release",
    "src",
)
_FASTA_SUFFIXES = (".gz", ".fasta", ".fna", ".fa")


def species_acronym(isolate: str) -> str:
    head, sep, _tail = isolate.partition("_")
    if not sep or not head:
        raise ValueError(f"Isolate {isolate!r} has no species prefix before '_'")
    return head


def assembly_folder_name(filename: str) -> str:
    """Folder the gene viewer requests: FASTA name without .fa/.fna/.fasta/.gz."""
    name = Path(filename).name
    changed = True
    while changed and name:
        changed = False
        lower = name.lower()
        for suffix in _FASTA_SUFFIXES:
            if lower.endswith(suffix):
                name = name[: -len(suffix)]
                changed = True
                break
    if not name:
        raise ValueError(f"Cannot derive an assembly folder from {filename!r}")
    return name


def load_mapping(path: Path) -> list[tuple[str, str]]:
    """Return (isolate, assembly filename) rows from a prefix/assembly TSV."""
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or not {"prefix", "assembly"} <= set(
            reader.fieldnames
        ):
            raise ValueError(f"{path} must be a TSV with columns: prefix, assembly")
        rows: list[tuple[str, str]] = []
        for row in reader:
            isolate = (row.get("prefix") or "").strip()
            assembly = (row.get("assembly") or "").strip()
            if not isolate or not assembly or isolate.startswith("#"):
                continue
            rows.append((isolate, assembly))
    if not rows:
        raise ValueError(f"No isolate rows in {path}")
    return rows


def candidate_isolate_names(isolate: str) -> list[str]:
    """Folder names to try when hyphens and underscores differ from the TSV."""
    iso = isolate.strip()
    names = [iso]
    if "_" in iso:
        head, tail = iso.split("_", 1)
        names.extend(
            [
                f"{head}_{tail.replace('-', '_')}",
                f"{head}-{tail}",
                f"{head}-{tail.replace('_', '-')}",
            ]
        )
    names.extend([iso.replace("-", "_"), iso.replace("_", "-")])
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def gff_dir(base: Path, isolate: str, template: str = DEFAULT_GFF_DIR_TEMPLATE) -> Path:
    rendered = template.format(base=str(base).rstrip("/"), isolate=isolate)
    return Path(rendered)


def is_primary_annotations_gff(name: str) -> bool:
    base = Path(name).name
    return (
        base.endswith("_annotations.gff")
        and "with_descriptions" not in base
        and not base.endswith("_annotations-orig.gff")
    )


def find_fasta(fasta_dir: Path, assembly: str) -> Path | None:
    path = fasta_dir / assembly
    return path if path.is_file() else None


def find_gff(
    gff_base: Path,
    isolate: str,
    template: str = DEFAULT_GFF_DIR_TEMPLATE,
) -> Path | None:
    for folder in candidate_isolate_names(isolate):
        directory = gff_dir(gff_base, folder, template)
        if not directory.is_dir():
            continue
        matches = sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and is_primary_annotations_gff(path.name)
        )
        preferred = f"{folder}_annotations.gff"
        for path in matches:
            if path.name == preferred:
                return path
        if matches:
            return matches[0]
    return None


def parse_isolates(
    values: list[str] | None, isolates_file: Path | None
) -> set[str] | None:
    names: list[str] = []
    for value in values or []:
        names.extend(
            part.strip() for part in value.replace(",", " ").split() if part.strip()
        )
    if isolates_file is not None:
        text = isolates_file.read_text()
        names.extend(
            part.strip() for part in text.replace(",", " ").split() if part.strip()
        )
    if not names:
        return None
    return set(names)


def plan_jobs(
    *,
    map_tsv: Path,
    fasta_dir: Path | None,
    gff_base: Path | None,
    release: str,
    gff_dir_template: str = DEFAULT_GFF_DIR_TEMPLATE,
    isolates: set[str] | None = None,
    only: str = "all",
    skip_missing: bool = False,
) -> list[dict[str, str]]:
    if only not in {"all", "fasta", "gff"}:
        raise ValueError("--only must be all, fasta, or gff")
    if only in {"all", "fasta"} and (fasta_dir is None or not fasta_dir.is_dir()):
        raise FileNotFoundError(f"FASTA directory not found: {fasta_dir}")
    if only in {"all", "gff"} and (gff_base is None or not gff_base.is_dir()):
        raise FileNotFoundError(f"GFF base directory not found: {gff_base}")

    jobs: list[dict[str, str]] = []
    missing: list[str] = []
    for isolate, assembly in load_mapping(map_tsv):
        if isolates is not None and isolate not in isolates:
            continue
        species = species_acronym(isolate)
        if only in {"all", "fasta"}:
            assert fasta_dir is not None
            fasta = find_fasta(fasta_dir, assembly)
            if fasta is None:
                missing.append(f"FASTA {fasta_dir / assembly}")
            else:
                jobs.append(
                    {
                        "kind": "fasta",
                        "isolate": isolate,
                        "species": species,
                        "assembly_folder": assembly_folder_name(assembly),
                        "release": release,
                        "src": str(fasta.resolve()),
                    }
                )
        if only in {"all", "gff"}:
            assert gff_base is not None
            gff = find_gff(gff_base, isolate, gff_dir_template)
            if gff is None:
                missing.append(
                    f"GFF for {isolate} under {gff_dir(gff_base, isolate, gff_dir_template)}"
                )
            else:
                jobs.append(
                    {
                        "kind": "gff",
                        "isolate": isolate,
                        "species": species,
                        "assembly_folder": "",
                        "release": release,
                        "src": str(gff.resolve()),
                    }
                )

    if missing and not skip_missing:
        detail = "\n".join(f"  - {item}" for item in missing)
        raise FileNotFoundError(f"Missing inputs:\n{detail}")
    if missing:
        for item in missing:
            print(f"Skipping missing input: {item}")
    if not jobs:
        raise FileNotFoundError("No index jobs matched the mapping and input paths")
    return jobs


def write_jobs(jobs: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=JOB_FIELDS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(jobs)
