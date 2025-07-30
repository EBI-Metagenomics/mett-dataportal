from elasticsearch_dsl import (
    Boolean,
    Document,
    Float,
    Integer,
    Keyword,
    Nested,
    Text,
    analyzer,
    normalizer,
    tokenizer,
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
