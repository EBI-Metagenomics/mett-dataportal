
from __future__ import annotations

import gc
from typing import Any, Dict, List, Optional
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.utils import canonical_pair_id
from dataportal.ingest.gff.parser import GFFParser

import pandas as pd


def _keys_map(cols) -> Dict[str, str]:
    return {str(c).lower().strip(): c for c in cols}


def _get(rec: Dict[str, Any], km: Dict[str, str], *names, default=None):
    for n in names:
        k = km.get(str(n).lower().strip())
        if k is not None:
            return rec.get(k, default)
    return default


def _split_locus_and_desc(cell: Any) -> tuple[str, str]:
    """
    Split "BU_61_00001 Chromosomal ..." -> ("BU_61_00001", "Chromosomal ...").
    If no space is found, returns (cell, "").
    """
    if cell is None:
        return "", ""
    s = str(cell).strip()
    if not s:
        return "", ""
    if " " in s:
        locus, desc = s.split(" ", 1)
        return locus.strip(), desc.strip()
    return s, ""


def _extract_species_from_locus(locus_tag: str) -> tuple[str, str, str]:
    """
    Extract species information from locus tag.
    Examples:
    - "BU_61_00001" -> ("BU", "Bacteroides uniformis", "BU_61")
    - "BU_909_00001" -> ("BU", "Bacteroides uniformis", "BU_909")
    - "BU_AN67_00004" -> ("BU", "Bacteroides uniformis", "BU_AN67")
    - "PV_CL11T00C01_02240" -> ("PV", "Phocaeicola vulgatus", "PV_CL11T00C01")
    - "PV_ATCC8482_00001" -> ("PV", "Phocaeicola vulgatus", "PV_ATCC8482")
    """
    if not locus_tag or "_" not in locus_tag:
        return "UNKNOWN", "Unknown species", "UNKNOWN"
    
    # Find the first underscore to get species acronym
    first_underscore = locus_tag.find("_")
    if first_underscore == -1:
        return "UNKNOWN", "Unknown species", "UNKNOWN"
    
    species_acronym = locus_tag[:first_underscore]
    
    # Find the second underscore to get isolate name
    second_underscore = locus_tag.find("_", first_underscore + 1)
    if second_underscore == -1:
        # No second underscore, use the whole thing after first underscore as isolate
        isolate = locus_tag
    else:
        # Extract isolate name (species_acronym + everything up to second underscore)
        isolate = locus_tag[:second_underscore]
    
    # Map acronyms to full species names
    species_map = {
        "BU": "Bacteroides uniformis",
        "PV": "Phocaeicola vulgatus",
    }
    
    species_name = species_map.get(species_acronym, f"Unknown {species_acronym}")
    return species_acronym, species_name, isolate


def _get_gene_info_for_locus(gff_parser: Optional[GFFParser], locus_tag: str) -> Optional[Dict[str, Any]]:
    """Get gene information from GFF parser for a given locus tag."""
    if not gff_parser or not locus_tag:
        return None
    
    # Extract species from locus tag
    species_acronym, species_name, isolate = _extract_species_from_locus(locus_tag)
    
    # Try to get gene info using the unique species name format
    unique_species_name = f"{species_name}_{isolate}"
    gene_info = gff_parser.get_gene_info(unique_species_name, locus_tag)
    if gene_info:
        return {
            "locus_tag": gene_info.locus_tag,
            "uniprot_id": gene_info.uniprot_id,
            "name": gene_info.name,
            "seqid": gene_info.seqid,
            "source": gene_info.source,
            "type": gene_info.type,
            "start": gene_info.start,
            "end": gene_info.end,
            "score": gene_info.score,
            "strand": gene_info.strand,
            "phase": gene_info.phase,
            "product": gene_info.product,
        }
    
    # If direct lookup fails, try to find the gene in the loaded GFF data
    # This handles cases where the locus tag is from a different isolate of the same species
    if hasattr(gff_parser, '_gene_cache'):
        for loaded_isolate, gene_cache in gff_parser._gene_cache.items():
            if locus_tag in gene_cache:
                gene_info = gene_cache[locus_tag]
                return {
                    "locus_tag": gene_info.locus_tag,
                    "uniprot_id": gene_info.uniprot_id,
                    "name": gene_info.name,
                    "seqid": gene_info.seqid,
                    "source": gene_info.source,
                    "type": gene_info.type,
                    "start": gene_info.start,
                    "end": gene_info.end,
                    "score": gene_info.score,
                    "strand": gene_info.strand,
                    "phase": gene_info.phase,
                    "product": gene_info.product,
                }
    
    return None


