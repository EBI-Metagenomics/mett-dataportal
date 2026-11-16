"""
Protein-protein interaction document model for Elasticsearch.

This module defines the ProteinProteinDocument class for indexing protein-protein
interactions with various scoring metrics and experimental evidence.
"""

from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    Double,
    ScaledFloat,
)

from .base import (
    autocomplete_analyzer,
    lowercase_normalizer,
    canonical_pair,
    build_pair_id,
)
from dataportal.utils.constants import PPI_EVIDENCE_CATEGORIES, PPI_INDEXED_SCORE_FIELDS
from dataportal.utils.ppi_scores import apply_ppi_v4_rollups


class ProteinProteinDocument(Document):
    """Elasticsearch document for protein-protein interactions."""

    # ---- Identity / keys ----
    species_scientific_name = Keyword()  # e.g., "Bacteroides uniformis"
    species_acronym = Keyword(normalizer=lowercase_normalizer)  # e.g., "BU"
    # Optional isolate, if/when you scope PPIs more granularly
    isolate_name = Keyword()  # nullable

    # Participants (undirected)
    protein_a = Keyword()
    protein_b = Keyword()
    participants = Keyword(multi=True)  # [protein_a, protein_b] (order does not matter)
    participants_sorted = Keyword(multi=True)  # [min(a,b), max(a,b)] for symmetric queries
    # Optional locus-tag level participants (for locus-centric queries/aggregations)
    participants_locus_tag = Keyword(multi=True)
    participants_locus_tag_sorted = Keyword(multi=True)
    pair_id = Keyword()  # "{species}:{min}__{max}" – set as _id
    is_self_interaction = Boolean()  # convenience flag when a == b

    # ---- Gene Information for protein_a ----
    protein_a_locus_tag = Keyword()
    protein_a_uniprot_id = Keyword()
    protein_a_name = Keyword()
    protein_a_seqid = Keyword()
    protein_a_source = Keyword()
    protein_a_type = Keyword()
    protein_a_start = Integer()
    protein_a_end = Integer()
    protein_a_score = ScaledFloat(scaling_factor=1_000_000)
    protein_a_strand = Keyword()
    protein_a_phase = Keyword()
    protein_a_product = Text()

    # ---- Gene Information for protein_b ----
    protein_b_locus_tag = Keyword()
    protein_b_uniprot_id = Keyword()
    protein_b_name = Keyword()
    protein_b_seqid = Keyword()
    protein_b_source = Keyword()
    protein_b_type = Keyword()
    protein_b_start = Integer()
    protein_b_end = Integer()
    protein_b_score = ScaledFloat(scaling_factor=1_000_000)
    protein_b_strand = Keyword()
    protein_b_phase = Keyword()
    protein_b_product = Text()

    # ---- External identifiers (e.g. STRING) ----
    # These allow direct linking out to external PPI resources.
    string_protein_a_id = Keyword()
    string_protein_b_id = Keyword()

    # ---- PPI v4 scores ----
    # Double keeps the full TSV precision (scaled_float rounded category scores).
    consensus_score = Double()
    raw_consensus_score = Double()
    consensus_rank = Integer()
    edge_id = Keyword()
    q_ppi = Double()
    q_chemical_genetic = Double()
    q_coexpression = Double()
    q_operons = Double()
    q_metabolic = Double()

    # How many evidence categories and underlying networks support the edge.
    n_evidence_types = Integer()
    n_networks_total = Integer()
    n_ppi = Integer()
    n_chemical_genetic = Integer()
    n_coexpression = Integer()
    n_operons = Integer()
    n_metabolic = Integer()

    # ---- Experimental context ----
    experimental_condition_id = Integer()  # from SP2_ppi_interaction
    experimental_condition = Keyword()  # optional human-friendly label

    # Category presence flags for filtering
    has_ppi = Boolean()
    has_chemical_genetic = Boolean()
    has_coexpression = Boolean()
    has_operons = Boolean()
    has_metabolic = Boolean()

    # Number of evidence categories (n_evidence_types), or legacy network total.
    evidence_count = Integer()

    class Index:
        name = "ppi_index"
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
        # Enforce canonical undirected identity before saving
        aa, bb = canonical_pair(self.protein_a, self.protein_b)
        self.participants = [self.protein_a, self.protein_b]
        self.participants_sorted = [aa, bb]
        self.is_self_interaction = aa == bb

        # Build id; species_acronym should be present (fallback to scientific name if needed)
        species_key = getattr(self, "species_acronym", None) or getattr(
            self, "species_scientific_name", "na"
        )
        self.pair_id = build_pair_id(species_key, aa, bb)
        self.meta.id = self.pair_id

        rolled = {field: getattr(self, field, None) for field in PPI_INDEXED_SCORE_FIELDS}
        apply_ppi_v4_rollups(rolled)
        for _, _, flag_field in PPI_EVIDENCE_CATEGORIES:
            setattr(self, flag_field, rolled[flag_field])
        self.evidence_count = rolled["evidence_count"]

        return super().save(**kwargs)
