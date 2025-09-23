from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import csv

from django.utils.timezone import now

from dataportal.ingest.ppi.parsing import iter_ppi_rows
from dataportal.ingest.ppi.gff_parser import GFFParser
from dataportal.ingest.es_repo import PPIIndexRepository


# Keep helpers consistent with your model
def canonical_pair(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted([a, b]))


def build_pair_id(species_key: str, a: str, b: str) -> str:
    aa, bb = canonical_pair(a, b)
    return f"{species_key}:{aa}__{bb}"


def _species_key(species_name: Optional[str], species_map: Dict[str, str]) -> str:
    if species_name and species_name in species_map:
        return species_map[species_name]
    if species_name:
        parts = species_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
    return "NA"


def _flags_and_rollups(src: Dict) -> None:
    src["has_xlms"] = bool(src.get("xlms_peptides") or src.get("xlms_files"))
    src["has_string"] = src.get("string_score") is not None
    src["has_operon"] = src.get("operon_score") is not None
    src["has_ecocyc"] = src.get("ecocyc_score") is not None
    # src["has_experimental"] = any(
    #     src.get(k) is not None for k in [
    #         "melt_score", "perturbation_score", "abundance_score",
    #         "secondary_score", "bayesian_score", "tt_score", "ds_score"
    #     ]
    # )
    keys = ['ds_score', 'tt_score', 'perturbation_score', 'abundance_score',
            'melt_score', 'secondary_score', 'bayesian_score', 'string_score',
            'operon_score', 'ecocyc_score']
    # cnt = sum(1 for k in keys if src.get(k) is not None)
    # src["evidence_count"] = cnt

    # s = src.get("string_score")
    # if (s is not None and s >= 0.7) or cnt >= 4:
    #     src["confidence_bin"] = "high"
    # elif (s is not None and s >= 0.4) or cnt >= 2:
    #     src["confidence_bin"] = "medium"
    # else:
    #     src["confidence_bin"] = "low"


