from __future__ import annotations
from typing import Iterable, Tuple, Optional, List, Dict
import os
import pandas as pd
from Bio import SeqIO
import ftplib
import re

def _safe_float(x) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None

def read_mapping_tsv(path: str) -> Dict[str, str]:
    """TSV with columns: assembly, prefix"""
    df = pd.read_csv(path, sep="\t")
    return dict(zip(df["assembly"], df["prefix"]))

# -------- MIC & Metabolism CSVs --------

def iter_mic_rows(csv_paths: List[str], default_unit: str = "uM") -> Iterable[Tuple[str, dict]]:
    """
    Yields (strain, payload) from MIC CSVs with columns: Strain, Drug, relation, drug_conc_um
    """
    for p in csv_paths:
        if not p or not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        cols = {c.lower(): c for c in df.columns}
        for _, row in df.iterrows():
            yield str(row[cols.get("strain", "Strain")]).strip(), {
                "drug_name": str(row[cols.get("drug", "Drug")]).strip(),
                "relation": str(row[cols.get("relation", "relation")]).strip(),
                "mic_value": _safe_float(row[cols.get("drug_conc_um", "drug_conc_um")]),
                # "unit": default_unit,
            }

def iter_metabolism_rows(csv_paths: List[str]) -> Iterable[Tuple[str, dict]]:
    """
    Yields (strain, payload) from metabolism CSVs with columns: Strain, Drug, DEGR_PERC, PVAL, PFDR, Metabolizer
    """
    for p in csv_paths:
        if not p or not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        cols = {c.lower(): c for c in df.columns}
        for _, row in df.iterrows():
            yield str(row[cols.get("strain", "Strain")]).strip(), {
                "drug_name": str(row[cols.get("drug", "Drug")]).strip(),
                "degr_percent": _safe_float(row[cols.get("degr_perc", "DEGR_PERC")]),
                "pval": _safe_float(row[cols.get("pval", "PVAL")]),
                "fdr": _safe_float(row[cols.get("pfdr", "PFDR")]),
                "metabolizer_classification": (
                    str(row[cols.get("metabolizer", "Metabolizer")]).strip()
                    if (cols.get("metabolizer") or "Metabolizer" in df.columns) else None
                ),
            }

# -------- FTP helpers for strain/contigs --------

def ftp_connect(server: str) -> ftplib.FTP:
    ftp = ftplib.FTP(server)
    ftp.login()
    return ftp

def ftp_list_fasta(ftp: ftplib.FTP, directory: str) -> List[str]:
    ftp.cwd(directory)
    return [f for f in ftp.nlst() if f.endswith(".fa")]

def ftp_download(ftp: ftplib.FTP, remote: str, local: str) -> None:
    ftp.voidcmd("TYPE I")
    with open(local, "wb") as f:
        ftp.retrbinary(f"RETR " + remote, f.write)

def parse_fasta_contigs(local_path: str) -> List[dict]:
    out: List[dict] = []
    with open(local_path, "r") as fh:
        for record in SeqIO.parse(fh, "fasta"):
            out.append({"seq_id": record.id, "length": len(record.seq)})
    return out


def _folder_key(name: str) -> str:
    """Uppercase and remove underscores/hyphens/spaces for folder matching."""
    return re.sub(r"[_\-\s]", "", (name or "")).upper()

def ftp_list_children(ftp: ftplib.FTP, base: str) -> List[str]:
    """
    Return list of immediate child *names* (basenames) under base.
    We use `nlst(base)` and strip to basename.
    """
    try:
        entries = ftp.nlst(base)
    except Exception:
        return []
    # Some FTP servers may return full paths; reduce to basenames
    out = []
    for p in entries:
        # Ignore '.'/'..' if any
        name = os.path.basename(p.rstrip("/"))
        if name and name not in (".", ".."):
            out.append(name)
    return out

def ftp_build_isolate_folder_map(ftp: ftplib.FTP, gff_base: str) -> Dict[str, str]:
    """
    Build a map: folder_key -> actual folder name under gff_base.
    """
    children = ftp_list_children(ftp, gff_base.rstrip("/"))
    mapping: Dict[str, str] = {}
    for child in children:
        key = _folder_key(child)
        # first one wins; if duplicates exist (shouldn't), we keep the first
        mapping.setdefault(key, child)
    return mapping

def candidate_isolate_folder_names(isolate: str) -> List[str]:
    """
    Generate a few plausible folder name variants for an isolate:
    - original
    - replace '-' with '_' after first '_'
    - replace '_' with '-' after first '_'
    """
    if not isolate:
        return []
    iso = isolate.strip()
    variants = {iso}
    if "_" in iso:
        head, tail = iso.split("_", 1)
        variants.add(f"{head}_{tail.replace('-', '_')}")
        variants.add(f"{head}-{tail}")                  # first '_' -> '-', keep tail
        variants.add(f"{head}-{tail.replace('_', '-')}") # swap remaining '_' -> '-'
    # Also try global swaps as a last resort
    variants.add(iso.replace("-", "_"))
    variants.add(iso.replace("_", "-"))
    return list(variants)

def ftp_list_gff_for_isolate(
    ftp: ftplib.FTP,
    gff_base: str,
    isolate: str,
    folder_map: Optional[Dict[str, str]] = None,
) -> List[str]:
    """
    Return *file names only* for GFFs in the isolate folder under gff_base.
    Uses folder_map (if provided) to resolve underscore/hyphen variants.
    """
    # 1) resolve folder name
    folder_name: Optional[str] = None
    if folder_map:
        folder_name = folder_map.get(_folder_key(isolate))

    # 2) if not found, try variants
    candidates = []
    if folder_name:
        candidates = [folder_name]
    else:
        candidates = candidate_isolate_folder_names(isolate)

    # 3) try each candidate until one lists successfully
    for cand in candidates:
        gff_dir = f"{gff_base.rstrip('/')}/{cand}/functional_annotation/merged_gff"
        try:
            lst = ftp.nlst(gff_dir)
        except Exception:
            continue
        if not lst:
            continue
        # Return only filenames
        files = [os.path.basename(p) for p in lst if p.endswith(".gff")]
        if files:
            return files

    return []

def choose_primary_gff(gff_files: List[str]) -> Optional[str]:
    """Choose one GFF file name; prefer '*_annotations.gff', else first sorted."""
    if not gff_files:
        return None
    preferred = [f for f in gff_files if f.endswith("_annotations.gff")]
    return sorted(preferred or gff_files)[0]