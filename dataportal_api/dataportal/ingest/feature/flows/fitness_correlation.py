"""
Fitness correlation ingestion flow.

This module handles importing gene-gene fitness correlation data from CSV files
into the GeneFitnessCorrelationDocument Elasticsearch index.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
import logging

from dataportal.ingest.ppi.gff_parser import GFFParser
from dataportal.ingest.es_repo import GeneFitnessCorrelationIndexRepository

logger = logging.getLogger(__name__)


def canonical_pair(a: str, b: str) -> Tuple[str, str]:
    """Return sorted pair for canonical ordering."""
    return tuple(sorted([a, b]))


def build_pair_id(species_key: str, a: str, b: str) -> str:
    """Build unique pair ID for correlation document."""
    aa, bb = canonical_pair(a, b)
    return f"{species_key}:{aa}__{bb}"


def _extract_species_from_locus(locus_tag: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract species acronym and scientific name from locus tag.
    Examples:
      - BU_ATCC8492_01234 -> ("BU", "Bacteroides uniformis")
      - PV_ATCC8482_00123 -> ("PV", "Prevotella vulgatus")
    """
    if not locus_tag or not isinstance(locus_tag, str):
        return None, None
    
    parts = locus_tag.split("_")
    if len(parts) < 2:
        return None, None
    
    acronym = parts[0].upper()
    
    # Map acronyms to scientific names
    species_map = {
        "BU": "Bacteroides uniformis",
        "PV": "Prevotella vulgatus",
        # Add more mappings as needed
    }
    
    scientific_name = species_map.get(acronym)
    return acronym, scientific_name


def _extract_isolate_from_locus(locus_tag: str) -> Optional[str]:
    """
    Extract isolate name from locus tag.
    Example: BU_ATCC8492_01234 -> BU_ATCC8492
    """
    if not locus_tag or not isinstance(locus_tag, str):
        return None
    
    parts = locus_tag.split("_")
    if len(parts) >= 3:
        return f"{parts[0]}_{parts[1]}"
    return None


@dataclass
class FitnessCorrelationFlow:
    """
    Flow for ingesting gene-gene fitness correlation data.
    
    Expected CSV columns:
      - Gene1: locus tag of first gene
      - Gene2: locus tag of second gene
      - value: correlation coefficient (-1 to 1)
    """
    repo: GeneFitnessCorrelationIndexRepository
    gff_parser: Optional[GFFParser] = None
    chunk_size: int = 20000  # Increased for large datasets (240K+ records)
    batch_size: int = 5000   # Increased for better I/O efficiency

    def _row_to_action(self, row: Dict) -> Optional[Dict]:
        """Convert a CSV row to an Elasticsearch bulk action."""
        gene_a = row.get("Gene1")
        gene_b = row.get("Gene2")
        
        if not gene_a or not gene_b:
            return None
        
        # Get correlation value
        try:
            corr_value = float(row.get("value", 0))
        except (ValueError, TypeError):
            logger.warning(f"Invalid correlation value for {gene_a} - {gene_b}")
            return None
        
        # Extract species information from locus tags
        acronym_a, species_a = _extract_species_from_locus(gene_a)
        acronym_b, species_b = _extract_species_from_locus(gene_b)
        
        # Use first gene's species info (they should match in same-species correlations)
        species_acronym = acronym_a or acronym_b or "UNKNOWN"
        species_scientific_name = species_a or species_b
        isolate_name = _extract_isolate_from_locus(gene_a) or _extract_isolate_from_locus(gene_b)
        
        # Canonical ordering
        gene_a_sorted, gene_b_sorted = canonical_pair(gene_a, gene_b)
        pair_id = build_pair_id(species_acronym, gene_a, gene_b)
        
        # Build base document
        src = {
            "pair_id": pair_id,
            "species_scientific_name": species_scientific_name,
            "species_acronym": species_acronym,
            "isolate_name": isolate_name,
            "gene_a": gene_a,
            "gene_b": gene_b,
            "genes": [gene_a, gene_b],
            "genes_sorted": [gene_a_sorted, gene_b_sorted],
            "is_self_correlation": (gene_a == gene_b),
            "correlation_value": corr_value,
            "abs_correlation": abs(corr_value),
        }
        
        # Categorize correlation strength
        abs_val = abs(corr_value)
        if abs_val >= 0.7:
            strength = "strong"
        elif abs_val >= 0.4:
            strength = "moderate"
        else:
            strength = "weak"
        
        direction = "positive" if corr_value >= 0 else "negative"
        src["correlation_strength"] = f"{strength}_{direction}" if abs_val > 0.1 else "weak"
        
        # Enrich with gene information from GFF if available
        if self.gff_parser:
            # Get gene info for gene_a
            gene_a_info = self.gff_parser.get_gene_info(species_scientific_name, gene_a)
            if gene_a_info:
                src.update({
                    "gene_a_locus_tag": gene_a_info.locus_tag,
                    "gene_a_uniprot_id": gene_a_info.uniprot_id,
                    "gene_a_name": gene_a_info.name,
                    "gene_a_product": gene_a_info.product,
                    "gene_a_seq_id": gene_a_info.seqid,
                    "gene_a_start": gene_a_info.start,
                    "gene_a_end": gene_a_info.end,
                })
            
            # Get gene info for gene_b
            gene_b_info = self.gff_parser.get_gene_info(species_scientific_name, gene_b)
            if gene_b_info:
                src.update({
                    "gene_b_locus_tag": gene_b_info.locus_tag,
                    "gene_b_uniprot_id": gene_b_info.uniprot_id,
                    "gene_b_name": gene_b_info.name,
                    "gene_b_product": gene_b_info.product,
                    "gene_b_seq_id": gene_b_info.seqid,
                    "gene_b_start": gene_b_info.start,
                    "gene_b_end": gene_b_info.end,
                })
        
        # Return bulk action
        return {
            "_op_type": "index",
            "_id": pair_id,
            "_source": src,
        }

    def run(self, csv_path: str) -> Tuple[int, int]:
        """
        Process a fitness correlation CSV file.
        
        Returns:
            Tuple of (total_processed, total_indexed)
        """
        logger.info(f"Processing fitness correlation file: {csv_path}")
        
        total_processed = 0
        total_indexed = 0
        actions = []
        
        try:
            # Read CSV in chunks
            for chunk in pd.read_csv(csv_path, chunksize=self.chunk_size):
                for _, row in chunk.iterrows():
                    total_processed += 1
                    
                    action = self._row_to_action(row.to_dict())
                    if action:
                        actions.append(action)
                    
                    # Batch insert
                    if len(actions) >= self.batch_size:
                        success, failures = self.repo.bulk_index(actions)
                        total_indexed += success
                        
                        if failures:
                            logger.warning(f"Failed to index {len(failures)} correlation records")
                        
                        actions.clear()
            
            # Insert remaining actions
            if actions:
                success, failures = self.repo.bulk_index(actions)
                total_indexed += success
                
                if failures:
                    logger.warning(f"Failed to index {len(failures)} correlation records")
        
        except Exception as e:
            logger.error(f"Error processing fitness correlation file: {e}")
            raise
        
        logger.info(f"Processed {total_processed} rows, indexed {total_indexed} correlations")
        return total_processed, total_indexed

