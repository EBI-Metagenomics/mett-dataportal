from __future__ import annotations
import os, time, ftplib
from dataclasses import dataclass
from typing import Dict, List, Optional

from dataportal.models import StrainDocument
from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.utils import normalize_strain_id, species_name_for_isolate, strain_prefix
from dataportal.ingest.strain.resolver import StrainResolver  # ✅ add resolver
from .parsers import (
    ftp_connect,
    ftp_list_fasta,
    ftp_download,
    parse_fasta_contigs,
    ftp_list_gff_for_isolate,
    choose_primary_gff,
    ftp_build_isolate_folder_map,
)


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
    # Optional: separate GFF location
    gff_server: Optional[str] = None
    gff_base: Optional[str] = None
    # ✅ resolver for canonicalizing isolate ids
    resolver: Optional[StrainResolver] = None

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
        ftp_gff = None
        gff_folder_map = None

        # Open GFF FTP and build folder map once (if configured)
        if self.gff_server and self.gff_base:
            try:
                ftp_gff = self._connect_gff()
                if ftp_gff:
                    gff_folder_map = ftp_build_isolate_folder_map(ftp_gff, self.gff_base)
            except ftplib.all_errors:
                ftp_gff = None
                gff_folder_map = None

        fasta_files = ftp_list_fasta(ftp, self.ftp_directory)

        # Normalize type_strains once so we compare apples-to-apples
        if self.type_strains is not None:
            norm_list = [normalize_strain_id(s) for s in (self.type_strains or [])]
            # If resolver is available, canonicalize them too
            if self.resolver:
                canon_list = []
                for s in norm_list:
                    cid, _ = self.resolver.canonicalize(s)
                    canon_list.append(cid)
                type_set = set(canon_list)
            else:
                type_set = set(norm_list)
        else:
            type_set = None  # means "do not modify type_strain"

        accession_counter = 1

        for file in fasta_files:
            assembly_name = os.path.splitext(file)[0]

            raw_isolate = self.assembly_to_isolate.get(file)
            if not raw_isolate:
                continue

            # normalize input isolate
            iso_norm = normalize_strain_id(raw_isolate)

            # ✅ resolve canonical id via resolver (prevents variant ids)
            if self.resolver:
                canonical_id, _ = self.resolver.canonicalize(iso_norm)
            else:
                canonical_id = iso_norm

            # species based on canonical id (prefix is the same BU/PV...)
            species_name = species_name_for_isolate(canonical_id)
            if not species_name:
                continue

            # Download FASTA and extract contigs
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

            # ✅ read existing by canonical id
            existing = self.repo.get(canonical_id)
            doc = existing or StrainDocument(meta={"id": canonical_id})

            # always update contigs & rollups
            doc.contigs = contigs
            doc.contig_count = len(contigs)
            doc.genome_size = sum(c["length"] for c in contigs) if contigs else None

            # core identity (idempotent) — always canonical
            doc.strain_id = canonical_id
            doc.isolate_name = canonical_id
            doc.assembly_name = assembly_name
            doc.assembly_accession = f"AA{accession_counter:05d}"
            accession_counter += 1
            doc.fasta_file = file
            # leave existing gff_file intact unless we find a new match below
            doc.species_scientific_name = species_name
            doc.species_acronym = strain_prefix(canonical_id)

            # only touch type_strain if list supplied
            if type_set is not None:
                doc.type_strain = canonical_id in type_set
            # else: preserve existing value

            # GFF filename lookup (via folder map + canonical id)
            if ftp_gff is not None:
                gffs = ftp_list_gff_for_isolate(
                    ftp_gff, self.gff_base, canonical_id, folder_map=gff_folder_map
                )
                chosen = choose_primary_gff(gffs)
                if chosen:
                    doc.gff_file = chosen  # filename only

            self.repo.save(doc)

        ftp.quit()
        if ftp_gff:
            ftp_gff.quit()
