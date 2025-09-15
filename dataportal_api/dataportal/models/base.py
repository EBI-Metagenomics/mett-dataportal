"""
Base utilities and shared components for Elasticsearch document models.

This module contains analyzers, normalizers, and helper functions that are
shared across multiple document types.
"""

from elasticsearch_dsl import analyzer, tokenizer, normalizer


# ---- Tokenizers ----
edge_ngram_tokenizer = tokenizer(
    "edge_ngram_tokenizer",
    type="edge_ngram",
    min_gram=1,
    max_gram=20,
    token_chars=["letter", "digit", "connector_punctuation"],
)

# ---- Analyzers ----
autocomplete_analyzer = analyzer(
    "autocomplete_analyzer", tokenizer=edge_ngram_tokenizer, filter=["lowercase"]
)

# ---- Normalizers ----
lowercase_normalizer = normalizer(
    "lowercase_normalizer", type="custom", filter=["lowercase"]
)


# ---- Helper Functions ----
def canonical_pair(a: str, b: str) -> tuple[str, str]:
    """Return a,b sorted to ensure undirected symmetry."""
    return tuple(sorted([a, b]))


def build_pair_id(species_acronym: str, a: str, b: str) -> str:
    """Stable unique id for the interaction doc."""
    aa, bb = canonical_pair(a, b)
    # Use double-underscore to match your CSV pattern
    return f"{species_acronym}:{aa}__{bb}"