class Orthologs(Flow):
    """
    Builds order-insensitive pair docs with comprehensive gene information:
      pair_id = "<A>__<B>"

    Enhanced doc schema with GFF information:
      {
        "pair_id": "...",
        "doc_type": "ortholog",
        "gene_a": "...",   # locus tag
        "gene_b": "...",   # locus tag
        "orthology_type": "...",
        "oma_group_id": "...|None",
        "members": ["A","B"],
        # Gene A information from GFF
        "gene_a_locus_tag": "...",
        "gene_a_uniprot_id": "...",
        "gene_a_name": "...",
        "gene_a_product": "...",
        # ... more gene A fields
        # Gene B information from GFF
        "gene_b_locus_tag": "...",
        "gene_b_uniprot_id": "...",
        "gene_b_name": "...",
        "gene_b_product": "...",
        # ... more gene B fields
        # Species information
        "species_a": "...",
        "species_b": "...",
        "species_a_acronym": "...",
        "species_b_acronym": "...",
        "isolate_a": "...",
        "isolate_b": "...",
        # Convenience flags
        "has_gene_a_info": true/false,
        "has_gene_b_info": true/false,
        "both_genes_annotated": true/false
      }
    """

    def __init__(self, index_name: str = "ortholog_index", gff_parser: Optional[GFFParser] = None):
        super().__init__(index_name=index_name)
        self._docs: Dict[str, Dict[str, Any]] = {}
        self.gff_parser = gff_parser

    def _iter_chunks(self, path: str, chunksize: int):
        """
        Robust TSV reader for ortholog files:
        - Treats file as tab-separated
        - Ignores lines starting with '#'
        - File has NO real header row after comments, so we provide names
        - Skips first two columns (sequence numbers) as they're not meaningful
        - Format: seq_num_1<tab>seq_num_2<tab>protein_id_1<tab>protein_id_2<tab>orthology_type<tab>oma_group
        - We only use: protein_id_1<tab>protein_id_2<tab>orthology_type<tab>oma_group
        """
        expected_cols = [
            "seq_num_a",      # Ignored - sequence number for protein A
            "seq_num_b",      # Ignored - sequence number for protein B
            "protein_id_a",   # "BU_61_00001 Chromosomal replication initiator protein DnaA"
            "protein_id_b",   # "BU_909_00001 Chromosomal replication initiator protein DnaA"
            "orthology_type", # "1:1", "many:1", etc.
            "oma_group",      # OMA group ID (if any)
        ]

        return pd.read_csv(
            path,
            sep="\t",
            comment="#",
            header=None,  # there is no real header after comments
            names=expected_cols,  # consistent names for our _get()
            usecols=list(range(6)),  # guard against ragged rows
            dtype=str,  # keep raw strings
            chunksize=chunksize,
            engine="python",  # more forgiving with comments/mixed rows
            on_bad_lines="skip",
            na_filter=False,
            memory_map=False,
        )

    def run(self, path: str, chunksize: int = 100_000, flush_every: int = 200_000) -> None:
        rows = 0
        seen_since_flush = 0

        # Note: GFF files are now pre-loaded at the command level for better caching
        # This avoids re-downloading the same GFF files for each ortholog file

        try:
            for chunk in self._iter_chunks(path, chunksize=chunksize):
                km = _keys_map(chunk.columns)

                for rec in chunk.to_dict(orient="records"):
                    rows += 1

                    raw_a = _get(
                        rec, km,
                        "protein_id_a", "protein_id_1", "Protein 1", "protein 1", 
                        "Gene 1", "gene 1", "gene_a_locus_tag", "genea", "gene_a"
                    )
                    raw_b = _get(
                        rec, km,
                        "protein_id_b", "protein_id_2", "Protein 2", "protein 2", 
                        "Gene 2", "gene 2", "gene_b_locus_tag", "geneb", "gene_b"
                    )
                    if not raw_a or not raw_b:
                        continue

                    # Trim description text, keep only IDs in gene_a/gene_b
                    a_id, a_desc = _split_locus_and_desc(raw_a)
                    b_id, b_desc = _split_locus_and_desc(raw_b)
                    if not a_id or not b_id:
                        continue

                    pid = canonical_pair_id(a_id, b_id)

                    otype = _get(rec, km, "orthology_type", "Orthology type", "orthology type")
                    oma = _get(rec, km, "oma_group", "OMA group", "oma group", "OMA group (if any)")

                    doc = self._docs.get(pid)
                    if not doc:
                        # Extract species information for both genes
                        species_a_acronym, species_a_name, isolate_a = _extract_species_from_locus(a_id)
                        species_b_acronym, species_b_name, isolate_b = _extract_species_from_locus(b_id)
                        
                        # Get gene information from GFF parser
                        if self.gff_parser:
                            gene_a_info = _get_gene_info_for_locus(self.gff_parser, a_id)
                            gene_b_info = _get_gene_info_for_locus(self.gff_parser, b_id)
                        else:
                            gene_a_info = None
                            gene_b_info = None
                        
                        # Build comprehensive document
                        doc = {
                            "pair_id": pid,
                            "doc_type": "ortholog",
                            "gene_a": a_id,
                            "gene_b": b_id,
                            "orthology_type": None,
                            "oma_group_id": None,
                            "members": [a_id, b_id],
                            "is_one_to_one": False,  # Initialize to False, will be updated if orthology_type is 1:1
                            
                            # Species information
                            "species_a_acronym": species_a_acronym,
                            "species_b_acronym": species_b_acronym,
                            "isolate_a": isolate_a,
                            "isolate_b": isolate_b,
                            
                            # Gene A information (from GFF or defaults)
                            "gene_a_locus_tag": a_id,
                            "gene_a_uniprot_id": gene_a_info.get("uniprot_id") if gene_a_info else None,
                            "gene_a_name": gene_a_info.get("name") if gene_a_info else None,
                            "gene_a_source": gene_a_info.get("source") if gene_a_info else None,
                            "gene_a_type": gene_a_info.get("type") if gene_a_info else None,
                            "gene_a_start": gene_a_info.get("start") if gene_a_info else None,
                            "gene_a_end": gene_a_info.get("end") if gene_a_info else None,
                            "gene_a_score": gene_a_info.get("score") if gene_a_info else None,
                            "gene_a_strand": gene_a_info.get("strand") if gene_a_info else None,
                            "gene_a_phase": gene_a_info.get("phase") if gene_a_info else None,
                            "gene_a_product": gene_a_info.get("product") if gene_a_info else None,
                            "gene_a_desc": a_desc,
                            
                            # Gene B information (from GFF or defaults)
                            "gene_b_locus_tag": b_id,
                            "gene_b_uniprot_id": gene_b_info.get("uniprot_id") if gene_b_info else None,
                            "gene_b_name": gene_b_info.get("name") if gene_b_info else None,
                            "gene_b_source": gene_b_info.get("source") if gene_b_info else None,
                            "gene_b_type": gene_b_info.get("type") if gene_b_info else None,
                            "gene_b_start": gene_b_info.get("start") if gene_b_info else None,
                            "gene_b_end": gene_b_info.get("end") if gene_b_info else None,
                            "gene_b_score": gene_b_info.get("score") if gene_b_info else None,
                            "gene_b_strand": gene_b_info.get("strand") if gene_b_info else None,
                            "gene_b_phase": gene_b_info.get("phase") if gene_b_info else None,
                            "gene_b_product": gene_b_info.get("product") if gene_b_info else None,
                            "gene_b_desc": b_desc,
                            
                            # Cross-species analysis flags
                            "same_species": species_a_name == species_b_name,
                            "same_isolate": isolate_a == isolate_b,
                        }

                        self._docs[pid] = doc
                        seen_since_flush += 1

                    # set if provided; do not override with empty values
                    if otype not in (None, "", "nan", "NaN"):
                        orthology_type = str(otype).strip()
                        doc["orthology_type"] = orthology_type
                        
                        # Set orthology type flags
                        doc["is_one_to_one"] = orthology_type == "1:1"
                    
                    if oma not in (None, "", "nan", "NaN"):
                        try:
                            doc["oma_group_id"] = int(str(oma).strip())
                        except (ValueError, TypeError):
                            # If OMA group is not a valid integer, store as None
                            doc["oma_group_id"] = None

                    # Periodic flush to cap memory on huge files
                    if flush_every and seen_since_flush >= flush_every:
                        self._flush_partial()
                        seen_since_flush = 0

                # drop chunk ASAP and GC
                del km
                del chunk
                gc.collect()

        finally:
            # IMPORTANT: flush any stragglers at the end of THIS FILE
            if self._docs:
                self._flush_partial()

        print(f"[orthologs] processed rows from {path}: {rows}")

    def _get_all_isolates_from_file(self, path: str) -> List[str]:
        """Get all unique isolates from ortholog file by sampling locus tags."""
        isolates = set()
        
        try:
            # Sample first few chunks to get all unique isolates
            for chunk in self._iter_chunks(path, chunksize=1000):
                km = _keys_map(chunk.columns)
                
                for rec in chunk.to_dict(orient="records"):
                    raw_a = _get(rec, km, "protein_id_a", "protein_id_1", "Protein 1", "protein 1", "Gene 1", "gene 1")
                    raw_b = _get(rec, km, "protein_id_b", "protein_id_2", "Protein 2", "protein 2", "Gene 2", "gene 2")
                    
                    for raw_protein in [raw_a, raw_b]:
                        if raw_protein:
                            protein_id, _ = _split_locus_and_desc(raw_protein)
                            if protein_id:
                                species_acronym, species_name, isolate_name = _extract_species_from_locus(protein_id)
                                if species_name != "Unknown species" and isolate_name != "UNKNOWN":
                                    isolates.add(isolate_name)
                
                # Only sample first few chunks to avoid processing entire file
                break
                
        except Exception as e:
            print(f"[orthologs] Warning: Error sampling isolates from file {path}: {e}")
        
        return list(isolates)

    def _get_species_isolate_mapping(self, path: str) -> Dict[str, str]:
        """Get species to isolate mapping from ortholog file by sampling locus tags."""
        species_isolate_map = {}
        
        try:
            # Sample first few chunks to get species and isolate information
            for chunk in self._iter_chunks(path, chunksize=1000):
                km = _keys_map(chunk.columns)
                
                for rec in chunk.to_dict(orient="records"):
                    raw_a = _get(rec, km, "protein_id_a", "protein_id_1", "Protein 1", "protein 1", "Gene 1", "gene 1")
                    raw_b = _get(rec, km, "protein_id_b", "protein_id_2", "Protein 2", "protein 2", "Gene 2", "gene 2")
                    
                    for raw_protein in [raw_a, raw_b]:
                        if raw_protein:
                            protein_id, _ = _split_locus_and_desc(raw_protein)
                            if protein_id:
                                species_acronym, species_name, isolate_name = _extract_species_from_locus(protein_id)
                                if species_name != "Unknown species" and isolate_name != "UNKNOWN":
                                    # Map species name to isolate name for GFF lookup
                                    # Keep the first isolate found for each species
                                    if species_name not in species_isolate_map:
                                        species_isolate_map[species_name] = isolate_name
                
                # Only sample first few chunks to avoid processing entire file
                break
                
        except Exception as e:
            print(f"[orthologs] Warning: Error sampling species from file {path}: {e}")
        
        return species_isolate_map

    def _get_unique_species_from_file(self, path: str) -> List[str]:
        """Get unique species from ortholog file by sampling locus tags."""
        species_isolate_map = self._get_species_isolate_mapping(path)
        return list(species_isolate_map.keys())

    def _flush_partial(self) -> None:
        if not self._docs:
            return
        actions: List[Dict[str, Any]] = []
        # keep batch small (1000) to avoid big lists in RAM
        for pid, src in self._docs.items():
            actions.append({
                "_op_type": "index",
                "_index": self.index,
                "_id": pid,
                "_source": src,
            })
            if len(actions) >= 1000:
                bulk_exec(actions)
                actions.clear()
        if actions:
            bulk_exec(actions)
        print(f"[orthologs] partial index flush: {len(self._docs)} docs")
        # FREE the cache
        self._docs.clear()

    def flush(self) -> None:
        # stays as a safety net; usually run() will have flushed already
        if not self._docs:
            return
        actions: List[Dict[str, Any]] = []
        for pid, src in self._docs.items():
            actions.append({
                "_op_type": "index",
                "_index": self.index,
                "_id": pid,
                "_source": src,
            })
            if len(actions) >= 1000:
                bulk_exec(actions);
                actions.clear()
        if actions:
            bulk_exec(actions);
            actions.clear()
        print(f"[orthologs] indexed docs: {len(self._docs)}")
        self._docs.clear()
