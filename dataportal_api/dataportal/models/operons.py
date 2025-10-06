"""
Operon document model for Elasticsearch.

This module defines the OperonDocument class for indexing operon information
and gene composition.
"""

from elasticsearch_dsl import Document, Keyword, Integer, Boolean, Text


class OperonDocument(Document):
    """Elasticsearch document for operon information."""
    
    operon_id = Keyword(required=True)
    isolate_name = Keyword()
    species_acronym = Keyword()
    species_scientific_name = Keyword()

    # composition
    genes = Keyword(multi=True)
    gene_count = Integer()

    # gene A details
    gene_a_locus_tag = Keyword()
    gene_a_uniprot_id = Keyword()
    gene_a_name = Keyword()
    gene_a_product = Text()
    gene_a_isolate_name = Keyword()

    # gene B details
    gene_b_locus_tag = Keyword()
    gene_b_uniprot_id = Keyword()
    gene_b_name = Keyword()
    gene_b_product = Text()
    gene_b_isolate_name = Keyword()

    # rollups
    has_tss = Boolean()
    has_terminator = Boolean()

    class Index:
        name = "operon_index"
        settings = {"index": {"max_result_window": 500_000}}
