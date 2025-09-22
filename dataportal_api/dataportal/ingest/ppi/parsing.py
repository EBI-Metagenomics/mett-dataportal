from __future__ import annotations
import csv, glob, os
from typing import Dict, Iterable, Iterator, List, Optional, Tuple
from .gff_parser import GFFParser, GeneInfo

PPI_CSV_COLUMNS = [
    "species","id","protein_a","protein_b","ds_score","tt_score","perturb_score",
    "gp_score","melt_score","sec_score","bn_score","string_physical_score",
    "operon_score","ecocyc_score","xlms_peptides","xlms_files",
]

def _flt(v: Optional[str]) -> Optional[float]:
    if v is None:
        return None
    v = str(v).strip()
    if not v or v.lower() in {"na", "nan", "none"}:
        return None
    try:
        return float(v)
    except Exception:
        return None

def _split_list(v: Optional[str]) -> Optional[List[str]]:
    if not v:
        return None
    parts = [p.strip() for p in str(v).split(",")]
    parts = [p for p in parts if p]
    return parts or None

def iter_ppi_rows(folder: str, pattern: str = "*.csv", gff_parser: Optional[GFFParser] = None) -> Iterator[Dict]:
    """Yield raw rows from all CSVs in `folder` matching pattern with optional gene information."""
    for path in sorted(glob.glob(os.path.join(folder, pattern))):
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # optional: verify header superset
            missing = set(["species","protein_a","protein_b"]) - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"PPI CSV missing columns {missing} in {path}")
            for row in reader:
                base_row = {
                    "species": row.get("species"),
                    "csv_id": row.get("id"),  # may be None; not trusted for canonicalization
                    "protein_a": row.get("protein_a"),
                    "protein_b": row.get("protein_b"),
                    "ds_score": _flt(row.get("ds_score")),
                    "tt_score": _flt(row.get("tt_score")),
                    "perturbation_score": _flt(row.get("perturb_score")),
                    "abundance_score": _flt(row.get("gp_score")),
                    "melt_score": _flt(row.get("melt_score")),
                    "secondary_score": _flt(row.get("sec_score")),
                    "bayesian_score": _flt(row.get("bn_score")),
                    "string_score": _flt(row.get("string_physical_score")),
                    "operon_score": _flt(row.get("operon_score")),
                    "ecocyc_score": _flt(row.get("ecocyc_score")),
                    "xlms_peptides": (row.get("xlms_peptides") or None),
                    "xlms_files": _split_list(row.get("xlms_files")),
                }
                
                # Add gene information if GFF parser is provided
                if gff_parser:
                    # Extract isolate from species or use a default mapping
                    isolate = _extract_isolate_from_species(base_row["species"])
                    if isolate:
                        gene_a, gene_b = gff_parser.get_gene_info_for_proteins(
                            isolate, base_row["protein_a"], base_row["protein_b"]
                        )
                        base_row.update(_add_gene_info_to_row(gene_a, gene_b))
                
                yield base_row


def _extract_isolate_from_species(species: Optional[str]) -> Optional[str]:
    """Extract isolate name from species information."""
    if not species:
        return None
    
    # This is a simple mapping - you might need to adjust based on your data
    # For now, we'll assume the species contains the isolate information
    # You might need to implement a more sophisticated mapping here
    species_mapping = {
        "Bacteroides uniformis": "BU_ATCC8492",  # Example mapping
        "Phocaeicola vulgatus": "PV_ATCC8482",   # Example mapping
    }
    
    return species_mapping.get(species)


def _add_gene_info_to_row(gene_a: Optional[GeneInfo], gene_b: Optional[GeneInfo]) -> Dict:
    """Add gene information to a PPI row."""
    gene_info = {}
    
    # Add protein_a gene information
    if gene_a:
        gene_info.update({
            "protein_a_locus_tag": gene_a.locus_tag,
            "protein_a_uniprot_id": gene_a.uniprot_id,
            "protein_a_name": gene_a.name,
            "protein_a_seqid": gene_a.seqid,
            "protein_a_source": gene_a.source,
            "protein_a_type": gene_a.type,
            "protein_a_start": gene_a.start,
            "protein_a_end": gene_a.end,
            "protein_a_score": gene_a.score,
            "protein_a_strand": gene_a.strand,
            "protein_a_phase": gene_a.phase,
            "protein_a_product": gene_a.product,
        })
    else:
        # Add None values for missing gene information
        gene_info.update({
            "protein_a_locus_tag": None,
            "protein_a_uniprot_id": None,
            "protein_a_name": None,
            "protein_a_seqid": None,
            "protein_a_source": None,
            "protein_a_type": None,
            "protein_a_start": None,
            "protein_a_end": None,
            "protein_a_score": None,
            "protein_a_strand": None,
            "protein_a_phase": None,
            "protein_a_product": None,
        })
    
    # Add protein_b gene information
    if gene_b:
        gene_info.update({
            "protein_b_locus_tag": gene_b.locus_tag,
            "protein_b_uniprot_id": gene_b.uniprot_id,
            "protein_b_name": gene_b.name,
            "protein_b_seqid": gene_b.seqid,
            "protein_b_source": gene_b.source,
            "protein_b_type": gene_b.type,
            "protein_b_start": gene_b.start,
            "protein_b_end": gene_b.end,
            "protein_b_score": gene_b.score,
            "protein_b_strand": gene_b.strand,
            "protein_b_phase": gene_b.phase,
            "protein_b_product": gene_b.product,
        })
    else:
        # Add None values for missing gene information
        gene_info.update({
            "protein_b_locus_tag": None,
            "protein_b_uniprot_id": None,
            "protein_b_name": None,
            "protein_b_seqid": None,
            "protein_b_source": None,
            "protein_b_type": None,
            "protein_b_start": None,
            "protein_b_end": None,
            "protein_b_score": None,
            "protein_b_strand": None,
            "protein_b_phase": None,
            "protein_b_product": None,
        })
    
    return gene_info
