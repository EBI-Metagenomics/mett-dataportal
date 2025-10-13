"""
Gene fitness correlation document model for Elasticsearch.

This module defines the GeneFitnessCorrelationDocument class for indexing
pairwise gene fitness correlations derived from transposon sequencing experiments.
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


class GeneFitnessCorrelationDocument(Document):
    """Elasticsearch document for gene-gene fitness correlations."""
    
    # ---- Identity / Species Context ----
    species_scientific_name = Keyword()
    species_acronym = Keyword(normalizer=lowercase_normalizer)
    isolate_name = Keyword()
    
    # ---- Pair Identity (undirected, symmetric) ----
    gene_a = Keyword()                          # locus_tag of gene A
    gene_b = Keyword()                          # locus_tag of gene B
    genes = Keyword(multi=True)                 # [gene_a, gene_b] unordered
    genes_sorted = Keyword(multi=True)          # [min(a,b), max(a,b)] for canonical queries
    pair_id = Keyword()                         # "{species}:{min}__{max}" – set as _id
    is_self_correlation = Boolean()             # True when gene_a == gene_b (always = 1.0)
    
    # ---- Correlation Value ----
    correlation_value = ScaledFloat(scaling_factor=1_000_000)  # preserves 6 decimals, allows negatives
    
    # ---- Gene A Details (enriched from gene table) ----
    gene_a_locus_tag = Keyword()
    gene_a_uniprot_id = Keyword()
    gene_a_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()}
    )
    gene_a_product = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()}
    )
    gene_a_seq_id = Keyword()
    gene_a_start = Integer()
    gene_a_end = Integer()
    
    # ---- Gene B Details (enriched from gene table) ----
    gene_b_locus_tag = Keyword()
    gene_b_uniprot_id = Keyword()
    gene_b_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()}
    )
    gene_b_product = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()}
    )
    gene_b_seq_id = Keyword()
    gene_b_start = Integer()
    gene_b_end = Integer()
    
    # ---- Correlation Metadata ----
    abs_correlation = ScaledFloat(scaling_factor=1_000_000)  # |correlation_value| for filtering
    correlation_strength = Keyword()                         # "strong_positive", "moderate_positive", 
                                                             # "weak", "moderate_negative", "strong_negative"
    
    # Optional: p_value if available in future datasets
    p_value = ScaledFloat(scaling_factor=1_000_000)
    
    class Index:
        name = "fitness_correlation_index"
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
        """Enforce canonical undirected pair identity before saving."""
        # Canonical ordering
        aa, bb = canonical_pair(self.gene_a, self.gene_b)
        self.genes = [self.gene_a, self.gene_b]
        self.genes_sorted = [aa, bb]
        self.is_self_correlation = (aa == bb)
        
        # Build pair_id
        species_key = getattr(self, "species_acronym", None) or "unknown"
        self.pair_id = build_pair_id(species_key, aa, bb)
        self.meta.id = self.pair_id
        
        # Calculate absolute value for easier filtering
        if self.correlation_value is not None:
            self.abs_correlation = abs(self.correlation_value)
            
            # Categorize correlation strength
            abs_val = abs(self.correlation_value)
            if abs_val >= 0.7:
                strength = "strong"
            elif abs_val >= 0.4:
                strength = "moderate"
            else:
                strength = "weak"
            
            direction = "positive" if self.correlation_value >= 0 else "negative"
            self.correlation_strength = f"{strength}_{direction}" if abs_val > 0.1 else "weak"
        
        return super().save(**kwargs)

