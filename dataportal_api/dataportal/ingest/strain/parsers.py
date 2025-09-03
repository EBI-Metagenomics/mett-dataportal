from __future__ import annotations
from typing import Dict, Iterable, List, Tuple, Optional
import os
import ftplib
import pandas as pd
from Bio import SeqIO

def read_mapping_tsv(path: str) -> Dict[str, str]:
    """TSV with columns: assembly, prefix"""
    df = pd.read_csv(path, sep="\t")
    return dict(zip(df["assembly"], df["prefix"]))

def iter_mic_rows(csv_paths: List[str]) -> Iterable[Tuple[str, dict]]:
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
                "unit": "uM",
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
                "metabolizer_classification": str(row[cols.get("metabolizer", "Metabolizer")]).strip()
                    if cols.get("metabolizer") or "Metabolizer" in df.columns else None,
            }

def ftp_list_fasta(ftp: ftplib.FTP, directory: str) -> List[str]:
    ftp.cwd(directory)
    return [f for f in ftp.nlst() if f.endswith(".fa")]

def ftp_download(ftp: ftplib.FTP, remote: str, local: str) -> None:
    ftp.voidcmd("TYPE I")
    with open(local, "wb") as f:
        ftp.retrbinary(f"RETR {remote}", f.write)

def parse_fasta_contigs(local_path: str) -> List[dict]:
    out = []
    with open(local_path, "r") as fh:
        for record in SeqIO.parse(fh, "fasta"):
            out.append({"seq_id": record.id, "length": len(record.seq)})
    return out

def _safe_float(x) -> Optional[float]:
    try:
        return float(x)
    except Exception:
        return None
