"""
Ortholog document model for Elasticsearch.

This module defines the OrthologDocument class for indexing ortholog relationships
between genes across different species.
"""

from elasticsearch_dsl import Document, Keyword, Text, Integer


class OrthologDocument(Document):
    """Elasticsearch document for ortholog relationships."""
    
    pair_id = Keyword()
    locus_a = Keyword()
    locus_b = Keyword()
    desc_a = Text()
    desc_b = Text()
    species_a = Keyword()
    species_b = Keyword()
    orthology_type = Keyword()
    oma_group_id = Integer()

    class Index:
        name = "ortholog_index"
        settings = {"index": {"max_result_window": 500000}}
