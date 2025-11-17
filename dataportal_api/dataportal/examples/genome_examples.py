"""Reusable Swagger/OpenAPI examples for genome-oriented payloads."""

GENOME_RESPONSE_EXAMPLE = {
    "species_scientific_name": "Bacteroides uniformis",
    "species_acronym": "BU",
    "isolate_name": "BU_ATCC8492",
    "assembly_name": "BU_ATCC8492VPI0062_NT5002",
    "assembly_accession": "",
    "fasta_file": "BU_ATCC8492VPI0062_NT5002.1.fa",
    "gff_file": "BU_ATCC8492_annotations.gff",
    "fasta_url": "https://ftp.ebi.ac.uk/pub/databases/mett/all_hd_isolates/deduplicated_assemblies/BU_ATCC8492VPI0062_NT5002.1.fa",
    "gff_url": "https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/BU_ATCC8492/functional_annotation/merged_gff/BU_ATCC8492_annotations.gff",
    "type_strain": True,
    "contigs": [
        {"seq_id": "contig_1", "length": 4200000},
        {"seq_id": "contig_2", "length": 600000},
    ],
}

GENOME_SEARCH_QUERY_EXAMPLE = {
    "query": "type strain",
    "page": 1,
    "per_page": 25,
    "sortField": "isolate_name",
    "sortOrder": "asc",
    "isolates": ["BU_ATCC8492", "PV_ATCC8482"],
    "species_acronym": "BU",
}


__all__ = [
    "GENOME_RESPONSE_EXAMPLE",
    "GENOME_SEARCH_QUERY_EXAMPLE",
]
