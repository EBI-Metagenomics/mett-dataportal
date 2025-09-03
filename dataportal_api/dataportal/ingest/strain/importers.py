from __future__ import annotations
import ftplib, os, time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from dataportal.models import StrainDocument
from dataportal.ingest.es_repo import StrainIndexRepository
from dataportal.ingest.utils import (
    normalize_strain_id, species_name_for_isolate, strain_prefix
)
from .parsers import (
    read_mapping_tsv, ftp_list_fasta, ftp_download, parse_fasta_contigs,
    iter_mic_rows, iter_metabolism_rows
)

# ---------- Base ----------
class BaseImporter:
    def run(self):
        raise NotImplementedError

# ---------- Strain + Contigs via FTP ----------
@dataclass
class StrainContigImporter(BaseImporter):
    repo: StrainIndexRepository
    ftp_server: str
    ftp_directory: str
    assembly_to_isolate: Dict[str, str]
    type_strains: Optional[List[str]] = None

    def _connect(self) -> ftplib.FTP:
        retries = 3
        for i in range(retries):
            try:
                ftp = ftplib.FTP(self.ftp_server)
                ftp.login()
                return ftp
            except ftplib.all_errors:
                if i < retries - 1:
                    time.sleep(2)
                else:
                    raise

    def run(self):
        ftp = self._connect()
        fasta_files = ftp_list_fasta(ftp, self.ftp_directory)
        type_set = set(self.type_strains or [])
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

            # Download fasta
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

            doc = self.repo.get(isolate_name) or StrainDocument(meta={"id": isolate_name})
            doc.strain_id = isolate_name
            doc.isolate_name = isolate_name
            doc.assembly_name = assembly_name
            doc.assembly_accession = f"AA{accession_counter:05d}"
            accession_counter += 1
            doc.fasta_file = file
            # keep any existing gff_file if present
            doc.type_strain = isolate_name in type_set
            doc.species_scientific_name = species_name
            doc.species_acronym = strain_prefix(isolate_name)
            doc.contigs = contigs
            doc.contig_count = len(contigs)
            doc.genome_size = sum(c["length"] for c in contigs) if contigs else None

            self.repo.save(doc)
        ftp.quit()

# ---------- Drug MIC ----------
@dataclass
class DrugMICImporter(BaseImporter):
    repo: StrainIndexRepository
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None
    default_unit: str = "uM"

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        def key(it: dict):
            return (
                (it.get("drug_name") or "").lower(),
                it.get("relation"),
                round((it.get("mic_value") or 0.0), 6),
                it.get("unit"),
            )
        seen, out = set(), []
        for it in (existing or []) + new_items:
            k = key(it)
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out

    def run(self):
        by_strain: Dict[str, List[dict]] = {}
        for strain, payload in iter_mic_rows([self.bu_csv, self.pv_csv]):
            strain = normalize_strain_id(strain)
            if self.default_unit and "unit" not in payload:
                payload["unit"] = self.default_unit
            by_strain.setdefault(strain, []).append(payload)

        for strain, items in by_strain.items():
            doc = self.repo.get(strain) or StrainDocument(meta={"id": strain}, strain_id=strain, isolate_name=strain)
            existing = list(getattr(doc, "drug_mic", []) or [])
            doc.drug_mic = self._dedup(existing, items)
            self.repo.save(doc)

# ---------- Drug Metabolism ----------
@dataclass
class DrugMetabolismImporter(BaseImporter):
    repo: StrainIndexRepository
    bu_csv: Optional[str] = None
    pv_csv: Optional[str] = None
    significance_fdr: float = 0.05

    @staticmethod
    def _dedup(existing: List[dict], new_items: List[dict]) -> List[dict]:
        def nf(x): return None if x is None else round(float(x), 6)
        def key(it: dict):
            return (
                (it.get("drug_name") or "").lower(),
                nf(it.get("degr_percent")),
                nf(it.get("pval")),
                nf(it.get("fdr")),
                (it.get("metabolizer_classification") or "").lower()
                    if it.get("metabolizer_classification") else "",
            )
        seen, out = set(), []
        for it in (existing or []) + new_items:
            k = key(it)
            if k not in seen:
                seen.add(k)
                out.append(it)
        return out

    def run(self):
        by_strain: Dict[str, List[dict]] = {}
        for strain, payload in iter_metabolism_rows([self.bu_csv, self.pv_csv]):
            strain = normalize_strain_id(strain)
            fdr = payload.get("fdr")
            payload["is_significant"] = (fdr is not None and fdr < self.significance_fdr)
            by_strain.setdefault(strain, []).append(payload)

        for strain, items in by_strain.items():
            doc = self.repo.get(strain) or StrainDocument(meta={"id": strain}, strain_id=strain, isolate_name=strain)
            existing = list(getattr(doc, "drug_metabolism", []) or [])
            doc.drug_metabolism = self._dedup(existing, items)
            self.repo.save(doc)
