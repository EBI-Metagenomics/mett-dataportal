from __future__ import annotations
from typing import Iterable, Tuple, Optional, List, Dict
import os
import pandas as pd
from Bio import SeqIO
import ftplib

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

def ftp_list_gff_for_isolate(ftp: ftplib.FTP, gff_base: str, isolate: str) -> List[str]:
    """
    Returns full remote paths for GFF files under:
      <gff_base>/<isolate>/functional_annotation/merged_gff/
    """
    gff_dir = f"{gff_base.rstrip('/')}/{isolate}/functional_annotation/merged_gff"
    try:
        lst = ftp.nlst(gff_dir)
    except Exception:
        return []
    return [p for p in lst if p.endswith(".gff")]

def choose_primary_gff(gff_paths: List[str]) -> str | None:
    """
    Choose one GFF per isolate; prefer '*_annotations.gff', else first sorted.
    """
    if not gff_paths:
        return None
    preferred = [p for p in gff_paths if p.endswith("_annotations.gff")]
    return sorted(preferred or gff_paths)[0]