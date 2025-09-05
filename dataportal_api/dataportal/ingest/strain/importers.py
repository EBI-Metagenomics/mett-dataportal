from __future__ import annotations
import os, time, ftplib
from dataclasses import dataclass
from typing import Dict, List, Optional

from dataportal.models import StrainDocument
from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.utils import normalize_strain_id, species_name_for_isolate, strain_prefix
from .parsers import ftp_connect, ftp_list_fasta, ftp_download, parse_fasta_contigs, ftp_list_gff_for_isolate, \
    choose_primary_gff


class BaseImporter:
    def run(self):
        raise NotImplementedError

@dataclass
class StrainContigImporter(BaseImporter):
    repo: StrainIndexRepository
    ftp_server: str
    ftp_directory: str
    assembly_to_isolate: Dict[str, str]
    # If None => DO NOT modify type_strain; if [] => set all False; if list => set those True
    type_strains: Optional[List[str]] = None
    # NEW: separate GFF location
    gff_server: Optional[str] = None
    gff_base: Optional[str] = None

    def _connect(self) -> ftplib.FTP:
        retries = 3
        for i in range(retries):
            try:
                return ftp_connect(self.ftp_server)
            except ftplib.all_errors:
                if i < retries - 1:
                    time.sleep(2)
                else:
                    raise

    def _connect_gff(self) -> Optional[ftplib.FTP]:
        if not self.gff_server or not self.gff_base:
            return None
        retries = 3
        for i in range(retries):
            try:
                return ftp_connect(self.gff_server)
            except ftplib.all_errors:
                if i < retries - 1:
                    time.sleep(2)
                else:
                    return None

    def run(self):
        ftp = self._connect()
        ftp_gff = self._connect_gff()
        fasta_files = ftp_list_fasta(ftp, self.ftp_directory)
        type_set = set(self.type_strains or []) if self.type_strains is not None else None
        accession_counter = 1

        for file in fasta_files:
            assembly_name = os.path.splitext(file)[0]
            isolate_name = self.assembly_to_isolate.get(file)
            if not isolate_name:
                continue
            isolate_name = normalize_strain_id(isolate_name)

            species_name = species_name_for_isolate(isolate_name)
            if not species_name:
                continue

            local = f"/tmp/{file}"
            try:
                ftp_download(ftp, file, local)
            except ftplib.all_errors:
                continue

            contigs = parse_fasta_contigs(local)
            try:
                os.remove(local)
            except OSError:
                pass

            existing = self.repo.get(isolate_name)
            doc = existing or StrainDocument(meta={"id": isolate_name})

            # always update contigs & rollups
            doc.contigs = contigs
            doc.contig_count = len(contigs)
            doc.genome_size = sum(c["length"] for c in contigs) if contigs else None

            # core identity (idempotent)
            doc.strain_id = isolate_name
            doc.isolate_name = isolate_name
            doc.assembly_name = assembly_name
            doc.assembly_accession = f"AA{accession_counter:05d}"; accession_counter += 1
            doc.fasta_file = file
            if not getattr(doc, "gff_file", None):
                doc.gff_file = None
            doc.species_scientific_name = species_name
            doc.species_acronym = strain_prefix(isolate_name)

            # only touch type_strain if list supplied
            if type_set is not None:
                doc.type_strain = isolate_name in type_set
            # else: preserve existing value

            if ftp_gff is not None:
                gffs = ftp_list_gff_for_isolate(ftp_gff, self.gff_base, isolate_name)
                chosen = choose_primary_gff(gffs)
                if chosen:
                    doc.gff_file = chosen

            self.repo.save(doc)
        ftp.quit()
