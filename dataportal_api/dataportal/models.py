from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    analyzer,
    tokenizer,
    Nested,
    normalizer,
    Float, Long, ScaledFloat,
)

edge_ngram_tokenizer = tokenizer(
    "edge_ngram_tokenizer",
    type="edge_ngram",
    min_gram=1,
    max_gram=20,
    token_chars=["letter", "digit", "connector_punctuation"],
)

autocomplete_analyzer = analyzer(
    "autocomplete_analyzer", tokenizer=edge_ngram_tokenizer, filter=["lowercase"]
)

lowercase_normalizer = normalizer(
    "lowercase_normalizer", type="custom", filter=["lowercase"]
)


class SpeciesDocument(Document):
    scientific_name = Text(fields={"keyword": Keyword()})
    common_name = Text()
    acronym = Keyword()
    taxonomy_id = Integer()

    class Index:
        name = "species_index"

    def save(self, **kwargs):
        """set `_id` as `acronym`"""
        self.meta.id = self.acronym
        return super().save(**kwargs)


class StrainDocument(Document):
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
                "tokenizer": {"edge_ngram_tokenizer": edge_ngram_tokenizer},
                "normalizer": {"lowercase_normalizer": lowercase_normalizer},
            }
        }

    def save(self, **kwargs):
        """set `_id` as `isolate_name`"""
        self.meta.id = self.isolate_name
        return super().save(**kwargs)


from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    Nested,
    Float,
)

# re-use your existing definitions
# edge_ngram_tokenizer, autocomplete_analyzer, lowercase_normalizer


class FeatureDocument(Document):
    # ---- Identity ----
    feature_id = Keyword()                                 # gene: locus_tag; IG: "IG-between-...-and-..."
    feature_type = Keyword(normalizer=lowercase_normalizer) # 'gene' | 'IG' | others
    element = Keyword(normalizer=lowercase_normalizer)      # gene, intergenic, ncRNA, ...

    # For genes (convenience/compatibility)
    locus_tag = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )                                 # still stored for genes
    uniprot_id = Keyword()

    # IG context (only meaningful when feature_type == 'IG')
    ig_locus_tag_a = Keyword()
    ig_locus_tag_b = Keyword()
    strand = Keyword()

    # Genomic coordinates (region-level; for genes or IGs)
    seq_id = Text(analyzer=autocomplete_analyzer,
                  search_analyzer="standard",
                  fields={"keyword": Keyword()})
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

    dbxref = Nested(properties={"db": Keyword(), "ref": Keyword()})

    ec_number = Keyword()

    essentiality = Keyword(normalizer=lowercase_normalizer)  # legacy single-value (kept for backward compatibility)
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
            "experimental_condition": Keyword(),       # e.g. mGAM_undefined_rich_media
            "TAs_in_locus": Integer(),
            "TAs_hit": Float(),                        # fraction 0..1
            "essentiality_call": Keyword(              # essential, not_essential, essential_solid, essential_liquid, not_classified, unclear
                normalizer=lowercase_normalizer
            ),
        }
    )

    # quick-existence flags
    has_proteomics = Boolean()
    has_fitness = Boolean()
    has_mutant_growth = Boolean()
    has_reactions = Boolean()

    # ---- PROTEIN ↔ COMPOUND interactions (new) ----
    protein_compound = Nested(
        properties={
            "compound": Keyword(),
            "ttp_score": Float(),
            "fdr": Float(),
            "hit_calling": Boolean(),
            "experimental_condition": Keyword(),
        }
    )

    # ---- GENE FITNESS (new, structured) ----
    # You already had a simpler fitness_data; we supersede/extend it here
    fitness = Nested(
        properties={
            "experimental_condition": Keyword(),
            "media": Keyword(),
            "contrast": Keyword(),
            "lfc": Float(),
            "fdr": Float()
        }
    )

    # ---- REACTIONS / GPR / METABOLITES (new) ----
    # 1) direct gene→reaction links (many)
    reactions = Keyword(multi=True)                    # e.g. ["ASPTA","CPPPGO",...]
    # 2) per-reaction details + GPR and metabolite edges
    reaction_details = Nested(
        properties={
            "reaction": Keyword(),
            "gpr": Text(fields={"keyword": Keyword()}),  # e.g. "BU_... or BU_..."
            # reaction graph edges (optional but useful for UI filters)
            "substrates": Keyword(multi=True),
            "products": Keyword(multi=True),
            # convenience fields for searching metabolite involvement
            "metabolites": Keyword(multi=True),
        }
    )

    # ---- MUTANT GROWTH (new) ----
    mutant_growth = Nested(
        properties={
            "media": Keyword(),
            "experimental_condition": Keyword(),
            "replicate": Integer(),
            "tas_hit": Float(),                         # 0..1
            "doubling_rate_h": Float(),
        }
    )

    # ---- PROTEOMICS (new) ----
    proteomics = Nested(
        properties={
            "coverage": Float(),
            "unique_peptides": Integer(),
            "unique_intensity": Float(),
            "evidence": Boolean(),
        }
    )

    # ---- Sequences (existing) ----
    protein_sequence = Text(fields={"keyword": Keyword()})  # only for 'gene'

    class Index:
        name = "feature_index"
        settings = {
            "index": {"max_result_window": 500000},
            "analysis": {
                "analyzer": {"autocomplete_analyzer": autocomplete_analyzer},
                "tokenizer": {"edge_ngram_tokenizer": edge_ngram_tokenizer},
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

