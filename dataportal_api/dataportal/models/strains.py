"""
Strain document model for Elasticsearch.

This module defines the StrainDocument class for indexing strain information
including drug MIC data, drug metabolism, and contig information.
"""

from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    Long,
    Nested,
    ScaledFloat,
)

from .base import autocomplete_analyzer, lowercase_normalizer


class StrainDocument(Document):
    """Elasticsearch document for strain information."""
    
    strain_id = Keyword()

    species_scientific_name = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    species_acronym = Keyword(normalizer=lowercase_normalizer)

    isolate_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword(normalizer=lowercase_normalizer)},
    )
    isolate_key = Keyword()  # data cleanup resolver attribute

    assembly_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    assembly_accession = Keyword()

    fasta_file = Keyword()
    gff_file = Keyword()  # Nullable
    type_strain = Boolean()

    # Rollups for UI / sorting
    contig_count = Integer()
    genome_size = Long()

    # Contigs
    contigs = Nested(properties={
        "seq_id": Keyword(),
        "length": Integer()
    })

    # ---- Drug MIC (growth inhibition / MIC-like) ----
    drug_mic = Nested(properties={
        # drug metadata (all optional)
        "drug_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "drug_class": Keyword(normalizer=lowercase_normalizer),
        "drug_subclass": Keyword(normalizer=lowercase_normalizer),
        "compound_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "pubchem_id": Keyword(),

        # measurements
        "relation": Keyword(),  # '=', '>', '<=', etc.
        "mic_value": ScaledFloat(scaling_factor=1000),  # 0.001 precision (e.g., µM or mg/L)
        "unit": Keyword(),  # 'uM', 'mg/L'

        # experimental context (if/when available)
        "experimental_condition_id": Integer(),
        "experimental_condition_name": Keyword(normalizer=lowercase_normalizer)
    })

    # ---- Drug Metabolism ----
    drug_metabolism = Nested(properties={
        # drug metadata (all optional)
        "drug_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "drug_class": Keyword(normalizer=lowercase_normalizer),
        "drug_subclass": Keyword(normalizer=lowercase_normalizer),
        "compound_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "pubchem_id": Keyword(),

        # measurements
        "degr_percent": ScaledFloat(scaling_factor=10000),  # 0.0001 precision
        "pval": ScaledFloat(scaling_factor=1000000),
        "fdr": ScaledFloat(scaling_factor=1000000),
        "metabolizer_classification": Keyword(normalizer=lowercase_normalizer),

        # convenience flags for filtering
        "is_significant": Boolean(),  # e.g., fdr < 0.05

        # experimental context (optional)
        "experimental_condition_id": Integer(),
        "experimental_condition_name": Keyword(normalizer=lowercase_normalizer)
    })

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
        """Set `_id` as `isolate_name`."""
        self.meta.id = self.isolate_name
        return super().save(**kwargs)
