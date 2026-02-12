from __future__ import annotations
import csv
import glob
import os
import logging
from typing import Dict, Iterator, List, Optional
from .gff_parser import GFFParser, GeneInfo

logger = logging.getLogger(__name__)

PPI_CSV_COLUMNS = [
    "species",
    "id",
    "protein_a",
    "protein_b",
    "ds_score",
    "tt_score",
    "perturb_score",
    "gp_score",
    "melt_score",
    "sec_score",
    "bn_score",
    "string_physical_score",
    "operon_score",
    "ecocyc_score",
    "xlms_peptides",
    "xlms_files",
]


def load_string_mapping(path: str) -> Dict[str, str]:
    """
    Load a UniProt → STRING protein id mapping from a TSV/CSV file.

    Supports two formats:
      1) Headered mapping files (recommended):
         - UniProt column: one of ["mett_uniprot", "uniprot", "uniprot_id"]
         - STRING column: one of ["string_protein_id", "string_id", "string_protein"]
      2) Raw DIAMOND output with no header, where:
         - column 0 = METT/UniProt id (qseqid)
         - column 1 = STRING protein id (sseqid)
    """
    mapping: Dict[str, str] = {}
    if not path:
        return mapping

    dialect = None

    # First attempt: headered DictReader
    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            sample = f.read(4096)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample, delimiters="\t,")
            except Exception:
                dialect = csv.excel_tab

            reader = csv.DictReader(f, dialect=dialect)
            fieldnames = [h.strip() for h in (reader.fieldnames or [])]
            lower = {h.lower(): h for h in fieldnames}

            uni_keys = ["mett_uniprot", "uniprot", "uniprot_id"]
            str_keys = ["string_protein_id", "string_id", "string_protein"]

            uni_col = next((lower[k] for k in uni_keys if k in lower), None)
            str_col = next((lower[k] for k in str_keys if k in lower), None)

            if uni_col and str_col:
                for row in reader:
                    uni = (row.get(uni_col) or "").strip()
                    sid = (row.get(str_col) or "").strip()
                    if not uni or not sid:
                        continue
                    mapping[uni] = sid

                logger.info(
                    f"[ppi] Loaded {len(mapping)} UniProt→STRING mappings from {path} (headered)"
                )
                return mapping
    except FileNotFoundError:
        logger.warning(f"[ppi] STRING mapping file not found: {path}")
        return mapping
    except Exception as e:
        logger.warning(f"[ppi] Error reading STRING mapping file {path}: {e}")

    # Fallback: headerless raw mapping (e.g. *_to_string_raw.tsv)
    try:
        if dialect is None:
            dialect = csv.excel_tab
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f, dialect=dialect)
            for row in reader:
                if len(row) < 2:
                    continue
                uni = str(row[0]).strip()
                sid = str(row[1]).strip()
                if not uni or not sid:
                    continue
                mapping[uni] = sid

        logger.info(
            f"[ppi] Loaded {len(mapping)} UniProt→STRING mappings from {path} (headerless)"
        )
    except Exception as e:
        logger.warning(
            f"[ppi] Failed to parse STRING mapping file {path} as headerless mapping: {e}"
        )

    return mapping


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


def iter_ppi_rows(
    folder: str, pattern: str = "*.csv", gff_parser: Optional[GFFParser] = None
) -> Iterator[Dict]:
    """Yield raw rows from all CSVs in `folder` matching pattern with optional gene information."""
    for path in sorted(glob.glob(os.path.join(folder, pattern))):
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # optional: verify header superset
            missing = set(["species", "protein_a", "protein_b"]) - set(
                reader.fieldnames or []
            )
            if missing:
                raise ValueError(f"PPI CSV missing columns {missing} in {path}")
            for row in reader:
                base_row = {
                    "species": row.get("species"),
                    "csv_id": row.get(
                        "id"
                    ),  # may be None; not trusted for canonicalization
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
                    species = base_row["species"]
                    protein_a = base_row["protein_a"]
                    protein_b = base_row["protein_b"]

                    # logger.info(f"Looking up gene info for species: {species}, protein_a: {protein_a}, protein_b: {protein_b}")

                    if species:
                        gene_a, gene_b = gff_parser.get_gene_info_for_proteins(
                            species, protein_a, protein_b
                        )

                        # logger.info(f"Gene lookup results - gene_a: {gene_a}, gene_b: {gene_b}")

                        base_row.update(_add_gene_info_to_row(gene_a, gene_b))
                    else:
                        logger.info("No species found in row, skipping gene lookup")
                else:
                    logger.info("No GFF parser provided, skipping gene lookup")

                yield base_row


def _add_gene_info_to_row(
    gene_a: Optional[GeneInfo], gene_b: Optional[GeneInfo]
) -> Dict:
    """Add gene information to a PPI row."""
    gene_info = {}

    # logger.info(f"Adding gene info to row - gene_a: {gene_a}, gene_b: {gene_b}")

    # Add protein_a gene information
    if gene_a:
        # logger.info(f"Adding gene_a info: locus_tag={gene_a.locus_tag}, uniprot_id={gene_a.uniprot_id}, name={gene_a.name}")
        gene_info.update(
            {
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
            }
        )
    else:
        # logger.info("No gene_a info, adding None values")
        # Add None values for missing gene information
        gene_info.update(
            {
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
            }
        )

    # Add protein_b gene information
    if gene_b:
        # logger.info(f"Adding gene_b info: locus_tag={gene_b.locus_tag}, uniprot_id={gene_b.uniprot_id}, name={gene_b.name}")
        gene_info.update(
            {
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
            }
        )
    else:
        # logger.info("No gene_b info, adding None values")
        # Add None values for missing gene information
        gene_info.update(
            {
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
            }
        )

    # logger.info(f"Final gene_info dict: {gene_info}")
    return gene_info
