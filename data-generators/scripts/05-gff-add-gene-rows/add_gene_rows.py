#!/usr/bin/env python3
"""Insert `gene` features for CDS-only GFFs (20HM / Prodigal-style).

Portal ingest reads only GFF rows with type `gene`. Published METT v1 files
already have both `gene` and `CDS`. 20HM merged GFFs currently have CDS only.

For each CDS whose locus_tag has no gene row yet, this writes a `gene` line
(same coordinates and attributes, phase `.`) immediately before that CDS.
Files that already have gene rows are copied unchanged.

Do not overwrite the FTP originals; write a local copy and point ingest at it.

  python add_gene_rows.py --input AR_VPI0990_annotations.gff --output out.gff
  python add_gene_rows.py --input-dir ./gffs --output-dir ../../data/generated/gff-with-genes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _paths import GFF_GENE_OUT


def _locus_tag(attributes: str) -> str | None:
    for item in (attributes or "").split(";"):
        if item.startswith("locus_tag="):
            tag = item.split("=", 1)[1].strip()
            return tag or None
    return None


def add_gene_rows(text: str) -> tuple[str, dict]:
    lines = text.splitlines(keepends=True)
    gene_loci: set[str] = set()
    for line in lines:
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
    for line in lines:
        if line.startswith("#") or not line.strip():
            out.append(line)
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
    return "".join(out), {"existing_genes": existing, "added_genes": added}


def _iter_gff_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.gff") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="Single GFF file")
    parser.add_argument("--output", type=Path, help="Output GFF (with --input)")
    parser.add_argument("--input-dir", type=Path, help="Directory of .gff files")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=GFF_GENE_OUT,
        help=f"Output directory (default: {GFF_GENE_OUT})",
    )
    args = parser.parse_args()

    if args.input:
        src = args.input
        dest = args.output or (args.output_dir / src.name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        text = src.read_text(encoding="utf-8", errors="replace")
        rewritten, stats = add_gene_rows(text)
        dest.write_text(rewritten, encoding="utf-8")
        print(
            f"{src.name}: existing_genes={stats['existing_genes']} added_genes={stats['added_genes']} -> {dest}"
        )
        return 0

    if args.input_dir:
        files = _iter_gff_files(args.input_dir)
        if not files:
            print(f"No .gff files under {args.input_dir}", file=sys.stderr)
            return 1
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for src in files:
            dest = args.output_dir / src.name
            text = src.read_text(encoding="utf-8", errors="replace")
            rewritten, stats = add_gene_rows(text)
            dest.write_text(rewritten, encoding="utf-8")
            print(
                f"{src.name}: existing_genes={stats['existing_genes']} "
                f"added_genes={stats['added_genes']} -> {dest}"
            )
        return 0

    parser.error("Provide --input or --input-dir")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
