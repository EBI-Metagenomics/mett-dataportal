#!/usr/bin/env python3
"""Prepare local mettannotator results for portal ingest.

Keeps only:
  <root>/<genome>/functional_annotation/merged_gff/<genome>_annotations.gff
  <root>/<genome>/functional_annotation/merged_gff/<genome>_annotations-orig.gff
  <root>/<genome>/functional_annotation/prokka/<genome>.faa

For each annotations GFF:
  1. Move the original to *_annotations-orig.gff (once)
  2. Write a new *_annotations.gff with:
       - ##FASTA (and sequence) truncated
       - a `gene` row copied from each CDS (CDS kept)
       - gene phase `.`; attributes/ID/locus_tag copied as-is; no Parent

Default is a dry run. Pass --apply to delete extras and rewrite GFFs.

  python prep_mettannotator.py
  python prep_mettannotator.py --apply
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _paths import METTANNOTATOR_OUT

ANNOTATIONS_DIR = Path("functional_annotation") / "merged_gff"
PROKKA_DIR = Path("functional_annotation") / "prokka"


def _locus_tag(attributes: str) -> str | None:
    for item in (attributes or "").split(";"):
        if item.startswith("locus_tag="):
            tag = item.split("=", 1)[1].strip()
            return tag or None
    return None


def rewrite_annotations_gff(text: str) -> tuple[str, dict]:
    """Drop ##FASTA and insert gene rows copied from CDS."""
    gene_loci: set[str] = set()
    feature_lines: list[str] = []
    fasta_truncated = False
    for line in text.splitlines(keepends=True):
        if line.startswith("##FASTA"):
            fasta_truncated = True
            break
        feature_lines.append(line)
        if line.startswith("#") or not line.strip():
            continue
        cols = line.rstrip("\n").split("\t")
        if len(cols) == 9 and cols[2] == "gene":
            tag = _locus_tag(cols[8])
            if tag:
                gene_loci.add(tag)

    existing = len(gene_loci)
    added = 0
    out: list[str] = []
    for line in feature_lines:
        if line.startswith("#") or not line.strip():
            out.append(line if line.endswith("\n") else line + "\n")
            continue
        cols = line.rstrip("\n").split("\t")
        if len(cols) == 9 and cols[2] == "CDS":
            tag = _locus_tag(cols[8])
            if tag and tag not in gene_loci:
                gene_cols = list(cols)
                gene_cols[2] = "gene"
                gene_cols[7] = "."
                out.append("\t".join(gene_cols) + "\n")
                gene_loci.add(tag)
                added += 1
        out.append(line if line.endswith("\n") else line + "\n")
    return "".join(out), {
        "existing_genes": existing,
        "added_genes": added,
        "fasta_truncated": fasta_truncated,
    }


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


def prepare_genome(root: Path, genome: str, apply: bool) -> dict:
    gff = annotations_gff_path(root, genome)
    orig = orig_gff_path(root, genome)
    stats = {
        "genome": genome,
        "skipped": False,
        "source": None,
        "existing_genes": 0,
        "added_genes": 0,
        "fasta_truncated": False,
    }
    source = orig if orig.exists() else gff
    if not source.exists():
        stats["skipped"] = True
        stats["reason"] = f"missing {gff.relative_to(root)}"
        return stats

    stats["source"] = str(source.relative_to(root))
    text = source.read_text(encoding="utf-8", errors="replace")
    rewritten, rewrite_stats = rewrite_annotations_gff(text)
    stats.update(rewrite_stats)
    if not apply:
        return stats

    orig.parent.mkdir(parents=True, exist_ok=True)
    if not orig.exists():
        shutil.move(str(gff), str(orig))
    orig.parent.joinpath(f"{genome}_annotations.gff").write_text(
        rewritten, encoding="utf-8"
    )
    return stats


def run(root: Path, apply: bool) -> int:
    if not root.is_dir():
        print(f"Root not found: {root}", file=sys.stderr)
        return 1

    genomes = list_genomes(root)
    extra = files_to_prune(root, genomes)
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[{mode}] root={root}")
    print(f"[{mode}] genomes={len(genomes)} extra_files={len(extra)}")

    for genome in genomes:
        stats = prepare_genome(root, genome, apply=apply)
        if stats["skipped"]:
            print(f"  skip {genome}: {stats.get('reason')}")
            continue
        print(
            f"  {genome}: source={stats['source']} "
            f"existing_genes={stats['existing_genes']} "
            f"added_genes={stats['added_genes']} "
            f"fasta_truncated={stats['fasta_truncated']}"
        )

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
        help="Rewrite GFFs and delete files outside the keep pattern",
    )
    args = parser.parse_args()
    return run(args.root.resolve(), apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
