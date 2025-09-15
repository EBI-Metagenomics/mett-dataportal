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
    ScaledFloat,
)

from .base import autocomplete_analyzer, lowercase_normalizer, canonical_pair, build_pair_id


class ProteinProteinDocument(Document):
    """Elasticsearch document for protein-protein interactions."""
    
    # ---- Identity / keys ----
    species_scientific_name = Keyword()                         # e.g., "Bacteroides uniformis"
    species_acronym = Keyword(normalizer=lowercase_normalizer)  # e.g., "BU"
    # Optional isolate, if/when you scope PPIs more granularly
    isolate_name = Keyword()                                    # nullable

    # Participants (undirected)
    protein_a = Keyword()
    protein_b = Keyword()
    participants = Keyword(multi=True)      # [protein_a, protein_b] (order does not matter)
    participants_sorted = Keyword(multi=True)  # [min(a,b), max(a,b)] for symmetric queries
    pair_id = Keyword()                     # "{species}:{min}__{max}" – set as _id
    is_self_interaction = Boolean()         # convenience flag when a == b

    # ---- Scores / evidence (ScaledFloat keeps storage compact & sortable) ----
    # Use scaling_factor=1e6 to preserve up to ~6 decimal places and allow negatives.
    dl_score             = ScaledFloat(scaling_factor=1_000_000)     # "ds_score" in CSV?
    comelt_score         = ScaledFloat(scaling_factor=1_000_000)     # "melt_score" / "comelt" variants
    perturbation_score   = ScaledFloat(scaling_factor=1_000_000)     # "perturb_score"
    abundance_score      = ScaledFloat(scaling_factor=1_000_000)     # "gp_score" (global proteomics)
    melt_score           = ScaledFloat(scaling_factor=1_000_000)     # "melt_score" (if distinct)
    secondary_score      = ScaledFloat(scaling_factor=1_000_000)     # "sec_score"
    bayesian_score       = ScaledFloat(scaling_factor=1_000_000)     # "bn_score"
    string_score         = ScaledFloat(scaling_factor=1_000_000)     # "string_physical_score"
    operon_score         = ScaledFloat(scaling_factor=1_000_000)
    ecocyc_score         = ScaledFloat(scaling_factor=1_000_000)
    tt_score             = ScaledFloat(scaling_factor=1_000_000)     # "tt_score" in CSV
    ds_score             = ScaledFloat(scaling_factor=1_000_000)     # "ds_score" in CSV (keep both if needed)

    # ---- Experimental context ----
    experimental_condition_id = Integer()       # from SP2_ppi_interaction
    experimental_condition    = Keyword()       # optional human-friendly label

    # ---- XL-MS & external evidence ----
    xlms_peptides = Text()                      # free text list from CSV / DB
    xlms_files    = Keyword(multi=True)         # split on delimiters into array if possible

    # Quick evidence flags for filtering
    has_xlms      = Boolean()
    has_string    = Boolean()
    has_operon    = Boolean()
    has_ecocyc    = Boolean()
    has_experimental = Boolean()                # e.g., co-melt/perturb present

    # Optional rollups for UI
    evidence_count = Integer()                  # how many sources contributed (non-null scores)
    confidence_bin = Keyword(normalizer=lowercase_normalizer)  # "high" | "medium" | "low" (set at ingest)

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
        self.is_self_interaction = (aa == bb)

        # Build id; species_acronym should be present (fallback to scientific name if needed)
        species_key = getattr(self, "species_acronym", None) or getattr(self, "species_scientific_name", "na")
        self.pair_id = build_pair_id(species_key, aa, bb)
        self.meta.id = self.pair_id

        # Convenience flags
        self.has_xlms = bool(self.xlms_peptides or self.xlms_files)
        self.has_string = self.string_score is not None
        self.has_operon = self.operon_score is not None
        self.has_ecocyc = self.ecocyc_score is not None
        self.has_experimental = any(
            s is not None for s in [
                self.comelt_score, self.perturbation_score, self.abundance_score, self.melt_score,
                self.secondary_score, self.bayesian_score, self.tt_score, self.ds_score
            ]
        )

        # Rollup counts & bins
        numeric_scores = [
            self.dl_score, self.comelt_score, self.perturbation_score, self.abundance_score,
            self.melt_score, self.secondary_score, self.bayesian_score, self.string_score,
            self.operon_score, self.ecocyc_score, self.tt_score, self.ds_score
        ]
        self.evidence_count = sum(1 for v in numeric_scores if v is not None)

        # Example binning heuristic (adjust during ingest as you learn ranges)
        if (self.string_score and self.string_score >= 0.7) or self.evidence_count >= 4:
            self.confidence_bin = "high"
        elif (self.string_score and self.string_score >= 0.4) or self.evidence_count >= 2:
            self.confidence_bin = "medium"
        else:
            self.confidence_bin = "low"

        return super().save(**kwargs)
