"""
GFF parser utility for extracting gene information with caching.

This module provides functionality to parse GFF files and extract gene information
for protein-protein interactions, with in-memory caching to avoid re-downloading
the same GFF files.
"""

import os
import tempfile
import ftplib
import logging
import time
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GeneInfo:
    """Gene information extracted from GFF files."""
    locus_tag: Optional[str] = None
    uniprot_id: Optional[str] = None
    name: Optional[str] = None
    seqid: Optional[str] = None
    source: Optional[str] = None
    type: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None
    score: Optional[float] = None
    strand: Optional[str] = None
    phase: Optional[str] = None
    product: Optional[str] = None


class GFFParser:
    """GFF parser with caching for gene information extraction."""
    
    def __init__(self, ftp_server: str = "ftp.ebi.ac.uk", ftp_directory: str = "/pub/databases/mett/annotations/v1_2024-04-15/"):
        self.ftp_server = ftp_server
        self.ftp_directory = ftp_directory
        self._gene_cache: Dict[str, Dict[str, GeneInfo]] = {}  # isolate -> {locus_tag -> GeneInfo}
        self._uniprot_cache: Dict[str, Dict[str, GeneInfo]] = {}  # isolate -> {uniprot_id -> GeneInfo}
        self._gff_file_cache: Dict[str, str] = {}  # isolate -> gff_file mapping
        self._species_to_isolate: Dict[str, str] = {}  # species -> isolate mapping
        self._loaded_isolates: set = set()  # Track which isolates have been loaded
    
    def _reconnect_ftp(self) -> ftplib.FTP:
        """Handle FTP connection with retry logic and exponential backoff."""
        retries = 5  # Increased retries
        for attempt in range(retries):
            try:
                ftp = ftplib.FTP(self.ftp_server)
                ftp.login()
                return ftp
            except ftplib.all_errors as e:
                if attempt < retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, 8s
                    delay = 2 ** attempt
                    logger.warning(f"FTP connection failed, retrying in {delay}s... (attempt {attempt + 1}/{retries})")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to connect to FTP after {retries} attempts: {e}")
                    raise
    
    def _get_gff_file_for_isolate(self, isolate: str) -> Optional[str]:
        """Get the GFF file name for a given isolate."""
        logger.info(f"Getting GFF file for isolate: {isolate}")
        
        if isolate in self._gff_file_cache:
            # logger.info(f"GFF file found in cache for isolate {isolate}: {self._gff_file_cache[isolate]}")
            return self._gff_file_cache[isolate]
        
        try:
            # logger.info(f"Connecting to FTP server: {self.ftp_server}")
            ftp = self._reconnect_ftp()
            isolate_path = f"{self.ftp_directory}/{isolate}/functional_annotation/merged_gff/"
            # logger.info(f"Looking for GFF files in path: {isolate_path}")
            
            gff_files = ftp.nlst(isolate_path)
            # logger.info(f"Found {len(gff_files)} files in directory: {gff_files}")
            ftp.quit()
            
            # Find the annotations GFF file
            gff_file = None
            for file in gff_files:
                # logger.info(f"Checking file: {file}")
                if file.endswith("_annotations.gff"):
                    gff_file = file
                    # logger.info(f"Found annotations GFF file: {gff_file}")
                    break
            
            if gff_file:
                self._gff_file_cache[isolate] = gff_file
                # logger.info(f"Successfully found GFF file for isolate {isolate}: {gff_file}")
                return gff_file
            else:
                logger.warning(f"No GFF file found for isolate {isolate} in directory {isolate_path}")
                logger.warning(f"Available files: {gff_files}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting GFF file for isolate {isolate}: {e}")
            return None
    
    def _parse_dbxref(self, dbxref_string: str) -> Tuple[list, Optional[str]]:
        """Parse dbxref string to extract UniProt ID."""
        if not dbxref_string or dbxref_string.strip() == "":
            return [], None
        
        dbxref_list = dbxref_string.split(",")
        uniprot_id = None
        
        for entry in dbxref_list:
            parts = entry.split(":", 1)
            if len(parts) == 2 and parts[0] == "UniProt":
                uniprot_id = parts[1]
                break
        
        return dbxref_list, uniprot_id
    
    def _download_gff_file(self, gff_file: str) -> Optional[str]:
        """Download GFF file to temporary location."""
        # logger.debug(f"Downloading GFF file: {gff_file}")
        
        try:
            ftp = self._reconnect_ftp()
            local_gff_path = os.path.join(tempfile.gettempdir(), os.path.basename(gff_file))
            # logger.debug(f"Local GFF path: {local_gff_path}")
            
            # Check if file exists on FTP
            try:
                file_size = ftp.size(gff_file)
                # logger.debug(f"File size on FTP: {file_size} bytes")
            except ftplib.error_perm as e:
                logger.warning(f"File not found on FTP: {gff_file}, error: {e}")
                ftp.quit()
                return None
            
            # Download file
            # logger.debug(f"Starting download of {gff_file}")
            with open(local_gff_path, "wb") as f:
                ftp.retrbinary(f"RETR {gff_file}", f.write)
            ftp.quit()
            
            # Verify download
            if os.path.exists(local_gff_path):
                actual_size = os.path.getsize(local_gff_path)
                # logger.debug(f"Downloaded file size: {actual_size} bytes")
                if actual_size == 0:
                    logger.error(f"Downloaded file is empty: {local_gff_path}")
                    return None
                # logger.info(f"Successfully downloaded GFF file: {local_gff_path}")
            else:
                logger.error(f"Downloaded file does not exist: {local_gff_path}")
                return None
            
            return local_gff_path
            
        except Exception as e:
            logger.error(f"Error downloading GFF file {gff_file}: {e}")
            return None
    
    def _parse_gff_file(self, gff_file_path: str) -> Dict[str, GeneInfo]:
        """Parse GFF file and extract gene information."""
        gene_info_map = {}
        line_count = 0
        gene_count = 0
        skipped_lines = 0
        
        # logger.debug(f"Starting to parse GFF file: {gff_file_path}")
        
        try:
            with open(gff_file_path, "r") as gff:
                for line_num, line in enumerate(gff, 1):
                    line_count += 1
                    
                    if line.startswith("#"):
                        # if line_count <= 10:  # Log first 10 comment lines
                            # logger.debug(f"Comment line {line_num}: {line.strip()}")
                        continue
                    
                    columns = line.strip().split("\t")
                    if len(columns) != 9:
                        skipped_lines += 1
                        # if skipped_lines <= 5:  # Log first 5 skipped lines
                        #     logger.debug(f"Skipped line {line_num} (wrong column count {len(columns)}): {line.strip()}")
                        continue
                    
                    if columns[2] != "gene":
                        skipped_lines += 1
                        # if skipped_lines <= 5:  # Log first 5 skipped lines
                        #     logger.debug(f"Skipped line {line_num} (not a gene, type: {columns[2]}): {line.strip()}")
                        continue
                    
                    seq_id, source, feature_type, start, end, score, strand, phase, attributes = columns
                    
                    # Parse attributes
                    attr_dict = {}
                    for item in attributes.split(";"):
                        if "=" in item:
                            key, value = item.split("=", 1)
                            attr_dict[key.strip()] = value.strip()
                    
                    locus_tag = attr_dict.get("locus_tag")
                    if not locus_tag:
                        skipped_lines += 1
                        # if skipped_lines <= 5:  # Log first 5 skipped lines
                        #     logger.debug(f"Skipped line {line_num} (no locus_tag): {line.strip()}")
                        continue
                    
                    # Parse dbxref for UniProt ID
                    dbxref_raw = attr_dict.get("Dbxref", "")
                    _, uniprot_id = self._parse_dbxref(dbxref_raw)
                    
                    # Log first few successful gene extractions
                    # if gene_count < 5:
                        # logger.debug(f"Gene {gene_count + 1} - Locus: {locus_tag}, UniProt: {uniprot_id}, Name: {attr_dict.get('Name')}, Product: {attr_dict.get('product')}")
                        # logger.debug(f"Full attributes: {attr_dict}")
                    
                    # Create GeneInfo object
                    gene_info = GeneInfo(
                        locus_tag=locus_tag,
                        uniprot_id=uniprot_id,
                        name=attr_dict.get("Name"),
                        seqid=seq_id,
                        source=source,
                        type=feature_type,
                        start=int(start) if start != "." else None,
                        end=int(end) if end != "." else None,
                        score=float(score) if score != "." else None,
                        strand=strand if strand != "." else None,
                        phase=phase if phase != "." else None,
                        product=attr_dict.get("product")
                    )
                    
                    gene_info_map[locus_tag] = gene_info
                    gene_count += 1
                    
        except Exception as e:
            logger.error(f"Error parsing GFF file {gff_file_path}: {e}")
        
        logger.info(f"GFF parsing complete - Total lines: {line_count}, Genes found: {gene_count}, Skipped lines: {skipped_lines}")
        return gene_info_map
    
    
    def set_species_mapping(self, species_mapping: Dict[str, str]):
        """Set the species to isolate mapping."""
        self._species_to_isolate = species_mapping
        logger.info(f"Set species mapping: {species_mapping}")
        logger.debug(f"Species mapping details: {len(species_mapping)} mappings set")
        for species, isolate in species_mapping.items():
            logger.debug(f"  {species} -> {isolate}")
    
    def preload_gff_files(self, species_list: List[str]) -> None:
        """Pre-load GFF files for all species in the list with connection throttling."""
        logger.info(f"Pre-loading GFF files for {len(species_list)} species...")
        
        successful_loads = 0
        failed_loads = 0
        
        for i, species in enumerate(species_list, 1):
            isolate = self._species_to_isolate.get(species)
            if not isolate:
                logger.warning(f"No isolate mapping found for species: {species}")
                continue
            
            if isolate in self._loaded_isolates:
                logger.debug(f"GFF data already loaded for isolate: {isolate}")
                continue
            
            try:
                logger.info(f"Loading GFF file {i}/{len(species_list)}: {isolate}")
                self._load_isolate_gff_data(isolate)
                self._loaded_isolates.add(isolate)
                successful_loads += 1
                logger.info(f"Successfully loaded GFF data for isolate: {isolate}")
                
                # Add delay between downloads to avoid overwhelming the FTP server
                if i < len(species_list):  # Don't delay after the last file
                    time.sleep(0.5)  # 500ms delay between downloads
                    
            except Exception as e:
                failed_loads += 1
                logger.error(f"Failed to load GFF data for isolate {isolate}: {e}")
                
                # Add longer delay after failures to give the server time to recover
                time.sleep(2.0)  # 2 second delay after failures
        
        logger.info(f"GFF preload complete: {successful_loads} successful, {failed_loads} failed")
    
    def _load_isolate_gff_data(self, isolate: str) -> None:
        """Load GFF data for a specific isolate."""
        # logger.debug(f"Loading GFF data for isolate: {isolate}")
        
        gff_file = self._get_gff_file_for_isolate(isolate)
        if not gff_file:
            logger.warning(f"No GFF file found for isolate: {isolate}")
            return
        
        # logger.debug(f"GFF file found: {gff_file}")
        
        local_gff_path = self._download_gff_file(gff_file)
        if not local_gff_path:
            logger.error(f"Failed to download GFF file for isolate: {isolate}")
            return
        
        # logger.debug(f"GFF file downloaded to: {local_gff_path}")
        
        try:
            gene_info_map = self._parse_gff_file(local_gff_path)
            self._gene_cache[isolate] = gene_info_map
            
            # Build UniProt ID cache
            uniprot_map = {}
            for locus_tag, gene_info in gene_info_map.items():
                if gene_info.uniprot_id:
                    uniprot_map[gene_info.uniprot_id] = gene_info
            self._uniprot_cache[isolate] = uniprot_map
            
            # logger.info(f"Loaded {len(gene_info_map)} genes from GFF file for isolate: {isolate}")
            # logger.info(f"Built UniProt cache with {len(uniprot_map)} entries for isolate: {isolate}")
            
            # Log sample of loaded genes for debugging
            if gene_info_map:
                sample_genes = list(gene_info_map.items())[:3]
                # for locus_tag, gene_info in sample_genes:
                #     logger.debug(f"Sample gene - {locus_tag}: {gene_info}")
            else:
                logger.warning(f"No genes loaded for isolate: {isolate}")
                
        finally:
            # Clean up temporary file
            if os.path.exists(local_gff_path):
                logger.debug(f"Cleaning up temporary file: {local_gff_path}")
                os.remove(local_gff_path)
    
    def get_gene_info(self, species: str, locus_tag: str) -> Optional[GeneInfo]:
        """Get gene information for a specific locus tag from a species."""
        # logger.info(f"Getting gene info for species: {species}, locus_tag: {locus_tag}")
        
        isolate = self._species_to_isolate.get(species)
        if not isolate:
            logger.warning(f"No isolate mapping found for species: {species}")
            logger.info(f"Available species mappings: {self._species_to_isolate}")
            return None
        
        # logger.info(f"Species {species} maps to isolate: {isolate}")
        
        # Load GFF data if not already loaded
        if isolate not in self._loaded_isolates:
            logger.info(f"GFF data not loaded for isolate {isolate}, loading now...")
            try:
                self._load_isolate_gff_data(isolate)
                self._loaded_isolates.add(isolate)
            except Exception as e:
                logger.error(f"Failed to load GFF data for isolate {isolate}: {e}")
                return None
        # else:
        #     logger.info(f"GFF data already loaded for isolate: {isolate}")
        
        # Return gene info from cache
        if isolate in self._gene_cache:
            gene_info = self._gene_cache[isolate].get(locus_tag)
            # if gene_info:
            #     logger.info(f"Found gene info for {locus_tag}: {gene_info}")
            # else:
            #     logger.info(f"No gene info found for locus_tag: {locus_tag} in isolate: {isolate}")
            #     logger.info(f"Available locus_tags in cache: {list(self._gene_cache[isolate].keys())[:10]}")
            return gene_info
        else:
            logger.warning(f"No gene cache found for isolate: {isolate}")
            return None
    
    def get_gene_info_by_uniprot(self, species: str, uniprot_id: str) -> Optional[GeneInfo]:
        """Get gene information for a specific UniProt ID from a species."""
        # logger.info(f"Getting gene info for species: {species}, uniprot_id: {uniprot_id}")
        
        isolate = self._species_to_isolate.get(species)
        if not isolate:
            logger.warning(f"No isolate mapping found for species: {species}")
            logger.info(f"Available species mappings: {self._species_to_isolate}")
            return None
        
        # logger.info(f"Species {species} maps to isolate: {isolate}")
        
        # Load GFF data if not already loaded
        if isolate not in self._loaded_isolates:
            # logger.info(f"GFF data not loaded for isolate {isolate}, loading now...")
            try:
                self._load_isolate_gff_data(isolate)
                self._loaded_isolates.add(isolate)
            except Exception as e:
                logger.error(f"Failed to load GFF data for isolate {isolate}: {e}")
                return None
        # else:
        #     logger.info(f"GFF data already loaded for isolate: {isolate}")
        
        # Return gene info from UniProt cache
        if isolate in self._uniprot_cache:
            gene_info = self._uniprot_cache[isolate].get(uniprot_id)
            # if gene_info:
            #     logger.info(f"Found gene info for UniProt ID {uniprot_id}: {gene_info}")
            # else:
            #     logger.info(f"No gene info found for UniProt ID: {uniprot_id} in isolate: {isolate}")
            #     logger.info(f"Available UniProt IDs in cache: {list(self._uniprot_cache[isolate].keys())[:10]}")
            return gene_info
        else:
            logger.warning(f"No UniProt cache found for isolate: {isolate}")
            return None
    
    def get_gene_info_for_proteins(self, species: str, protein_a: str, protein_b: str) -> Tuple[Optional[GeneInfo], Optional[GeneInfo]]:
        """Get gene information for both proteins in a PPI."""
        # Try locus tag lookup first, then UniProt ID lookup
        gene_a = self.get_gene_info(species, protein_a)
        if not gene_a:
            gene_a = self.get_gene_info_by_uniprot(species, protein_a)
        
        gene_b = self.get_gene_info(species, protein_b)
        if not gene_b:
            gene_b = self.get_gene_info_by_uniprot(species, protein_b)
        
        return gene_a, gene_b
    
    def clear_cache(self):
        """Clear the gene information cache."""
        self._gene_cache.clear()
        self._uniprot_cache.clear()
        self._gff_file_cache.clear()
        self._loaded_isolates.clear()
        logger.info("GFF parser cache cleared")
