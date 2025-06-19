# Generic constants

FIELD_ID = "id"
FIELD_SEQ_ID = "seq_id"
FIELD_ASSEMBLY = "assembly"
SORT_ASC = "asc"
SORT_DESC = "desc"
DEFAULT_SORT = SORT_ASC
DEFAULT_PER_PAGE_CNT = 20
DEFAULT_FACET_LIMIT = 10000

# Indexes
ES_INDEX_SPECIES = "species_index"
ES_INDEX_STRAIN = "strain_index"
ES_INDEX_GENE = "gene_index"

# Strain-related constants
STRAIN_FIELD_ISOLATE_NAME = "isolate_name"
STRAIN_FIELD_ASSEMBLY_NAME = "assembly_name"
STRAIN_FIELD_ASSEMBLY_ACCESSION = "assembly_accession"
STRAIN_FIELD_FASTA_FILE = "fasta_file"
STRAIN_FIELD_GFF_FILE = "gff_file"
STRAIN_FIELD_SPECIES = "species"
STRAIN_FIELD_FASTA_URL = "fasta_url"
STRAIN_FIELD_GFF_URL = "gff_url"
STRAIN_FIELD_CONTIGS = "contigs"
STRAIN_FIELD_CONTIG_SEQ_ID = "seq_id"
STRAIN_FIELD_CONTIG_LEN = "length"
STRAIN_FIELD_TYPE_STRAIN = "type_strain"

# species related constants
SPECIES_FIELD_SCIENTIFIC_NAME = "scientific_name"
SPECIES_FIELD_COMMON_NAME = "common_name"
SPECIES_FIELD_ACRONYM = "acronym"

# Gene-related constants
GENE_FIELD_DBXREF = "dbxref"
GENE_FIELD_EC_NUMBER = "ec_number"
GENE_FIELD_START_POS = "start_position"
GENE_FIELD_END_POS = "end_position"
GENE_FIELD_START = "start"
GENE_FIELD_END = "end"
GENE_FIELD_ANNOTATIONS = "annotations"
GENE_DEFAULT_SORT_FIELD = "gene_name"
GENE_SORT_FIELD_STRAIN = "strain"
GENE_ESSENTIALITY = "essentiality"

# Elasticsearch field constants
ES_FIELD_GENE_NAME = "gene_name"
ES_FIELD_ALIAS = "alias"
ES_FIELD_PRODUCT = "product"
ES_FIELD_LOCUS_TAG = "locus_tag"
ES_FIELD_SPECIES_SCIENTIFIC_NAME = "species_scientific_name"
ES_FIELD_SPECIES_ACRONYM = "species_acronym"
ES_FIELD_ISOLATE_NAME = "isolate_name"
ES_FIELD_KEGG = "kegg"
ES_FIELD_UNIPROT_ID = "uniprot_id"
ES_FIELD_PFAM = "pfam"
ES_FIELD_COG_ID = "cog_id"
ES_FIELD_COG_FUNCATS = "cog_funcats"
ES_FIELD_INTERPRO = "interpro"
ES_FIELD_EGGNOG = "eggnog"
ES_FIELD_AMR = "amr"
ES_FIELD_AMR_INFO = "has_amr_info"

# Search fields
GENE_SEARCH_FIELDS = [
    ES_FIELD_GENE_NAME,
    ES_FIELD_ALIAS,
    ES_FIELD_PRODUCT,
    ES_FIELD_PFAM,
    ES_FIELD_INTERPRO,
]

# Faceted Search Fields
FACET_FIELDS = [
    ES_FIELD_PFAM,
    ES_FIELD_INTERPRO,
    ES_FIELD_KEGG,
    ES_FIELD_COG_ID,
    ES_FIELD_COG_FUNCATS,
    GENE_ESSENTIALITY,
    ES_FIELD_AMR_INFO,
]

# Keyword sort fields
KEYWORD_SORT_FIELDS = {
    ES_FIELD_GENE_NAME,
    ES_FIELD_ALIAS,
    FIELD_SEQ_ID,
    ES_FIELD_LOCUS_TAG,
    ES_FIELD_PRODUCT,
}

# Default values
UNKNOWN_ESSENTIALITY = "Unknown"

# Hmmer Constants
