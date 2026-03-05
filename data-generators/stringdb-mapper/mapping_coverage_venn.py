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
    mapped: int,
    mett_only: int,
    string_only: int,
) -> Path | None:
    """Draw Venn diagram using matplotlib-venn. Returns output path or None if lib missing."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib_venn import venn2
    except ImportError:
        print("  (Install matplotlib and matplotlib-venn to generate Venn diagram)")
        print("    pip install matplotlib matplotlib-venn")
        return None

    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    # venn2 expects (set_a, set_b) or counts as (ab, a, b) for 2-circle
    # We use: Set A = METT, Set B = STRING via mapping
    # Actually for "mapping coverage" we want:
    #   - Circle 1: METT proteins (total = mapped + mett_only)
    #   - Circle 2: STRING proteins (total = string_hit_count + string_only)
    #   - Overlap: Mapped METT proteins (they map TO string_ids)
    #
    # The overlap in a 2-set Venn: items in BOTH sets.
    # Here: "mapped" = METT proteins that found a STRING match.
    # So we have: METT = {mapped} ∪ {mett_only}, and STRING = {string_hit} ∪ {string_only}
    # The intersection METT ∩ STRING (conceptually, via mapping) = mapped.
    #
    # For venn2(subsets=(mapped, mett_only, string_only)):
    # Actually venn2 uses: (size_of_A_only, size_of_B_only, size_of_A_and_B)
    # So: (mett_only, string_only, mapped) - but wait, "mapped" is METT→STRING mapping count.
    # The two sets are:
    #   A = METT proteins
    #   B = STRING proteins that we care about for "coverage"
    #
    # Simpler interpretation for coverage report:
    #   Set A: METT proteins (mett_total)
    #   Set B: Successfully mapped METT proteins (mapped) - this is a SUBSET of A
    # That would be a contained circle. Not ideal.
    #
    # Better: Two circles
    #   Set A: METT proteome
    #   Set B: STRING proteome (for same taxon)
    #   Overlap: The "mapping" - i.e. METT proteins that mapped AND the STRING proteins they hit
    # The overlap size could be: mapped (count of METT that mapped). The STRING side could have
    # many-to-one (multiple METT→same STRING), so we use mapped for the intersection.
    #
    # For Venn2 with (|A-B|, |B-A|, |A∩B|):
    #   |A-B| = mett_only (METT not in overlap)
    #   |B-A| = string_only (STRING not in overlap)
    #   |A∩B| = mapped
    # So: venn2(subsets=(mett_only, string_only, mapped), set_labels=('METT proteins', 'STRING proteins'))
    venn2(
        subsets=(mett_only, string_only, mapped),
        set_labels=("METT proteins", "STRING proteins\n(same taxon)"),
        ax=ax,
    )
    ax.set_title(
        f"Mapping Coverage: {strain} ({mett_total} METT, {string_total} STRING)"
    )
    out_path = out_dir / f"venn_{strain.lower()}.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Venn diagram: {out_path}")
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
        f.write(f"string_only_unmatched\t{len(string_only)}\t-\n")

    write_verification_files(out_dir, strain, mett_only, string_only)

    if draw:
        draw_venn(
            out_dir,
            strain,
            result["mett_proteins"],
            result["string_proteins"],
            result["successfully_mapped"],
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
        print(f"  STRING only:         {r['string_only_unmatched']}")
        print("  Output: output/mapping_coverage/")


if __name__ == "__main__":
    main()