@dataclass
class PPICSVFlow:
    repo: PPIIndexRepository
    species_map: Dict[str, str]
    gff_parser: Optional[GFFParser] = None

    def _row_to_action(self, row: Dict) -> Optional[Dict]:
        a, b = row.get("protein_a"), row.get("protein_b")
        if not a or not b:
            return None

        sp_name = row.get("species")
        sp_key = _species_key(sp_name, self.species_map)

        aa, bb = canonical_pair(a, b)
        pair_id = build_pair_id(sp_key, aa, bb)

        src = {
            # identity
            "pair_id": pair_id,
            "species_scientific_name": sp_name,
            "species_acronym": sp_key,
            "protein_a": aa,
            "protein_b": bb,
            "participants": [a, b],
            "participants_sorted": [aa, bb],
            "is_self_interaction": (aa == bb),

            # scores
            "ds_score": row.get("ds_score"),
            "tt_score": row.get("tt_score"),
            "perturbation_score": row.get("perturbation_score"),
            "abundance_score": row.get("abundance_score"),
            "melt_score": row.get("melt_score"),
            "secondary_score": row.get("secondary_score"),
            "bayesian_score": row.get("bayesian_score"),
            "string_score": row.get("string_score"),
            "operon_score": row.get("operon_score"),
            "ecocyc_score": row.get("ecocyc_score"),

            # xlms
            "xlms_peptides": row.get("xlms_peptides"),
            "xlms_files": row.get("xlms_files"),
            
            # gene information for protein_a
            "protein_a_locus_tag": row.get("protein_a_locus_tag"),
            "protein_a_uniprot_id": row.get("protein_a_uniprot_id"),
            "protein_a_name": row.get("protein_a_name"),
            "protein_a_seqid": row.get("protein_a_seqid"),
            "protein_a_source": row.get("protein_a_source"),
            "protein_a_type": row.get("protein_a_type"),
            "protein_a_start": row.get("protein_a_start"),
            "protein_a_end": row.get("protein_a_end"),
            "protein_a_score": row.get("protein_a_score"),
            "protein_a_strand": row.get("protein_a_strand"),
            "protein_a_phase": row.get("protein_a_phase"),
            "protein_a_product": row.get("protein_a_product"),
            
            # gene information for protein_b
            "protein_b_locus_tag": row.get("protein_b_locus_tag"),
            "protein_b_uniprot_id": row.get("protein_b_uniprot_id"),
            "protein_b_name": row.get("protein_b_name"),
            "protein_b_seqid": row.get("protein_b_seqid"),
            "protein_b_source": row.get("protein_b_source"),
            "protein_b_type": row.get("protein_b_type"),
            "protein_b_start": row.get("protein_b_start"),
            "protein_b_end": row.get("protein_b_end"),
            "protein_b_score": row.get("protein_b_score"),
            "protein_b_strand": row.get("protein_b_strand"),
            "protein_b_phase": row.get("protein_b_phase"),
            "protein_b_product": row.get("protein_b_product"),
        }

        _flags_and_rollups(src)

        # For a fresh load, 'index' is fine (idempotent). Use 'create' if you want to error on dup IDs.
        return {
            "_op_type": "index",
            "_index": self.repo.concrete_index,
            "_id": pair_id,
            "_source": src,
        }

    def run(
            self,
            folder: str,
            pattern: str = "*.csv",
            batch_size: int = 5000,
            refresh: Optional[str | bool] = None,  # set "wait_for" at the end if needed
            log_every: int = 100_000,
            optimize_indexing: bool = True,
            refresh_every_rows: int | None = None,
            refresh_every_secs: float | None = None,
    ) -> int:
        """
        Stream CSVs and bulk-index in chunks. No Painless, no large in-memory merge.
        Returns number of actions indexed.
        """
        es = self.repo._conn()
        self.repo.ensure_index()
        
        # Pre-load GFF files if GFF parser is available
        if self.gff_parser:
            print("[ppi] Pre-loading GFF files...")
            # Set species mapping
            self.gff_parser.set_species_mapping(self.species_map)
            
            # Get unique species from CSV files
            species_list = self._get_unique_species_from_csvs(folder, pattern)
            if species_list:
                self.gff_parser.preload_gff_files(species_list)
                print(f"[ppi] Pre-loaded GFF files for {len(species_list)} species")
            else:
                print("[ppi] No species found in CSV files")

        # Optional: speed up big initial loads
        old_settings = {}
        if optimize_indexing:
            try:
                # capture current settings to restore later
                old = es.indices.get_settings(index=self.repo.concrete_index)
                cur = next(iter(old.values()))["settings"]["index"]
                old_settings["refresh_interval"] = cur.get("refresh_interval", "1s")
                old_settings["number_of_replicas"] = cur.get("number_of_replicas", "1")

                es.indices.put_settings(
                    index=self.repo.concrete_index,
                    body={"index": {"refresh_interval": "-1", "number_of_replicas": 0}},
                )
            except Exception as e:
                print(f"[ppi] warn: could not apply fast-index settings: {e}")

        buffer: List[Dict] = []
        total = 0

        try:
            for i, row in enumerate(iter_ppi_rows(folder, pattern, self.gff_parser), 1):
                act = self._row_to_action(row)
                if act is None:
                    continue
                buffer.append(act)

                if len(buffer) >= batch_size:
                    success, _ = self.repo.bulk_index(buffer, chunk_size=batch_size, refresh=None)
                    total += success
                    buffer.clear()
                    if log_every and (i % log_every == 0):
                        print(f"[ppi] processed rows: {i:,} | indexed: {total:,}")

                should_refresh = (
                        (refresh_every_rows is not None and rows_since_refresh >= refresh_every_rows) or
                        (refresh_every_secs is not None and now - last_refresh_ts >= refresh_every_secs)
                )
                if should_refresh:
                    self.repo.refresh()  # <- on-demand refresh
                    rows_since_refresh = 0
                    last_refresh_ts = now
                    print(f"[ppi] periodic refresh after {i:,} rows; total indexed: {total:,}")

            if buffer:
                success, _ = self.repo.bulk_index(buffer, chunk_size=batch_size, refresh=refresh)
                total += success
        finally:
            if optimize_indexing and old_settings:
                try:
                    es.indices.put_settings(
                        index=self.repo.concrete_index,
                        body={
                            "index": {
                                "refresh_interval": old_settings["refresh_interval"],
                                "number_of_replicas": old_settings["number_of_replicas"],
                            }
                        },
                    )
                    if refresh:
                        es.indices.refresh(index=self.repo.concrete_index)
                except Exception as e:
                    print(f"[ppi] warn: restore index settings failed: {e}")

        return total
    
    def _get_unique_species_from_csvs(self, folder: str, pattern: str) -> List[str]:
        """Get unique species from CSV files to pre-load GFF data."""
        import glob
        import os
        
        species_set = set()
        
        for path in sorted(glob.glob(os.path.join(folder, pattern))):
            try:
                with open(path, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        species = row.get("species")
                        if species and species.strip():
                            species_set.add(species.strip())
            except Exception as e:
                print(f"[ppi] Warning: Error reading CSV file {path}: {e}")
                continue
        
        return list(species_set)
