"""
Centralized constants for METT DataPortal.

This module contains all constant values used throughout the application,
organized by category for easy maintenance and discovery.

Organization:
    1. Application Configuration
    2. Elasticsearch Indexes
    3. Field Names - Core Entities
    4. Field Names - Experimental Data
    5. Boolean Flags
    6. Default Values & Enums
    7. Search Configuration
    8. Interaction Data (PPI, TTP)
    9. Backward Compatibility (Deprecated)
"""

# ============================================================================
# 1. APPLICATION CONFIGURATION
# ============================================================================

# --- Pagination ---
DEFAULT_PAGE_SIZE = 20
MAX_RESULTS_PER_PAGE = 1000

# --- Sorting ---
SORT_DIRECTION_ASC = "asc"
SORT_DIRECTION_DESC = "desc"
DEFAULT_SORT_DIRECTION = SORT_DIRECTION_ASC

# --- Search & Faceting ---
DEFAULT_FACET_LIMIT = 10000

# --- Scroll API ---
SCROLL_BATCH_SIZE = 10000
SCROLL_MAX_RESULTS = 1000000
SCROLL_TIMEOUT = "5m"

# ============================================================================
# 2. ELASTICSEARCH INDEXES
# ============================================================================

INDEX_FEATURES = "feature_index"
INDEX_STRAINS = "strain_index"
INDEX_SPECIES = "species_index"
INDEX_PPI = "ppi_index"
INDEX_ORTHOLOGS = "ortholog_index"
INDEX_OPERONS = "operon_index"
INDEX_STRAIN_EXPERIMENTS = "strain_experiment_index"
INDEX_GENE_EXPERIMENTS = "gene_experiment_index"

DEFAULT_ANNOTATION_RELEASE = "1.0"
DEFAULT_METTANNOTATOR_VERSION = "1.0"
DEFAULT_PIPELINE_VERSION = "1.0"
DEFAULT_ANNOTATION_DOC_LINK = "https://github.com/EBI-Metagenomics/mettannotator/releases/tag/v1.0"

# ============================================================================
# 3. FIELD NAMES - CORE ENTITIES
# ============================================================================

# --- Generic/Common Fields ---
FIELD_ID = "id"
FIELD_SEQ_ID = "seq_id"
FIELD_ASSEMBLY = "assembly"

# --- Gene Fields ---
GENE_FIELD_LOCUS_TAG = "locus_tag"
GENE_FIELD_NAME = "gene_name"
GENE_FIELD_ALIAS = "alias"
GENE_FIELD_PRODUCT = "product"
GENE_FIELD_UNIPROT_ID = "uniprot_id"
GENE_FIELD_FEATURE_TYPE = "feature_type"

# Gene - Genomic Coordinates
GENE_FIELD_START = "start"
GENE_FIELD_END = "end"
GENE_FIELD_START_POSITION = "start_position"
GENE_FIELD_END_POSITION = "end_position"

# Gene - Functional Annotations
GENE_FIELD_COG_ID = "cog_id"
GENE_FIELD_COG_FUNCATS = "cog_funcats"
GENE_FIELD_KEGG = "kegg"
GENE_FIELD_PFAM = "pfam"
GENE_FIELD_INTERPRO = "interpro"
GENE_FIELD_EGGNOG = "eggnog"
GENE_FIELD_GO_TERM = "go_term"
GENE_FIELD_EC_NUMBER = "ec_number"
GENE_FIELD_DBXREF = "dbxref"
GENE_FIELD_ANNOTATIONS = "annotations"

# Gene - AMR Data
GENE_FIELD_AMR = "amr"
GENE_FIELD_AMR_DRUG_CLASS = "drug_class"
GENE_FIELD_AMR_DRUG_SUBCLASS = "drug_subclass"

# Gene - Essentiality
GENE_FIELD_ESSENTIALITY = "essentiality"

# Gene - Default Sort
GENE_DEFAULT_SORT_FIELD = "gene_name"
GENE_SORT_FIELD_STRAIN = "strain"

