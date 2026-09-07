"""Elasticsearch document for gene-level experimental payloads (current annotation only)."""

from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    Nested,
    Float,
)

from .base import autocomplete_analyzer, lowercase_normalizer


class GeneExperimentDocument(Document):
    """Experimental nested data keyed by locus_tag (stable across annotation releases)."""

    feature_id = Keyword()
    feature_type = Keyword(normalizer=lowercase_normalizer)
    locus_tag = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    uniprot_id = Keyword()
    gene_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    product = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    isolate_name = Keyword()
    species_scientific_name = Keyword()
    species_acronym = Keyword(normalizer=lowercase_normalizer)

    has_proteomics = Boolean()
    has_fitness = Boolean()
    has_mutant_growth = Boolean()
    has_reactions = Boolean()

    protein_compound = Nested(
        properties={
            "compound": Keyword(),
            "ttp_score": Float(),
            "fdr": Float(),
            "hit_calling": Boolean(),
            "experimental_condition": Keyword(),
            "notes": Text(fields={"keyword": Keyword()}),
            "assay": Keyword(),
            "poolA": Keyword(),
            "poolB": Keyword(),
        }
    )

    fitness = Nested(
        properties={
            "experimental_condition": Keyword(),
            "media": Keyword(),
            "contrast": Keyword(),
            "lfc": Float(),
            "fdr": Float(),
            "number_of_barcodes": Integer(),
        }
    )

    reactions = Keyword(multi=True)
    reaction_details = Nested(
        properties={
            "reaction": Keyword(),
            "gpr": Text(fields={"keyword": Keyword()}),
            "substrates": Keyword(multi=True),
            "products": Keyword(multi=True),
            "metabolites": Keyword(multi=True),
        }
    )

    mutant_growth = Nested(
        properties={
            "doubling_time": Float(),
            "isdoublepicked": Boolean(),
            "brep": Keyword(),
            "plate384": Integer(),
            "well384": Keyword(),
            "percent_from_start": Float(),
            "media": Keyword(),
            "experimental_condition": Keyword(),
        }
    )

    proteomics = Nested(
        properties={
            "coverage": Float(),
            "unique_peptides": Integer(),
            "unique_intensity": Float(),
            "evidence": Boolean(),
        }
    )

    class Index:
        name = "gene_experiment_index"
        settings = {
            "index": {"max_result_window": 500000},
            "analysis": {
                "analyzer": {"autocomplete_analyzer": autocomplete_analyzer},
                "tokenizer": {"edge_ngram_tokenizer": autocomplete_analyzer.tokenizer},
                "normalizer": {"lowercase_normalizer": lowercase_normalizer},
            },
        }
        dynamic = "true"

    def save(self, **kwargs):
        if not getattr(self, "feature_id", None):
            self.feature_id = getattr(self, "locus_tag", None)
        self.meta.id = self.feature_id
        return super().save(**kwargs)
