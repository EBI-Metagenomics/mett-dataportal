from __future__ import annotations
import csv
import glob
import os
import re
import logging
from typing import Dict, Iterator, List, Optional, Tuple
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

# Consensus RankAvg TSV: Weight_* column -> internal field name
CONSENSUS_WEIGHT_COLUMN_MAP: Dict[str, str] = {
    "Weight_Coexp": "weight_coexp",
    "Weight_Operons-ANNOgesic": "weight_operons_annogesic",
    "Weight_Operons-OpDetect": "weight_operons_opdetect",
    "Weight_Operons-OpMapper": "weight_operons_opmapper",
    "Weight_PhenoCorr-neg": "weight_phenocorr_neg",
    "Weight_PhenoCorr-pos": "weight_phenocorr_pos",
    "Weight_PMI-GSMs": "weight_pmi_gsms",
    "Weight_PMI": "weight_pmi",
    "Weight_PPI-BnScore": "bayesian_score",
    "Weight_PPI-DsScore": "ds_score",
    "Weight_PPI-EcocycScore": "ecocyc_score",
    "Weight_PPI-GpScore-neg": "weight_ppi_gp_score_neg",
    "Weight_PPI-GpScore-pos": "weight_ppi_gp_score_pos",
    "Weight_PPI-MeltScore": "melt_score",
    "Weight_PPI-OperonScore": "operon_score",
    "Weight_PPI-PerturbScore-neg": "weight_ppi_perturb_score_neg",
    "Weight_PPI-PerturbScore-pos": "weight_ppi_perturb_score_pos",
    "Weight_PPI-SecScore": "secondary_score",
    "Weight_PPI-StringPhysicalScore": "string_score",
    "Weight_PPI-TtScore": "tt_score",
    "Weight_PPI-XlmsFiles": "weight_ppi_xlms_files",
    "Weight_PPI-XlmsPeptides": "weight_ppi_xlms_peptides",
}

LOCUS_TAG_SPECIES_MAP: Dict[str, Tuple[str, str]] = {
    "BU": ("Bacteroides uniformis", "BU"),
    "PV": ("Phocaeicola vulgatus", "PV"),
}


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

        logger.info(f"[ppi] Loaded {len(mapping)} UniProt→STRING mappings from {path} (headerless)")
    except Exception as e:
        logger.warning(
            f"[ppi] Failed to parse STRING mapping file {path} as headerless mapping: {e}"
        )

    return mapping


def _int(v: Optional[str]) -> Optional[int]:
    if v is None:
        return None
    v = str(v).strip()
    if not v or v.lower() in {"na", "nan", "none"}:
        return None
    try:
        return int(float(v))
    except Exception:
        return None


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


def _infer_species_from_locus_tag(locus_tag: str) -> Tuple[Optional[str], Optional[str]]:
    """Infer (species_scientific_name, species_acronym) from locus tag prefix."""
    if not locus_tag:
        return None, None
    match = re.match(r"^([A-Z]+)_", locus_tag)
    if not match:
        return None, None
    acronym = match.group(1)
    return LOCUS_TAG_SPECIES_MAP.get(acronym, (None, acronym))


def _infer_species_from_filename(path: str) -> Tuple[Optional[str], Optional[str]]:
    basename = os.path.basename(path).upper()
    for acronym, (scientific_name, _) in LOCUS_TAG_SPECIES_MAP.items():
        if basename.startswith(f"{acronym}_"):
            return scientific_name, acronym
    return None, None


