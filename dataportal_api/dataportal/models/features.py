"""
Feature document model for Elasticsearch.

This module defines the FeatureDocument class for indexing genomic features
including genes, intergenic regions, and their associated annotations.
"""

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


class FeatureDocument(Document):
    """Elasticsearch document for genomic features (genes, intergenic regions, etc.)."""

    # ---- Identity ----
    feature_id = Keyword()  # gene: locus_tag; IG: "IG-between-...-and-..."
    feature_type = Keyword(normalizer=lowercase_normalizer)  # 'gene' | 'IG' | others
    element = Keyword(normalizer=lowercase_normalizer)  # gene, intergenic, ncRNA, ...

    # For genes (convenience/compatibility)
    locus_tag = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )  # still stored for genes
    uniprot_id = Keyword()

    # IG context (only meaningful when feature_type == 'IG')
    ig_locus_tag_a = Keyword()
    ig_locus_tag_b = Keyword()
    flanking_locus_tags = Keyword(multi=True)
    strand = Keyword()

    # Genomic coordinates (region-level; for genes or IGs)
    seq_id = Text(
        analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()}
    )
    start = Integer()
    end = Integer()

    gene_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    alias = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )

    product = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    product_source = Text(fields={"keyword": Keyword()})

    species_scientific_name = Keyword()
    species_acronym = Keyword(normalizer=lowercase_normalizer)
    isolate_name = Keyword()

    # ---- Functional annotations (existing) ----
    cog_id = Keyword(multi=True)
    cog_funcats = Keyword(multi=True)
    kegg = Keyword(multi=True, normalizer=lowercase_normalizer)
    pfam = Keyword(multi=True, normalizer=lowercase_normalizer)
    eggnog = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    interpro = Keyword(multi=True, normalizer=lowercase_normalizer)
    has_amr_info = Boolean()
    uf_ontology_terms = Keyword(multi=True)
    uf_prot_rec_fullname = Text(fields={"keyword": Keyword()})
    uf_keyword = Keyword(multi=True)
    uf_gene_name = Text(fields={"keyword": Keyword()})
    uf_gene_name_synonym = Text(fields={"keyword": Keyword()})
    uf_prot_rec_shortname = Text(fields={"keyword": Keyword()})
    uf_prot_alt_fullname = Text(fields={"keyword": Keyword()})
    uf_prot_alt_shortname = Text(fields={"keyword": Keyword()})
    uf_prot_alt_ecnumber = Keyword()
    uf_chebi = Keyword(multi=True)
    uf_pirsr_cofactor = Text(fields={"keyword": Keyword()})

    dbxref = Nested(properties={"db": Keyword(), "ref": Keyword()})

    ec_number = Keyword()
    uf_prot_rec_ecnumber = Keyword()

    # dbCAN / CAZyme annotations (from merged GFF)
    dbcan_prot_type = Keyword()
    dbcan_prot_family = Keyword(multi=True)
    substrate_dbcan_pul = Text(fields={"keyword": Keyword()})
    substrate_dbcan_sub = Text(fields={"keyword": Keyword()})

    # Biosynthetic gene cluster annotations
    gecco_bgc_type = Keyword()
    nearest_mibig = Keyword()
    nearest_mibig_class = Keyword()
    antismash_bgc_function = Text(fields={"keyword": Keyword()})

    # Mobilome annotations
    mge_id = Keyword()
    mge_types = Keyword(multi=True)

    # Defense system annotations
    defense_finder_type = Keyword()
    defense_finder_subtype = Keyword()

    extra_copy_number = Integer()
    note = Text(fields={"keyword": Keyword(ignore_above=512)})

    has_essentiality = Boolean()  # flag indicating if essentiality data is available
    essentiality = Keyword(normalizer=lowercase_normalizer)
    inference = Text(fields={"keyword": Keyword()})

    ontology_terms = Nested(
        properties={
            "ontology_type": Keyword(),
            "ontology_id": Keyword(),
            "ontology_description": Text(fields={"keyword": Keyword(ignore_above=256)}),
        }
    )

    amr = Nested(
        properties={
            "gene_symbol": Keyword(),
            "sequence_name": Text(fields={"keyword": Keyword()}),
            "scope": Keyword(),
            "element_type": Keyword(),
            "element_subtype": Keyword(),
            "drug_class": Keyword(),
            "drug_subclass": Keyword(),
            "uf_keyword": Keyword(multi=True),
            "uf_ecnumber": Keyword(),
        }
    )

    # ---- ESSENTIALITY (new, structured) ----
    # matches your CSV: TnSeq/TAs metrics + call + condition
    essentiality_data = Nested(
        properties={
            "experimental_condition": Keyword(),  # e.g. mGAM_undefined_rich_media
            "TAs_in_locus": Integer(),
            "TAs_hit": Float(),  # fraction 0..1
            "essentiality_call": Keyword(  # essential, not_essential, essential_solid, essential_liquid, not_classified, unclear
                normalizer=lowercase_normalizer
            ),
        }
    )

    # quick-existence flags
    has_proteomics = Boolean()
    has_fitness = Boolean()
    has_mutant_growth = Boolean()
    has_reactions = Boolean()

    annotation_run_id = Keyword()
    annotation_release = Keyword()

    # ---- Sequences (existing) ----
    protein_sequence = Text(fields={"keyword": Keyword()})  # only for 'gene'

    class Index:
        name = "feature_index"
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
            # fall back for genes
            self.feature_id = getattr(self, "locus_tag", None)
        self.meta.id = self.feature_id
        return super().save(**kwargs)
