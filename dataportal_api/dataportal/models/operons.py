"""
Operon document model for Elasticsearch.

This module defines the OperonDocument class for indexing operon information
and gene composition.
"""

from elasticsearch_dsl import Document, Keyword, Integer, Boolean


class OperonDocument(Document):
    """Elasticsearch document for operon information."""
    
    operon_id = Keyword(required=True)
    isolate_name = Keyword()
    species_acronym = Keyword()
    species_scientific_name = Keyword()

    # composition
    genes = Keyword(multi=True)
    gene_count = Integer()

    # rollups
    has_tss = Boolean()
    has_terminator = Boolean()

    class Index:
        name = "operon_index"
        settings = {"index": {"max_result_window": 500_000}}
