"""
Ortholog document model for Elasticsearch.

This module defines the OrthologDocument class for indexing ortholog relationships
between genes across different species with comprehensive gene information.
"""

from elasticsearch_dsl import Document, Keyword, Text, Integer, ScaledFloat, Boolean
from dataportal.models.base import lowercase_normalizer, autocomplete_analyzer


class OrthologDocument(Document):
    """Elasticsearch document for ortholog relationships with gene information."""
    
    # ---- Identity / keys ----
    pair_id = Keyword()                                    # "{locus_a}__{locus_b}" – set as _id
    doc_type = Keyword()                                   # "ortholog" for filtering
    
    # ---- Ortholog-specific fields ----
    orthology_type = Keyword()                             # "1:1", "many:1", "1:many", "many:many"
    oma_group_id = Integer()                               # OMA group ID (if available)
    members = Keyword(multi=True)                          # [gene_a, gene_b] for queries
    is_one_to_one = Boolean()                             # True if orthology_type is "1:1"

    
    # ---- Gene A Information ----
    gene_a = Keyword()                                     # locus tag (e.g., "BU_ATCC8492_00001")
    gene_a_locus_tag = Keyword()                           # same as gene_a for consistency
    gene_a_uniprot_id = Keyword()                          # UniProt ID
    gene_a_name = Keyword()                                # gene name
    gene_a_source = Keyword()                              # source
    gene_a_type = Keyword()                                # feature type
    gene_a_start = Integer()                               # start position
    gene_a_end = Integer()                                 # end position
    gene_a_score = ScaledFloat(scaling_factor=1_000_000)   # score
    gene_a_strand = Keyword()                              # strand (+/-)
    gene_a_phase = Keyword()                               # phase
    gene_a_product = Text()                                # product description
    gene_a_desc = Text()                                   # additional description
    
    # ---- Gene B Information ----
    gene_b = Keyword()                                     # locus tag (e.g., "PV_ATCC8482_00001")
    gene_b_locus_tag = Keyword()                           # same as gene_b for consistency
    gene_b_uniprot_id = Keyword()                          # UniProt ID
    gene_b_name = Keyword()                                # gene name
    gene_b_source = Keyword()                              # source
    gene_b_type = Keyword()                                # feature type
    gene_b_start = Integer()                               # start position
    gene_b_end = Integer()                                 # end position
    gene_b_score = ScaledFloat(scaling_factor=1_000_000)   # score
    gene_b_strand = Keyword()                              # strand (+/-)
    gene_b_phase = Keyword()                               # phase
    gene_b_product = Text()                                # product description
    gene_b_desc = Text()                                   # additional description
    
    # ---- Species Information ----
    species_a_acronym = Keyword(normalizer=lowercase_normalizer)  # species acronym for gene A
    species_b_acronym = Keyword(normalizer=lowercase_normalizer)  # species acronym for gene B
    isolate_a = Keyword()                                  # isolate for gene A
    isolate_b = Keyword()                                  # isolate for gene B
    

    
    # ---- Cross-species analysis fields ----
    same_species = Boolean()                               # whether both genes are from the same species
    same_isolate = Boolean()                               # whether both genes are from the same isolate


    class Index:
        name = "ortholog_index"
        settings = {
            "index": {"max_result_window": 500000},
            "analysis": {
                "analyzer": {"autocomplete_analyzer": autocomplete_analyzer},
                "tokenizer": {"edge_ngram_tokenizer": autocomplete_analyzer.tokenizer},
                "normalizer": {"lowercase_normalizer": lowercase_normalizer},
            },
        }
        dynamic = "true"