# --- Genome/Strain Fields ---
GENOME_FIELD_ISOLATE_NAME = "isolate_name"
GENOME_FIELD_ASSEMBLY_NAME = "assembly_name"
GENOME_FIELD_ASSEMBLY_ACCESSION = "assembly_accession"
GENOME_FIELD_FASTA_FILE = "fasta_file"
GENOME_FIELD_GFF_FILE = "gff_file"
GENOME_FIELD_FASTA_URL = "fasta_url"
GENOME_FIELD_GFF_URL = "gff_url"
GENOME_FIELD_SPECIES = "species"
GENOME_FIELD_CONTIGS = "contigs"
GENOME_FIELD_TYPE_STRAIN = "type_strain"
GENOME_FIELD_CURRENT_ANNOTATION_RUN_ID = "current_annotation_run_id"
GENOME_FIELD_CURRENT_ANNOTATION_RELEASE = "current_annotation_release"
GENOME_FIELD_ANNOTATION_DOC_LINK = "annotation_doc_link"
GENE_FIELD_ANNOTATION_RUN_ID = "annotation_run_id"
GENE_FIELD_ANNOTATION_RELEASE = "annotation_release"

# Genome - Contig Fields
GENOME_CONTIG_FIELD_SEQ_ID = "seq_id"
GENOME_CONTIG_FIELD_LENGTH = "length"

# --- Species Fields ---
SPECIES_FIELD_SCIENTIFIC_NAME = "scientific_name"
SPECIES_FIELD_COMMON_NAME = "common_name"
SPECIES_FIELD_ACRONYM = "acronym"
SPECIES_FIELD_ACRONYM_SHORT = "species_acronym"

# ============================================================================
# 4. FIELD NAMES - EXPERIMENTAL DATA
# ============================================================================

# --- Proteomics Fields ---
PROTEOMICS_FIELD_COVERAGE = "coverage"
PROTEOMICS_FIELD_UNIQUE_PEPTIDES = "unique_peptides"
PROTEOMICS_FIELD_UNIQUE_INTENSITY = "unique_intensity"
PROTEOMICS_FIELD_EVIDENCE = "evidence"

# --- Essentiality Fields ---
ESSENTIALITY_FIELD_DATA = "essentiality_data"
ESSENTIALITY_FIELD_TAS_IN_LOCUS = "TAs_in_locus"
ESSENTIALITY_FIELD_TAS_HIT = "TAs_hit"
ESSENTIALITY_FIELD_CALL = "essentiality_call"
ESSENTIALITY_FIELD_CONDITION = "experimental_condition"
ESSENTIALITY_FIELD_ELEMENT = "element"

# --- Fitness Fields ---
FITNESS_FIELD_DATA = "fitness"
FITNESS_FIELD_LFC = "lfc"
FITNESS_FIELD_FDR = "fdr"
FITNESS_FIELD_MEDIA = "media"
FITNESS_FIELD_CONDITION = "experimental_condition"
FITNESS_FIELD_CONTRAST = "contrast"
FITNESS_FIELD_BARCODES = "number_of_barcodes"

# --- Mutant Growth Fields ---
MUTANT_GROWTH_FIELD_DATA = "mutant_growth"
MUTANT_GROWTH_FIELD_DOUBLING_TIME = "doubling_time"
MUTANT_GROWTH_FIELD_IS_DOUBLE_PICKED = "isdoublepicked"
MUTANT_GROWTH_FIELD_BREP = "brep"
MUTANT_GROWTH_FIELD_PLATE = "plate384"
MUTANT_GROWTH_FIELD_WELL = "well384"
MUTANT_GROWTH_FIELD_PERCENT_FROM_START = "percent_from_start"
MUTANT_GROWTH_FIELD_MEDIA = "media"
MUTANT_GROWTH_FIELD_CONDITION = "experimental_condition"

