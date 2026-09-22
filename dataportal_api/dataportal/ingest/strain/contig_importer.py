from __future__ import annotations
import os
import time
import ftplib
from dataclasses import dataclass
from typing import Dict, List, Optional

from dataportal.models import StrainDocument
from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.ftp_paths import (
    DEFAULT_FASTA_EXTENSIONS,
    DEFAULT_GFF_DIR_TEMPLATE,
    mapping_lookup,
)
from dataportal.ingest.utils import species_name_for_isolate, strain_prefix
from dataportal.ingest.strain.ftp import (
    choose_primary_gff,
    ftp_build_isolate_folder_map,
    ftp_connect,
    ftp_download,
    ftp_list_fasta,
    ftp_resolve_gff_for_isolate,
    parse_fasta_contigs,
    public_https_url,
)
from dataportal.ingest.strain.provenance import apply_annotation, isolate_allowed
from dataportal.ingest.strain.resolver import StrainResolver, isolate_lookup_key


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
    isolates: Optional[List[str]] = None
    annotation: Optional[dict] = None
    gff_dir_template: str = DEFAULT_GFF_DIR_TEMPLATE
    fasta_extensions: tuple = DEFAULT_FASTA_EXTENSIONS

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
                    gff_folder_map = ftp_build_isolate_folder_map(
                        ftp_gff, self.gff_base
                    )
            except ftplib.all_errors:
                ftp_gff = None
                gff_folder_map = None

        fasta_files = ftp_list_fasta(
            ftp, self.ftp_directory, extensions=self.fasta_extensions
        )
        skipped_unmapped = 0
        skipped_not_in_allowlist = 0
        allowlist = set(self.isolates) if self.isolates else None

        # Use raw type_strains without normalization
        if self.type_strains is not None:
            # If resolver is available, canonicalize them
            if self.resolver:
                canon_list = []
                for s in self.type_strains:
                    cid, _ = self.resolver.canonicalize(s)
                    canon_list.append(cid)
                type_set = set(canon_list)
            else:
                type_set = set(self.type_strains)
        else:
            type_set = None  # means "do not modify type_strain"

        accession_counter = 1

        for file in fasta_files:
            assembly_name = os.path.splitext(file)[0]

            raw_isolate = mapping_lookup(
                self.assembly_to_isolate, file, self.fasta_extensions
            )
            if not raw_isolate:
                skipped_unmapped += 1
                continue

            # Use raw isolate name directly
            isolate_name = raw_isolate

            # ✅ resolve canonical id via resolver (prevents variant ids)
            if self.resolver:
                canonical_id, _ = self.resolver.canonicalize(isolate_name)
            else:
                canonical_id = isolate_name

            if not isolate_allowed(isolate_name, allowlist, canonical_id):
                skipped_not_in_allowlist += 1
                continue

            # species based on canonical id (prefix is the same BU/PV...)
            species_acronym = strain_prefix(canonical_id)
            if not species_acronym:
                continue
            species_name = species_name_for_isolate(canonical_id) or ""

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
            doc.isolate_name = isolate_name  # Use raw isolate name
            doc.isolate_key = isolate_lookup_key(canonical_id)
            doc.assembly_name = assembly_name
            doc.assembly_accession = f"AA{accession_counter:05d}"
            accession_counter += 1
            doc.fasta_file = file
            doc.fasta_url = public_https_url(self.ftp_server, self.ftp_directory, file)
            # leave existing gff_file/gff_url intact unless we find a new match below
            doc.species_scientific_name = species_name
            doc.species_acronym = species_acronym

            # only touch type_strain if list supplied
            if type_set is not None:
                doc.type_strain = canonical_id in type_set
            # else: preserve existing value

            # GFF filename + public URL (via folder map + canonical id)
            if ftp_gff is not None:
                resolved = ftp_resolve_gff_for_isolate(
                    ftp_gff,
                    self.gff_base,
                    canonical_id,
                    folder_map=gff_folder_map,
                    gff_dir_template=self.gff_dir_template,
                )
                if resolved:
                    gff_dir, gffs = resolved
                    chosen = choose_primary_gff(gffs)
                    if chosen:
                        doc.gff_file = chosen
                        doc.gff_url = public_https_url(
                            self.gff_server or self.ftp_server, gff_dir, chosen
                        )

            apply_annotation(doc, self.annotation)

            self.repo.save(doc)

        print(
            f"[import_strains] FTP FASTA files={len(fasta_files)}, "
            f"imported={len(fasta_files) - skipped_unmapped - skipped_not_in_allowlist}, "
            f"skipped unmapped={skipped_unmapped} "
            f"(not in --map-tsv), skipped isolates filter={skipped_not_in_allowlist}"
        )
        ftp.quit()
        if ftp_gff:
            ftp_gff.quit()
