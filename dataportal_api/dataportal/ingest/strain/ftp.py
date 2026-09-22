from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Sequence

import ftplib
from Bio import SeqIO

from dataportal.ingest.ftp_paths import (
    DEFAULT_FASTA_EXTENSIONS,
    DEFAULT_GFF_DIR_TEMPLATE,
    format_ftp_path,
    is_fasta_filename,
    template_has_isolate,
)


def ftp_connect(server: str) -> ftplib.FTP:
    ftp = ftplib.FTP(server)
    ftp.login()
    return ftp


def public_https_url(server: str, *parts: str) -> str:
    """Build a browser-facing HTTPS URL from an FTP host and path segments."""
    host = (
        server.strip()
        .removeprefix("https://")
        .removeprefix("http://")
        .removeprefix("ftp://")
        .strip("/")
    )
    chunks: List[str] = []
    for part in parts:
        if not part:
            continue
        chunks.extend(p for p in str(part).replace("\\", "/").split("/") if p)
    return "https://" + "/".join([host, *chunks])


def ftp_list_fasta(
    ftp: ftplib.FTP,
    directory: str,
    extensions: Sequence[str] = DEFAULT_FASTA_EXTENSIONS,
) -> List[str]:
    ftp.cwd(directory)
    return [f for f in ftp.nlst() if is_fasta_filename(f, extensions)]


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
    gff_dir_template: str = DEFAULT_GFF_DIR_TEMPLATE,
) -> List[str]:
    resolved = ftp_resolve_gff_for_isolate(
        ftp,
        gff_base,
        isolate,
        folder_map=folder_map,
        gff_dir_template=gff_dir_template,
    )
    return resolved[1] if resolved else []


def ftp_resolve_gff_for_isolate(
    ftp: ftplib.FTP,
    gff_base: str,
    isolate: str,
    folder_map: Optional[Dict[str, str]] = None,
    gff_dir_template: str = DEFAULT_GFF_DIR_TEMPLATE,
) -> Optional[tuple[str, List[str]]]:
    """Return (remote_dir, gff filenames) for the isolate, or None if missing."""
    template = gff_dir_template or DEFAULT_GFF_DIR_TEMPLATE
    if not template_has_isolate(template):
        candidates = [isolate]
    else:
        folder_name: Optional[str] = None
        if folder_map:
            folder_name = folder_map.get(_folder_key(isolate))
        candidates = (
            [folder_name] if folder_name else candidate_isolate_folder_names(isolate)
        )

    for cand in candidates:
        if not cand:
            continue
        gff_dir = format_ftp_path(template, base=gff_base, isolate=cand)
        try:
            lst = ftp.nlst(gff_dir)
        except Exception:
            continue
        if not lst:
            continue
        files = [os.path.basename(p) for p in lst if p.endswith(".gff")]
        if files:
            return gff_dir, files

    return None


def choose_primary_gff(gff_files: List[str]) -> Optional[str]:
    if not gff_files:
        return None
    preferred = [f for f in gff_files if f.endswith("_annotations.gff")]
    return sorted(preferred or gff_files)[0]