# --- Reactions Fields ---
REACTIONS_FIELD_LIST = "reactions"
REACTIONS_FIELD_DETAILS = "reaction_details"
REACTIONS_FIELD_REACTION_ID = "reaction"
REACTIONS_FIELD_GPR = "gpr"
REACTIONS_FIELD_SUBSTRATES = "substrates"
REACTIONS_FIELD_PRODUCTS = "products"
REACTIONS_FIELD_METABOLITES = "metabolites"

# ============================================================================
# 5. BOOLEAN FLAGS (has_* fields)
# ============================================================================

FLAG_HAS_PROTEOMICS = "has_proteomics"
FLAG_HAS_ESSENTIALITY = "has_essentiality"
FLAG_HAS_FITNESS = "has_fitness"
FLAG_HAS_MUTANT_GROWTH = "has_mutant_growth"
FLAG_HAS_REACTIONS = "has_reactions"
FLAG_HAS_AMR_INFO = "has_amr_info"

# ============================================================================
# 6. DEFAULT VALUES & ENUMS
# ============================================================================

# --- Essentiality Values ---
ESSENTIALITY_UNKNOWN = "Unknown"
ESSENTIALITY_CALL_ESSENTIAL = "essential"
ESSENTIALITY_CALL_NOT_ESSENTIAL = "not_essential"
ESSENTIALITY_CALL_ESSENTIAL_SOLID = "essential_solid"
ESSENTIALITY_CALL_ESSENTIAL_LIQUID = "essential_liquid"
ESSENTIALITY_CALL_UNCLEAR = "unclear"

# ============================================================================
# 7. SEARCH CONFIGURATION
# ============================================================================

# --- Gene Search Fields ---
GENE_SEARCH_FIELDS = [
    GENE_FIELD_NAME,
    GENE_FIELD_ALIAS,
    GENE_FIELD_PRODUCT,
    GENE_FIELD_PFAM,
    GENE_FIELD_INTERPRO,
]

# --- Faceted Search Fields ---
FACET_FIELDS = [
    GENE_FIELD_PFAM,
    GENE_FIELD_INTERPRO,
    GENE_FIELD_KEGG,
    GENE_FIELD_COG_ID,
    GENE_FIELD_COG_FUNCATS,
    GENE_FIELD_ESSENTIALITY,
    FLAG_HAS_AMR_INFO,
]

# --- Keyword Sort Fields (fields that need .keyword suffix for sorting) ---
KEYWORD_SORT_FIELDS = {
    GENE_FIELD_NAME,
    GENE_FIELD_ALIAS,
    FIELD_SEQ_ID,
    GENE_FIELD_LOCUS_TAG,
    GENE_FIELD_PRODUCT,
}

# ============================================================================
# 8. INTERACTION DATA (PPI, TTP)
# ============================================================================

# --- PPI Score Fields ---
PPI_SCORE_FIELDS = [
    "consensus_score",
    "ds_score",
    "comelt_score",
    "perturbation_score",
    "abundance_score",
    "melt_score",
    "secondary_score",
    "bayesian_score",
    "string_score",
    "operon_score",
    "ecocyc_score",
    "tt_score",
]

# --- Consensus network evidence channel weight fields (non-PPI channels) ---
PPI_EVIDENCE_WEIGHT_FIELDS = [
    "weight_coexp",
    "weight_operons_annogesic",
    "weight_operons_opdetect",
    "weight_operons_opmapper",
    "weight_phenocorr_neg",
    "weight_phenocorr_pos",
    "weight_pmi_gsms",
    "weight_pmi",
    "weight_ppi_gp_score_neg",
    "weight_ppi_gp_score_pos",
    "weight_ppi_perturb_score_neg",
    "weight_ppi_perturb_score_pos",
    "weight_ppi_xlms_files",
    "weight_ppi_xlms_peptides",
]

