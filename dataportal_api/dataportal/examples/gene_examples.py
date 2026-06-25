"""Reusable OpenAPI examples for gene-focused requests/responses."""

GENE_SEARCH_QUERY_EXAMPLE = {
    "query": "dna",
    "page": 1,
    "per_page": 25,
    "sort_field": "gene_name",
    "sort_order": "asc",
}

GENE_ADVANCED_SEARCH_QUERY_EXAMPLE = {
    "isolates": "BU_ATCC8492,PV_ATCC8482",
    "species_acronym": "BU",
    "query": "dna",
    "filter": "pfam:PF00669;interpro:IPR001621",
    "filter_operators": "pfam:AND;interpro:OR",
    "page": 2,
    "per_page": 25,
    "sort_field": "locus_tag",
    "sort_order": "desc",
    "seq_id": "contig_1",
    "start_position": 10000,
    "end_position": 25000,
}

GENE_DOWNLOAD_TSV_QUERY_EXAMPLE = {
    "isolates": "BU_ATCC8492",
    "species_acronym": "BU",
    "query": "",
    "filter": "essentiality:essential_liquid",
    "filter_operators": "essentiality:OR",
    "sort_field": "gene_name",
    "sort_order": "asc",
}

GENE_AUTOCOMPLETE_QUERY_EXAMPLE = {
    "query": "dnaA",
    "limit": 10,
    "species_acronym": "BU",
    "isolates": "BU_ATCC8492",
}

GENE_RESPONSE_EXAMPLE = {
    "locus_tag": "BU_ATCC8492_00001",
    "gene_name": "dnaA",
    "alias": ["BACUNI_01739"],
    "product": "Chromosomal replication initiator protein DnaA",
    "product_source": "Prokka",
    "start_position": 1,
    "end_position": 1386,
    "seq_id": "contig_1",
    "isolate_name": "BU_ATCC8492",
    "species_scientific_name": "Bacteroides uniformis",
    "species_acronym": "BU",
    "uniprot_id": "A7V2E8",
    "essentiality": "essential",
    "cog_funcats": ["L"],
    "cog_id": ["COG0593"],
    "pfam": ["PF00308", "PF08299", "PF11638"],
    "interpro": [
        "IPR001957",
        "IPR010921",
        "IPR013159",
    ],
    "ec_number": None,
    "dbxref": [{"db": "UniProt", "ref": "A7V2E8"}],
    "eggnog": None,
    "inference": "ab initio prediction:Prodigal:002006",
    "ontology_terms": [
        {"ontology_type": "GO", "ontology_id": "GO:0006270", "ontology_description": None}
    ],
    "uf_ontology_terms": ["GO:0003688", "GO:0005524"],
    "uf_prot_rec_fullname": "Chromosomal replication initiator protein DnaA",
    "uf_keyword": ["ATP-binding", "DNA-binding", "Cytoplasm"],
    "uf_gene_name": "dnaA",
    "amr": [],
    "has_amr_info": False,
    "has_proteomics": True,
    "has_fitness": False,
    "has_mutant_growth": False,
    "has_reactions": False,
    "feature_type": "gene",
    "unifire": {
        "gene_name": "dnaA",
        "keywords": ["ATP-binding", "DNA-binding", "Cytoplasm"],
        "protein_fullname": "Chromosomal replication initiator protein DnaA",
        "ontology_terms": ["GO:0003688", "GO:0005524"],
    },
}

GET_ALL_GENES_QUERY_EXAMPLE = {
    "page": 1,
    "per_page": 20,
    "sort_field": "gene_name",
    "sort_order": "asc",
}

ESSENTIALITY_BY_CONTIG_ENTRY_EXAMPLE = {
    "locus_tag": "BU_ATCC8492_01813",
    "start": 2309078,
    "end": 2309374,
    "essentiality": "not_essential",
}

__all__ = [
    "GENE_SEARCH_QUERY_EXAMPLE",
    "GENE_ADVANCED_SEARCH_QUERY_EXAMPLE",
    "GENE_DOWNLOAD_TSV_QUERY_EXAMPLE",
    "GENE_AUTOCOMPLETE_QUERY_EXAMPLE",
    "GENE_RESPONSE_EXAMPLE",
    "GET_ALL_GENES_QUERY_EXAMPLE",
    "ESSENTIALITY_BY_CONTIG_ENTRY_EXAMPLE",
]
