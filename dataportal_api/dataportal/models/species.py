"""
Species document model for Elasticsearch.

This module defines the SpeciesDocument class for indexing species information
in the METT Data Portal.
"""

from elasticsearch_dsl import Document, Text, Keyword, Integer, Boolean


class SpeciesDocument(Document):
    """Elasticsearch document for species information."""

    scientific_name = Text(fields={"keyword": Keyword()})
    common_name = Text()
    acronym = Keyword()
    taxonomy_id = Integer()
    enabled = Boolean()

    class Index:
        name = "species_index"

    def save(self, **kwargs):
        """Set `_id` as `acronym`."""
        self.meta.id = self.acronym
        return super().save(**kwargs)
