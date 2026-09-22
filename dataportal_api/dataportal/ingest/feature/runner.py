"""Run annotation ingest into feature_index."""

from __future__ import annotations

from typing import Iterable, Optional

from dataportal.ingest.feature.essentiality import Essentiality
from dataportal.ingest.feature.external_dbxref import ExternalDBXRef
from dataportal.ingest.feature.gff_features import GFFGenes
from dataportal.ingest.feature.sources import (
    ftp_connect,
    list_isolates_from_ftp_session,
)
from dataportal.ingest.ftp_paths import (
    DEFAULT_FAA_PATH_TEMPLATE,
    DEFAULT_GFF_DIR_TEMPLATE,
    strip_fasta_extension,
)
from dataportal.ingest.utils import list_csv_files, read_tsv_mapping


def list_ftp_isolates(ftp_server: str, ftp_root: str) -> list[str]:
    ftp = ftp_connect(ftp_server)
    try:
        return list_isolates_from_ftp_session(ftp, ftp_root)
    finally:
        try:
            ftp.quit()
        except Exception:
            try:
                ftp.close()
            except Exception:
                pass


def ingest_gff_features(
    *,
    ftp_server: str,
    ftp_root: str,
    index_name: str,
    raw_isolates: Iterable[str],
    mapping: Optional[dict] = None,
    gff_dir_template: str = DEFAULT_GFF_DIR_TEMPLATE,
    faa_path_template: str = DEFAULT_FAA_PATH_TEMPLATE,
    local_root: Optional[str] = None,
) -> None:
    GFFGenes(
        ftp_server,
        ftp_root,
        index_name=index_name,
        mapping=mapping or {},
        gff_dir_template=gff_dir_template,
        faa_path_template=faa_path_template,
        local_root=local_root,
    ).run(raw_isolates=list(raw_isolates), norm_isolates=None)


def ingest_essentiality(index_name: str, essentiality_dir: Optional[str]) -> list[str]:
    files = list_csv_files(essentiality_dir)
    for csv_path in files:
        Essentiality(index_name=index_name).run(csv_path)
    return files


def ingest_dbxref(
    index_name: str, dbxref_dir: Optional[str], db_name: str = "STRING"
) -> list[str]:
    if not dbxref_dir:
        return []
    files = list_csv_files(dbxref_dir, exts=(".tsv", ".tab"))
    for tsv_path in files:
        ExternalDBXRef(index_name=index_name, db_name=db_name).run(tsv_path)
    return files


def load_assembly_mapping(mapping_task_file: Optional[str]) -> dict:
    if not mapping_task_file:
        return {}
    mapping = read_tsv_mapping(
        mapping_task_file,
        key_col="prefix",
        val_col="assembly",
        strip_suffix="",
    )
    return {key: strip_fasta_extension(value) for key, value in mapping.items()}
