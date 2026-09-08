"""Run annotation ingest into feature_index."""

from __future__ import annotations

import ftplib
from typing import Iterable, Optional

from dataportal.ingest.feature.essentiality import Essentiality
from dataportal.ingest.feature.external_dbxref import ExternalDBXRef
from dataportal.ingest.feature.gff_features import GFFGenes
from dataportal.ingest.utils import list_csv_files, read_tsv_mapping


def list_ftp_isolates(ftp_server: str, ftp_root: str) -> list[str]:
    ftp = ftplib.FTP(ftp_server)
    ftp.login()
    ftp.cwd(ftp_root)
    raw_isolates = [n for n in ftp.nlst() if not n.startswith(".")]
    ftp.quit()
    return raw_isolates


def ingest_gff_features(
    *,
    ftp_server: str,
    ftp_root: str,
    index_name: str,
    raw_isolates: Iterable[str],
    mapping: Optional[dict] = None,
) -> None:
    GFFGenes(
        ftp_server,
        ftp_root,
        index_name=index_name,
        mapping=mapping or {},
    ).run(raw_isolates=list(raw_isolates), norm_isolates=None)


def ingest_essentiality(index_name: str, essentiality_dir: Optional[str]) -> list[str]:
    files = list_csv_files(essentiality_dir)
    for csv_path in files:
        Essentiality(index_name=index_name).run(csv_path)
    return files


def ingest_dbxref(index_name: str, dbxref_dir: Optional[str], db_name: str = "STRING") -> list[str]:
    if not dbxref_dir:
        return []
    files = list_csv_files(dbxref_dir, exts=(".tsv", ".tab"))
    for tsv_path in files:
        ExternalDBXRef(index_name=index_name, db_name=db_name).run(tsv_path)
    return files


def load_assembly_mapping(mapping_task_file: Optional[str]) -> dict:
    if not mapping_task_file:
        return {}
    return read_tsv_mapping(
        mapping_task_file,
        key_col="prefix",
        val_col="assembly",
        strip_suffix=".fa",
    )
