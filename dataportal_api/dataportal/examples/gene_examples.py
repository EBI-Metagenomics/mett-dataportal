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
    "seq_id": "contig_1",
    "isolate_name": "BU_ATCC8492",
    "species_scientific_name": "Bacteroides uniformis",
    "species_acronym": "BU",
    "uniprot_id": "A7V2E8",
    "essentiality": "essential",
    "cog_funcats": ["L"],
    "pfam": ["PF00308", "PF08299", "PF11638"],
    "interpro": [
        "IPR001957",
        "IPR010921",
        "IPR013159",
        "IPR013317",
        "IPR020591",
        "IPR024633",
        "IPR027417",
        "IPR038454",
    ],
    "amr": [],
    "has_amr_info": False,
    "has_proteomics": True,
    "has_fitness": False,
    "has_mutant_growth": False,
    "has_reactions": False,
    "feature_type": "gene",
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
