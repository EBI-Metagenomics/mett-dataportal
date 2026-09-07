from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

import ftplib
from Bio import SeqIO


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
        ftp.retrbinary("RETR " + remote, f.write)


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
    try:
        entries = ftp.nlst(base)
    except Exception:
        return []
    out = []
    for p in entries:
        name = os.path.basename(p.rstrip("/"))
        if name and name not in (".", ".."):
            out.append(name)
    return out


def ftp_build_isolate_folder_map(ftp: ftplib.FTP, gff_base: str) -> Dict[str, str]:
    children = ftp_list_children(ftp, gff_base.rstrip("/"))
    mapping: Dict[str, str] = {}
    for child in children:
        mapping.setdefault(_folder_key(child), child)
    return mapping


def candidate_isolate_folder_names(isolate: str) -> List[str]:
    if not isolate:
        return []
    iso = isolate.strip()
    variants = {iso}
    if "_" in iso:
        head, tail = iso.split("_", 1)
        variants.add(f"{head}_{tail.replace('-', '_')}")
        variants.add(f"{head}-{tail}")
        variants.add(f"{head}-{tail.replace('_', '-')}")
    variants.add(iso.replace("-", "_"))
    variants.add(iso.replace("_", "-"))
    return list(variants)


def ftp_list_gff_for_isolate(
    ftp: ftplib.FTP,
    gff_base: str,
    isolate: str,
    folder_map: Optional[Dict[str, str]] = None,
) -> List[str]:
    folder_name: Optional[str] = None
    if folder_map:
        folder_name = folder_map.get(_folder_key(isolate))

    if folder_name:
        candidates = [folder_name]
    else:
        candidates = candidate_isolate_folder_names(isolate)

    for cand in candidates:
        gff_dir = f"{gff_base.rstrip('/')}/{cand}/functional_annotation/merged_gff"
        try:
            lst = ftp.nlst(gff_dir)
        except Exception:
            continue
        if not lst:
            continue
        files = [os.path.basename(p) for p in lst if p.endswith(".gff")]
        if files:
            return files

    return []


def choose_primary_gff(gff_files: List[str]) -> Optional[str]:
    if not gff_files:
        return None
    preferred = [f for f in gff_files if f.endswith("_annotations.gff")]
    return sorted(preferred or gff_files)[0]
