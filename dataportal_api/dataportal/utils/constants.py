# Router configuration
ROUTER_GENOME = "Genomes"
ROUTER_GENE = "Genes"
ROUTER_SPECIES = "Species"
URL_PREFIX_SPECIES = "/species"
URL_PREFIX_GENOMES = "/genomes"
URL_PREFIX_GENES = "/genes"

# Generic constants
FIELD_ID = "id"
FIELD_SEQ_ID = "seq_id"
FIELD_ASSEMBLY = "assembly"
SORT_ASC = "asc"
SORT_DESC = "desc"
DEFAULT_SORT = SORT_ASC
DEFAULT_PER_PAGE_CNT = 10

# Gene-related constants
GENE_FIELD_ID = "gene_id"
GENE_FIELD_NAME = "gene_name"
GENE_FIELD_PRODUCT = "product"
GENE_FIELD_DESCRIPTION = "description"
GENE_FIELD_LOCUS_TAG = "locus_tag"
GENE_FIELD_COG = "cog"
GENE_FIELD_KEGG = "kegg"
GENE_FIELD_PFAM = "pfam"
GENE_FIELD_INTERPRO = "interpro"
GENE_FIELD_DBXREF = "dbxref"
GENE_FIELD_EC_NUMBER = "ec_number"
GENE_FIELD_START_POS = "start_position"
GENE_FIELD_END_POS = "end_position"
GENE_FIELD_START = "start"
GENE_FIELD_END = "end"
GENE_FIELD_ANNOTATIONS = "annotations"
GENE_ESSENTIALITY_DATA = "essentiality_data"
GENE_DEFAULT_SORT_FIELD = "gene_name"
GENE_SORT_FIELD_STRAIN = "strain"
GENE_SORT_FIELD_STRAIN_ISO = "strain__isolate_name"
GENE_ESSENTIALITY = "essentiality"
GENE_ESSENTIALITY_MEDIA = "media"
GENE_ESSENTIALITY_SOLID = "solid"
GENE_ESSENTIALITY_LIQUID = "liquid"

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
STRAIN_FIELD_SPECIES_ACRONYM = "species_acronym"

# species related constants
SPECIES_FIELD_SCIENTIFIC_NAME = "scientific_name"
SPECIES_FIELD_COMMON_NAME = "common_name"
SPECIES_FIELD_ACRONYM = "acronym"

FILTER_MAPPING = {
    GENE_ESSENTIALITY: "essentiality_data__essentiality__name",
    GENE_ESSENTIALITY_MEDIA: "essentiality_data__media",
    GENE_FIELD_PRODUCT: GENE_FIELD_PRODUCT,
    GENE_FIELD_DESCRIPTION: GENE_FIELD_DESCRIPTION,
}
