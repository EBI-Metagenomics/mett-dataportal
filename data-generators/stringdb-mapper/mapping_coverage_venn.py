#!/usr/bin/env python3
"""
Mapping Coverage Venn Diagram Analysis

Quantifies STRING identifier mapping coverage for METT type strains.
Defines sets for a given strain:
  - METT proteins: All proteins in the METT type-strain FASTA
  - STRING proteins: All proteins for the same taxon in STRING
  - Successfully mapped: METT proteins that mapped to a STRING protein (via DIAMOND)

Usage:
  python mapping_coverage_venn.py --strain BU
  python mapping_coverage_venn.py --strain PV
  python mapping_coverage_venn.py --all

Output:
  - mapping_coverage_<strain>.json  : Structured data for downstream use
  - mapping_coverage_<strain>.tsv   : Summary table
  - venn_<strain>.png               : Venn diagram (if matplotlib-venn installed)
  - unmapped_mett_<strain>.txt      : METT IDs that failed to map (for verification)
  - unmatched_string_<strain>.txt   : STRING IDs not hit by any METT (for verification)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Strain configuration: strain_id -> (mett_faa, string_faa, raw_tsv)
STRAIN_CONFIG = {
    "BU": {
        "mett_faa": "mett-faa-files/bu_typestrains.faa",
        "string_faa": "bu820_string.faa",
        "raw_tsv": "output/raw/bu_to_string_raw.tsv",
        "taxon": 820,
        "species": "Bacteroides uniformis",
    },
    "PV": {
        "mett_faa": "mett-faa-files/pv_typestrains.faa",
        "string_faa": "pv435590_string.faa",
        "raw_tsv": "output/raw/pv_to_string_raw.tsv",
        "taxon": 435590,
        "species": "Bacteroides vulgatus",
    },
}


def parse_fasta_ids(fasta_path: Path) -> set[str]:
    """Extract sequence IDs from FASTA (header after '>', first whitespace-delimited token)."""
    ids: set[str] = set()
    with open(fasta_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith(">"):
                seq_id = line[1:].split()[0].strip()
                ids.add(seq_id)
    return ids


def parse_diamond_mapping(tsv_path: Path) -> tuple[set[str], set[str]]:
    """
    Parse DIAMOND raw output. Columns: qseqid, sseqid, ...
    Returns (mett_ids_that_mapped, string_ids_hit).
    """
    mett_mapped: set[str] = set()
    string_hit: set[str] = set()
    with open(tsv_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                mett_mapped.add(parts[0].strip())
                string_hit.add(parts[1].strip())
    return mett_mapped, string_hit


def compute_venn_sets(
    mett_ids: set[str],
    string_ids: set[str],
    mett_mapped: set[str],
    string_hit: set[str],
) -> dict:
    """
    Compute Venn diagram sets.
    - mett_only: METT proteins that did NOT map to STRING
    - string_only: STRING proteins that were NOT hit by any METT
    - mapped: METT proteins that successfully mapped (intersection for Venn)
    """
    mett_only = mett_ids - mett_mapped
    string_only = string_ids - string_hit
    mapped = mett_mapped  # successfully mapped METT proteins

    return {
        "mett_proteins": len(mett_ids),
        "string_proteins": len(string_ids),
        "successfully_mapped": len(mapped),
        "string_proteins_matched": len(
            string_hit
        ),  # unique STRING hit (many-to-one mapping)
        "mett_only_unmapped": len(mett_only),
        "string_only_unmatched": len(string_only),
        "mett_only_ids": sorted(mett_only),
        "string_only_ids": sorted(string_only),
        "mapped_mett_ids": sorted(mapped),
        "string_ids_hit": sorted(string_hit),
    }


def write_verification_files(
    out_dir: Path,
    strain: str,
    mett_only: set[str],
    string_only: set[str],
) -> None:
    """Write ID lists for manual cross-verification."""
    unmapped_path = out_dir / f"unmapped_mett_{strain}.txt"
    with open(unmapped_path, "w") as f:
        for _id in sorted(mett_only):
            f.write(f"{_id}\n")
    print(f"  Unmapped METT IDs: {unmapped_path} ({len(mett_only)} proteins)")

    unmatched_path = out_dir / f"unmatched_string_{strain}.txt"
    with open(unmatched_path, "w") as f:
        for _id in sorted(string_only):
            f.write(f"{_id}\n")
    print(f"  Unmatched STRING IDs: {unmatched_path} ({len(string_only)} proteins)")


def draw_venn(
    out_dir: Path,
    strain: str,
    mett_total: int,
    string_total: int,
    mett_mapped: int,
    string_matched: int,
    mett_only: int,
    string_only: int,
) -> Path | None:
    """Draw coverage bar chart (Venn is invalid: mapping is many-to-one)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (Install matplotlib to generate diagram)")
        print("    pip install matplotlib")
        return None

    fig, axes = plt.subplots(2, 1, figsize=(10, 6))

    # Panel 1: METT proteins (mapped | unmapped)
    ax1 = axes[0]
    ax1.barh(0, mett_mapped, color="#2ecc71", label=f"Mapped ({mett_mapped:,})")
    ax1.barh(
        0,
        mett_only,
        left=mett_mapped,
        color="#e74c3c",
        label=f"Unmapped ({mett_only:,})",
    )
    ax1.set_xlim(0, mett_total)
    ax1.set_yticks([0])
    ax1.set_yticklabels(["METT proteins"])
    ax1.set_xlabel("Count")
    ax1.set_title(
        f"METT: {mett_mapped:,} mapped + {mett_only:,} unmapped = {mett_total:,} total"
    )
    ax1.legend(loc="upper right")

    ax2 = axes[1]
    ax2.barh(0, string_matched, color="#3498db", label=f"Matched ({string_matched:,})")
    ax2.barh(
        0,
        string_only,
        left=string_matched,
        color="#95a5a6",
        label=f"Unmatched ({string_only:,})",
    )
    ax2.set_xlim(0, string_total)
    ax2.set_yticks([0])
    ax2.set_yticklabels(["STRING proteins"])
    ax2.set_xlabel("Count")
    ax2.set_title(
        f"STRING: {string_matched:,} matched + {string_only:,} unmatched = {string_total:,} total"
    )

    fig.suptitle(
        f"Mapping Coverage: {strain} — {mett_mapped:,} METT map to {string_matched:,} unique STRING",
        fontsize=11,
    )
    plt.tight_layout()
    out_path = out_dir / f"venn_{strain.lower()}.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Coverage diagram: {out_path}")
    return out_path


