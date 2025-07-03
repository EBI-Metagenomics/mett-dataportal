from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    analyzer,
    tokenizer,
    Nested,
    normalizer, Float,
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
    strain_id = Integer()

    species_scientific_name = Text(fields={"keyword": Keyword()})
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

    contigs = Nested(properties={"seq_id": Keyword(), "length": Integer()})

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


class FeatureDocument(Document):
    feature_type = Keyword()  # 'gene' or 'intergenomic_region'
    feature_id = Keyword()    # locus_tag for genes, IGR_B1234_B1235 for IGRs

    gene_id = Integer()
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
    # for IGRs
    locus_tag_start = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    locus_tag_end = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    strand = Keyword()
    length = Integer()

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


    cog_funcats = Keyword(multi=True)
    kegg = Keyword(multi=True, normalizer=lowercase_normalizer)
    pfam = Keyword(multi=True, normalizer=lowercase_normalizer)
    eggnog = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    interpro = Keyword(multi=True, normalizer=lowercase_normalizer)
    has_amr_info = Boolean()
    uf_ontology_terms = Keyword(multi=True)
    uf_prot_rec_fullname = Text(fields={"keyword": Keyword()})

    dbxref = Nested(properties={"db": Keyword(), "ref": Keyword()})

    uniprot_id = Keyword()
    cog_id = Keyword()

    ec_number = Keyword()

    essentiality = Keyword(normalizer=lowercase_normalizer)
    tas_hit = Float()  # Transposon Abundance Score (0-1) for essentiality QC

    inference = Text(fields={"keyword": Keyword()})

    ontology_terms = Nested(
        properties={
            "ontology_type": Keyword(),
            "ontology_id": Keyword(),
            "ontology_description": Text(fields={"keyword": Keyword(ignore_above=256)}),
        }
    )

    cross_references = Nested(
        properties={
            "db_name": Keyword(),
            "db_accession": Keyword(),
            "db_description": Text(),
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
        name = 'feature_index'
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
        if self.feature_type == 'gene':
            self.meta.id = self.locus_tag
        elif self.feature_type == 'intergenomic_region':
            self.meta.id = self.feature_id
        return super().save(**kwargs)


class PPIInteractionDocument(Document):
    """
    Stores pairwise Protein-Protein Interactions with multiple scores.

    Undirected edges (A-B == B-A):
    Must deduplicate: store only one direction (sorted(A,B)).

    Will need efficient:
        Lookup: “Does A interact with B?”
        Filtering: ensemble_score > 0.8, known_interaction = 1.
        Fetching partners: “Who are the top partners of A with score > X?”

    """

    interaction_id = Keyword()  # e.g., "P12345_P67890"
    protein_a_uniprot_id = Keyword()
    protein_b_uniprot_id = Keyword()

    known_interaction = Boolean()

    dl_score = Float()
    comelt_score = Float()
    abundance_score = Float()
    ensemble_score = Float()
    # additional scores as needed

    class Index:
        name = "ppi_interaction_index"
        settings = {
            "index": {"max_result_window": 500000}
        }

    def save(self, **kwargs):
        # Use sorted UniProt IDs for A-B == B-A consistency
        proteins = sorted([self.protein_a_uniprot_id, self.protein_b_uniprot_id])
        self.interaction_id = f"{proteins[0]}_{proteins[1]}"
        self.meta.id = self.interaction_id
        return super().save(**kwargs)