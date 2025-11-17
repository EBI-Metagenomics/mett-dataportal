"""Reusable OpenAPI examples for gene-focused requests/responses."""

GENE_SEARCH_QUERY_EXAMPLE = {
    "query": "flagellin",
    "page": 1,
    "per_page": 25,
    "sort_field": "gene_name",
    "sort_order": "asc",
}

GENE_ADVANCED_SEARCH_QUERY_EXAMPLE = {
    "isolates": "BU_ATCC8492,PV_ATCC8482",
    "species_acronym": "BU",
    "query": "virulence",
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
    "query": "dnaK",
    "limit": 10,
    "species_acronym": "BU",
    "isolates": "BU_ATCC8492",
}

GENE_RESPONSE_EXAMPLE = {
    "locus_tag": "BU_ATCC8492_00001",
    "gene_name": "dnaK",
    "alias": ["HSP70"],
    "product": "Chaperone protein DnaK",
    "seq_id": "contig_1",
    "isolate_name": "BU_ATCC8492",
    "species_scientific_name": "Bacteroides uniformis",
    "species_acronym": "BU",
    "uniprot_id": "Q5NEJ5",
    "essentiality": "essential_liquid",
    "cog_funcats": ["O"],
    "pfam": ["PF00012"],
    "interpro": ["IPR012725"],
    "amr": [
        {
            "drug_class": "Glycopeptide",
            "drug_subclass": "Vancomycin",
        }
    ],
    "has_amr_info": True,
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
