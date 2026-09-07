"""
Strain document model for Elasticsearch.

Identity, assembly, and current-annotation pointers. Strain-level assays live in strain_experiment_index.
"""

from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    Long,
    Nested,
)

from .base import autocomplete_analyzer, lowercase_normalizer


class StrainDocument(Document):
    """Elasticsearch document for strain / genome listing."""

    strain_id = Keyword()

    species_scientific_name = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    species_acronym = Keyword(normalizer=lowercase_normalizer)

    isolate_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword(normalizer=lowercase_normalizer)},
    )
    isolate_key = Keyword()

    assembly_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    assembly_accession = Keyword()

    fasta_file = Keyword()
    gff_file = Keyword()
    type_strain = Boolean()

    contig_count = Integer()
    genome_size = Long()

    contigs = Nested(properties={"seq_id": Keyword(), "length": Integer()})

    current_annotation_run_id = Keyword()
    current_annotation_release = Keyword()
    annotation_doc_link = Keyword()
    mettannotator_version = Keyword()
    pipeline_version = Keyword()

    class Index:
        name = "strain_index"
        settings = {
            "analysis": {
                "analyzer": {"autocomplete_analyzer": autocomplete_analyzer},
                "tokenizer": {"edge_ngram_tokenizer": autocomplete_analyzer.tokenizer},
                "normalizer": {"lowercase_normalizer": lowercase_normalizer},
            }
        }

    def save(self, **kwargs):
        self.meta.id = self.isolate_name
        return super().save(**kwargs)
