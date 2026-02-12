#!/usr/bin/env python3
"""
Convert locus_tag→STRING raw DIAMOND output to UniProt→STRING mapping.

PPI data uses UniProt IDs; STRING mapping files use locus_tags. This script
joins the raw DIAMOND output with GFF-derived locus_tag→UniProt to produce
a mapping that PPI import can use directly.

Usage:
  # With local GFF file:
  python convert_to_uniprot_mapping.py \
    --raw-tsv output/bu_to_string_raw.tsv \
    --gff-file /path/to/merged_annotations.gff \
    --output output/bu_uniprot_to_string.tsv

  # Or download GFF from FTP (default: ftp.ebi.ac.uk):
  python convert_to_uniprot_mapping.py \
    --raw-tsv output/bu_to_string_raw.tsv \
    --download-gff BU_ATCC8492 \
    --output output/bu_uniprot_to_string.tsv

Then point PPI import at the output directory:
  --string-mapping-dir output/

The output TSV has columns: locus_tag, uniprot_id, string_protein_id
"""


import argparse
import csv
import ftplib
import sys
import tempfile
from pathlib import Path


def download_gff_from_ftp(isolate: str, ftp_server: str, ftp_directory: str) -> str:
    """Download GFF for isolate from FTP; return path to temp file."""
    isolate_path = (
        f"{ftp_directory.rstrip('/')}/{isolate}/functional_annotation/merged_gff/"
    )
    try:
        ftp = ftplib.FTP(ftp_server)
        ftp.login()
        ftp.cwd(isolate_path)
        files = ftp.nlst()
        gff_file = next((f for f in files if f.endswith("_annotations.gff")), None)
        if not gff_file:
            raise FileNotFoundError(f"No *_annotations.gff in {isolate_path}")
        local = tempfile.NamedTemporaryFile(mode="wb", suffix=".gff", delete=False)
        ftp.retrbinary(f"RETR {gff_file}", local.write)
        ftp.quit()
        local.close()
        return local.name
    except Exception as e:
        raise RuntimeError(f"Failed to download GFF for {isolate}: {e}") from e


def parse_gff_for_uniprot(gff_path: str) -> dict[str, str]:
    """Parse GFF and extract locus_tag → UniProt from Dbxref."""
    locus_to_uniprot: dict[str, str] = {}
    gff_path = Path(gff_path)
    if not gff_path.exists():
        print(f"Error: GFF file not found: {gff_path}", file=sys.stderr)
        return locus_to_uniprot

    with open(gff_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 9:
                continue
            if parts[2] != "gene":
                continue
            attrs = {}
            for item in parts[8].split(";"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    attrs[k.strip()] = v.strip()
            locus_tag = attrs.get("locus_tag")
            if not locus_tag:
                continue
            dbxref = attrs.get("Dbxref", "")
            uniprot_id = None
            for entry in dbxref.split(","):
                entry = entry.strip()
                if ":" in entry:
                    db, ref = entry.split(":", 1)
                    if db.strip() == "UniProt":
                        uniprot_id = ref.strip()
                        break
            if uniprot_id:
                locus_to_uniprot[locus_tag] = uniprot_id

    return locus_to_uniprot


def convert_raw_to_uniprot(
    raw_tsv: str,
    locus_to_uniprot: dict[str, str],
    output_path: str,
) -> int:
    """Read raw DIAMOND output (locus_tag, string_id) and write locus_tag, uniprot_id, string_protein_id.
    All rows are kept; uniprot_id is empty when not in GFF (e.g. some genes lack UniProt in Dbxref).
    """
    count = 0
    with open(raw_tsv, "r", encoding="utf-8", newline="") as fin:
        with open(output_path, "w", encoding="utf-8", newline="") as fout:
            writer = csv.writer(fout, delimiter="\t")
            writer.writerow(["locus_tag", "uniprot_id", "string_protein_id"])
            reader = csv.reader(fin, delimiter="\t")
            for row in reader:
                if len(row) < 2:
                    continue
                locus_tag = row[0].strip()
                string_id = row[1].strip()
                if not locus_tag or not string_id:
                    continue
                uniprot_id = locus_to_uniprot.get(locus_tag, "")
                writer.writerow([locus_tag, uniprot_id, string_id])
                count += 1
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Convert locus_tag→STRING raw output to UniProt→STRING mapping"
    )
    parser.add_argument(
        "--raw-tsv",
        required=True,
        help="Path to raw DIAMOND output (locus_tag, string_id, ...)",
    )
    gff_group = parser.add_mutually_exclusive_group(required=True)
    gff_group.add_argument(
        "--gff-file",
        help="Path to local GFF file with locus_tag and Dbxref (UniProt)",
    )
    gff_group.add_argument(
        "--download-gff",
        metavar="ISOLATE",
        help="Download GFF for isolate from FTP (e.g. BU_ATCC8492, PV_ATCC8482)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output TSV (uniprot_id, string_protein_id)",
    )
    parser.add_argument(
        "--ftp-server",
        default="ftp.ebi.ac.uk",
        help="FTP server for --download-gff (default: ftp.ebi.ac.uk)",
    )
    parser.add_argument(
        "--ftp-directory",
        default="/pub/databases/mett/annotations/v1_2024-04-15",
        help="FTP base directory for GFF (default: METT annotations)",
    )
    args = parser.parse_args()

    if args.download_gff:
        print(f"Downloading GFF for {args.download_gff} from {args.ftp_server}...")
        gff_path = download_gff_from_ftp(
            args.download_gff, args.ftp_server, args.ftp_directory
        )
        try:
            locus_to_uniprot = parse_gff_for_uniprot(gff_path)
        finally:
            Path(gff_path).unlink(missing_ok=True)
    else:
        locus_to_uniprot = parse_gff_for_uniprot(args.gff_file)
    if not locus_to_uniprot:
        print("Error: No locus_tag→UniProt mappings found in GFF", file=sys.stderr)
        sys.exit(1)
    print(f"Parsed {len(locus_to_uniprot)} locus_tag→UniProt from GFF")

    count = convert_raw_to_uniprot(
        args.raw_tsv,
        locus_to_uniprot,
        args.output,
    )
    print(f"Wrote {count} UniProt→STRING mappings to {args.output}")


if __name__ == "__main__":
    main()