def run_strain(base_dir: Path, strain: str, draw: bool) -> dict:
    """Run analysis for one strain."""
    cfg = STRAIN_CONFIG[strain]
    mett_path = base_dir / cfg["mett_faa"]
    string_path = base_dir / cfg["string_faa"]
    tsv_path = base_dir / cfg["raw_tsv"]

    for p, name in [
        (mett_path, "METT FASTA"),
        (string_path, "STRING FASTA"),
        (tsv_path, "raw TSV"),
    ]:
        if not p.exists():
            print(f"Error: {name} not found: {p}", file=sys.stderr)
            sys.exit(1)

    mett_ids = parse_fasta_ids(mett_path)
    string_ids = parse_fasta_ids(string_path)
    mett_mapped, string_hit = parse_diamond_mapping(tsv_path)

    result = compute_venn_sets(mett_ids, string_ids, mett_mapped, string_hit)
    result["strain"] = strain
    result["taxon"] = cfg["taxon"]
    result["species"] = cfg["species"]

    mett_only = set(result["mett_only_ids"])
    string_only = set(result["string_only_ids"])

    out_dir = base_dir / "output" / "mapping_coverage"
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON (summary, no ID lists)
    json_path = out_dir / f"mapping_coverage_{strain}.json"
    json_out = {
        k: v
        for k, v in result.items()
        if k
        not in (
            "mett_only_ids",
            "string_only_ids",
            "mapped_mett_ids",
            "string_ids_hit",
        )
    }
    with open(json_path, "w") as f:
        json.dump(json_out, f, indent=2)
    # Full JSON with IDs (for debugging)
    with open(out_dir / f"mapping_coverage_{strain}_full.json", "w") as f:
        json.dump(result, f, indent=2)

    # TSV summary
    tsv_path_out = out_dir / f"mapping_coverage_{strain}.tsv"
    with open(tsv_path_out, "w") as f:
        f.write("set\tcount\tpercent_of_mett\n")
        f.write(f"METT_proteins\t{result['mett_proteins']}\t100.0\n")
        f.write(f"STRING_proteins\t{result['string_proteins']}\t-\n")
        pct = (
            100.0 * result["successfully_mapped"] / result["mett_proteins"]
            if result["mett_proteins"]
            else 0
        )
        f.write(f"successfully_mapped\t{result['successfully_mapped']}\t{pct:.2f}\n")
        pct2 = (
            100.0 * len(mett_only) / result["mett_proteins"]
            if result["mett_proteins"]
            else 0
        )
        f.write(f"mett_only_unmapped\t{len(mett_only)}\t{pct2:.2f}\n")
        f.write(f"string_proteins_matched\t{result['string_proteins_matched']}\t-\n")
        f.write(f"string_only_unmatched\t{len(string_only)}\t-\n")

    write_verification_files(out_dir, strain, mett_only, string_only)

    if draw:
        draw_venn(
            out_dir,
            strain,
            result["mett_proteins"],
            result["string_proteins"],
            result["successfully_mapped"],
            result["string_proteins_matched"],
            len(mett_only),
            len(string_only),
        )

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantify STRING mapping coverage and produce Venn diagram data"
    )
    parser.add_argument(
        "--strain",
        choices=list(STRAIN_CONFIG),
        help="Strain to analyze (BU or PV)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run for all configured strains",
    )
    parser.add_argument(
        "--no-venn",
        action="store_true",
        help="Skip Venn diagram generation (only produce data files)",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Base directory (default: script dir)",
    )
    args = parser.parse_args()

    if not args.strain and not args.all:
        parser.error("Specify --strain BU|PV or --all")

    strains = list(STRAIN_CONFIG) if args.all else [args.strain]
    draw = not args.no_venn

    for strain in strains:
        print(
            f"\n=== {strain} ({STRAIN_CONFIG[strain]['species']}, taxon {STRAIN_CONFIG[strain]['taxon']}) ==="
        )
        r = run_strain(args.base_dir, strain, draw)
        print(f"  METT proteins:        {r['mett_proteins']}")
        print(f"  STRING proteins:      {r['string_proteins']}")
        print(
            f"  Successfully mapped: {r['successfully_mapped']} ({100*r['successfully_mapped']/r['mett_proteins']:.1f}% of METT)"
        )
        print(f"  METT only (unmapped): {r['mett_only_unmapped']}")
        print(
            f"  STRING matched:      {r['string_proteins_matched']} ({100*r['string_proteins_matched']/r['string_proteins']:.1f}% of STRING)"
        )
        print(f"  STRING only:         {r['string_only_unmatched']}")
        print("  Output: output/mapping_coverage/")


if __name__ == "__main__":
    main()
