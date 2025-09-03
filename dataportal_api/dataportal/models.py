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


class GeneDocument(Document):
    gene_id = Integer()
    uniprot_id = Keyword()
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
    seq_id = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    locus_tag = Text(
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

    start = Integer()
    end = Integer()

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

    # Fitness Data - Size: ~140 Conditions * 2 species
    # (~3800 genes for P. vulgatus, 3300 genes for B. uniformis, without intergenic regions)
    fitness_data = Nested(
        properties={
            "contrast": Keyword(),
            "lfc": Float(),
            "fdr": Float(),
        }
    )

    protein_sequence = Text(fields={"keyword": Keyword()})

    class Index:
        name = "gene_index"
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
        """set `_id` as `locus_tag`"""
        self.meta.id = self.locus_tag
        return super().save(**kwargs)
