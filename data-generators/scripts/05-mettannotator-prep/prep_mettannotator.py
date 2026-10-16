#!/usr/bin/env python3
"""Prune a local mettannotator tree for portal ingest.

Gene rows and FASTA removal are already done by
prepare_gff_files.py (codon-slurm mettannotator scripts). This script
only deletes files outside the keep pattern:

  <root>/<genome>/functional_annotation/merged_gff/<genome>_annotations.gff
  <root>/<genome>/functional_annotation/merged_gff/<genome>_annotations-orig.gff
  <root>/<genome>/functional_annotation/prokka/<genome>.faa

Default is a dry run. Pass --apply to delete extras.

  python prep_mettannotator.py
  python prep_mettannotator.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _paths import METTANNOTATOR_OUT

ANNOTATIONS_DIR = Path("functional_annotation") / "merged_gff"
PROKKA_DIR = Path("functional_annotation") / "prokka"


def annotations_gff_path(root: Path, genome: str) -> Path:
    return root / genome / ANNOTATIONS_DIR / f"{genome}_annotations.gff"


def orig_gff_path(root: Path, genome: str) -> Path:
    return root / genome / ANNOTATIONS_DIR / f"{genome}_annotations-orig.gff"


def protein_faa_path(root: Path, genome: str) -> Path:
    return root / genome / PROKKA_DIR / f"{genome}.faa"


def list_genomes(root: Path) -> list[str]:
    return sorted(
        p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def keep_paths(root: Path, genomes: list[str]) -> set[Path]:
    keep: set[Path] = set()
    for genome in genomes:
        keep.add(annotations_gff_path(root, genome).resolve())
        keep.add(orig_gff_path(root, genome).resolve())
        keep.add(protein_faa_path(root, genome).resolve())
    return keep


def files_to_prune(root: Path, genomes: list[str]) -> list[Path]:
    keep = keep_paths(root, genomes)
    extra: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.resolve() not in keep:
            extra.append(path)
    return extra


def prune_empty_dirs(root: Path) -> list[Path]:
    removed: list[Path] = []
    dirs = sorted(
        (p for p in root.rglob("*") if p.is_dir()),
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for directory in dirs:
        if directory == root:
            continue
        try:
            next(directory.iterdir())
        except StopIteration:
            directory.rmdir()
            removed.append(directory)
    return removed


def run(root: Path, apply: bool) -> int:
    if not root.is_dir():
        print(f"Root not found: {root}", file=sys.stderr)
        return 1

    genomes = list_genomes(root)
    extra = files_to_prune(root, genomes)
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] root={root}")
    print(f"[{mode}] genomes={len(genomes)} extra_files={len(extra)}")

    for path in extra:
        rel = path.relative_to(root)
        if apply:
            path.unlink()
            print(f"  deleted {rel}")
        else:
            print(f"  would delete {rel}")

    if apply:
        for directory in prune_empty_dirs(root):
            print(f"  rmdir {directory.relative_to(root)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=METTANNOTATOR_OUT,
        help=f"mettannotator results root (default: {METTANNOTATOR_OUT})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete files outside the keep pattern",
    )
    args = parser.parse_args()
    return run(args.root.resolve(), apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
