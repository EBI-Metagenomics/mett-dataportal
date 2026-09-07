"""Elasticsearch document for strain-level experimental payloads (current annotation only)."""

from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    Nested,
    ScaledFloat,
)

from .base import autocomplete_analyzer, lowercase_normalizer


class StrainExperimentDocument(Document):
    """One document per isolate; nested strain-level assays (MIC, metabolism, later others)."""

    isolate_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword(normalizer=lowercase_normalizer)},
    )
    species_scientific_name = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    species_acronym = Keyword(normalizer=lowercase_normalizer)

    drug_mic = Nested(
        properties={
            "drug_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
            "drug_class": Keyword(normalizer=lowercase_normalizer),
            "drug_subclass": Keyword(normalizer=lowercase_normalizer),
            "compound_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
            "pubchem_id": Keyword(),
            "relation": Keyword(),
            "mic_value": ScaledFloat(scaling_factor=1000),
            "unit": Keyword(),
            "experimental_condition_id": Integer(),
            "experimental_condition_name": Keyword(normalizer=lowercase_normalizer),
        }
    )

    drug_metabolism = Nested(
        properties={
            "drug_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
            "drug_class": Keyword(normalizer=lowercase_normalizer),
            "drug_subclass": Keyword(normalizer=lowercase_normalizer),
            "compound_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
            "pubchem_id": Keyword(),
            "degr_percent": ScaledFloat(scaling_factor=10000),
            "pval": ScaledFloat(scaling_factor=1000000),
            "fdr": ScaledFloat(scaling_factor=1000000),
            "metabolizer_classification": Keyword(normalizer=lowercase_normalizer),
            "is_significant": Boolean(),
            "experimental_condition_id": Integer(),
            "experimental_condition_name": Keyword(normalizer=lowercase_normalizer),
        }
    )

    class Index:
        name = "strain_experiment_index"
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