def _parse_consensus_row(
    row: Dict[str, str],
    path: str,
    gff_parser: Optional[GFFParser] = None,
) -> Dict:
    """Parse a single consensus RankAvg TSV row into normalized PPI row dict."""
    locus_a = (row.get("GeneA") or "").strip()
    locus_b = (row.get("GeneB") or "").strip()
    species_name, species_acronym = _infer_species_from_locus_tag(locus_a)
    if not species_name:
        species_name, species_acronym = _infer_species_from_filename(path)

    base_row: Dict = {
        "species": species_name,
        "species_acronym": species_acronym,
        "csv_id": row.get("EdgeID"),
        "edge_id": row.get("EdgeID"),
        "protein_a_locus_tag": locus_a,
        "protein_b_locus_tag": locus_b,
        "consensus_score": _flt(row.get("Score")),
        "consensus_rank": _int(row.get("Rank")),
        "consensus_avg_rank": _flt(row.get("AvgRank")),
    }

    # Map evidence channel weights
    for tsv_col, field_name in CONSENSUS_WEIGHT_COLUMN_MAP.items():
        base_row[field_name] = _flt(row.get(tsv_col))

    # Legacy abundance/perturbation scores: use positive weight when available
    gp_pos = base_row.get("weight_ppi_gp_score_pos")
    gp_neg = base_row.get("weight_ppi_gp_score_neg")
    base_row["abundance_score"] = gp_pos if gp_pos is not None else gp_neg

    perturb_pos = base_row.get("weight_ppi_perturb_score_pos")
    perturb_neg = base_row.get("weight_ppi_perturb_score_neg")
    base_row["perturbation_score"] = perturb_pos if perturb_pos is not None else perturb_neg

    # Resolve protein IDs and gene metadata from GFF (locus-tag keyed)
    if gff_parser and species_name:
        gene_a, gene_b = gff_parser.get_gene_info_for_proteins(species_name, locus_a, locus_b)
        base_row.update(_add_gene_info_to_row(gene_a, gene_b))
        base_row["protein_a"] = (
            gene_a.uniprot_id if gene_a and gene_a.uniprot_id else None
        ) or locus_a
        base_row["protein_b"] = (
            gene_b.uniprot_id if gene_b and gene_b.uniprot_id else None
        ) or locus_b
    else:
        base_row["protein_a"] = locus_a
        base_row["protein_b"] = locus_b

    return base_row


def _parse_legacy_csv_row(
    row: Dict[str, str],
    gff_parser: Optional[GFFParser] = None,
) -> Dict:
    """Parse a legacy PPI CSV row."""
    base_row = {
        "species": row.get("species"),
        "csv_id": row.get("id"),
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

    if gff_parser:
        species = base_row["species"]
        protein_a = base_row["protein_a"]
        protein_b = base_row["protein_b"]

        if species:
            gene_a, gene_b = gff_parser.get_gene_info_for_proteins(species, protein_a, protein_b)
            base_row.update(_add_gene_info_to_row(gene_a, gene_b))

    return base_row


def _is_consensus_format(fieldnames: Optional[List[str]]) -> bool:
    return bool(fieldnames and "GeneA" in fieldnames and "Score" in fieldnames)


def iter_ppi_rows(
    folder: str, pattern: str = "*.csv", gff_parser: Optional[GFFParser] = None
) -> Iterator[Dict]:
    """Yield normalized rows from PPI CSV/TSV files in `folder` matching pattern."""
    for path in sorted(glob.glob(os.path.join(folder, pattern))):
        with open(path, "r", newline="", encoding="utf-8") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters="\t,")
            except csv.Error:
                dialect = csv.excel_tab if "\t" in sample.splitlines()[0] else csv.excel

            reader = csv.DictReader(f, dialect=dialect)
            fieldnames = reader.fieldnames or []

            if _is_consensus_format(fieldnames):
                logger.info(f"[ppi] Parsing consensus TSV format: {path}")
                for row in reader:
                    yield _parse_consensus_row(row, path, gff_parser)
            else:
                missing = set(["species", "protein_a", "protein_b"]) - set(fieldnames)
                if missing:
                    raise ValueError(f"PPI file missing columns {missing} in {path}")
                logger.info(f"[ppi] Parsing legacy CSV format: {path}")
                for row in reader:
                    yield _parse_legacy_csv_row(row, gff_parser)


def _add_gene_info_to_row(gene_a: Optional[GeneInfo], gene_b: Optional[GeneInfo]) -> Dict:
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