# Fields returned in edge/detail evidence_scores (exclude consensus — that is edge weight)
PPI_EVIDENCE_SCORE_FIELDS = [
    "weight_coexp",
    "weight_operons_annogesic",
    "weight_operons_opdetect",
    "weight_operons_opmapper",
    "weight_phenocorr_neg",
    "weight_phenocorr_pos",
    "weight_pmi_gsms",
    "weight_pmi",
    "bayesian_score",
    "ds_score",
    "ecocyc_score",
    "weight_ppi_gp_score_neg",
    "weight_ppi_gp_score_pos",
    "melt_score",
    "operon_score",
    "weight_ppi_perturb_score_neg",
    "weight_ppi_perturb_score_pos",
    "secondary_score",
    "string_score",
    "tt_score",
    "weight_ppi_xlms_files",
    "weight_ppi_xlms_peptides",
]

# Display labels for evidence channels (used by API / UI)
PPI_EVIDENCE_CHANNEL_LABELS = {
    "consensus_score": "Consensus",
    "weight_coexp": "Co-expression",
    "weight_operons_annogesic": "Operons (ANNOgesic)",
    "weight_operons_opdetect": "Operons (OpDetect)",
    "weight_operons_opmapper": "Operons (OpMapper)",
    "weight_phenocorr_neg": "Phenotype correlation (negative)",
    "weight_phenocorr_pos": "Phenotype correlation (positive)",
    "weight_pmi_gsms": "PMI (GSMs)",
    "weight_pmi": "PMI",
    "bayesian_score": "Bayesian network",
    "ds_score": "Deep learning",
    "ecocyc_score": "EcoCyc",
    "weight_ppi_gp_score_neg": "Global proteomics (negative)",
    "weight_ppi_gp_score_pos": "Global proteomics (positive)",
    "melt_score": "Thermal proteome profiling",
    "operon_score": "Operon score",
    "weight_ppi_perturb_score_neg": "Perturbation (negative)",
    "weight_ppi_perturb_score_pos": "Perturbation (positive)",
    "secondary_score": "Secondary structure",
    "string_score": "STRING physical",
    "tt_score": "Thermal tolerance",
    "weight_ppi_xlms_files": "XL-MS (files)",
    "weight_ppi_xlms_peptides": "XL-MS (peptides)",
    "comelt_score": "Co-melting",
    "perturbation_score": "Perturbation",
    "abundance_score": "Global proteomics",
    "interaction_weight": "Interaction weight",
    "n_sources": "Evidence sources",
}

# Default score used for network edge weight / ranking
PPI_DEFAULT_SCORE_TYPE = "consensus_score"

# --- PPI Non-Score Filter Fields ---
PPI_NON_SCORE_FIELDS = [
    "xlms_peptides",
    "xlms_files",
]

# --- All Valid PPI Filter Fields ---
PPI_VALID_FILTER_FIELDS = PPI_SCORE_FIELDS + PPI_NON_SCORE_FIELDS

# --- PPI Data Sources ---
# These represent logical sources of PPI interaction/network data.
# Kept generic so additional external or internal sources can be added
# without changing API contracts in many places.
PPI_DATA_SOURCE_LOCAL_ES = "local_es"
PPI_DATA_SOURCE_STRINGDB = "stringdb"

PPI_DATA_SOURCES = [
    PPI_DATA_SOURCE_LOCAL_ES,
    PPI_DATA_SOURCE_STRINGDB,
]


# STRING DB supported network types (https://string-db.org/help/api/)
STRING_NETWORK_TYPE_VALUES = ("physical", "functional")

# STRING DB evidence channels - map channel id to TSV score field name
# https://string-db.org/help/api/ - network output fields
STRING_EVIDENCE_CHANNELS = (
    ("neighborhood", "nscore", "Neighborhood"),
    ("fusion", "fscore", "Fusion"),
    ("cooccurrence", "pscore", "Co-occurrence"),
    ("coexpression", "ascore", "Co-expression"),
    ("experimental", "escore", "Experimental"),
    ("database", "dscore", "Database"),
    ("textmining", "tscore", "Text mining"),
)
STRING_EVIDENCE_CHANNEL_IDS = tuple(c[0] for c in STRING_EVIDENCE_CHANNELS)


# ============================================================================
# End of Constants
# ============================================================================
