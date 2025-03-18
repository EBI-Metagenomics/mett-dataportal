from elasticsearch_dsl import Document, Text, Keyword, Integer, Boolean, analyzer, tokenizer, Nested, normalizer

edge_ngram_tokenizer = tokenizer(
    "edge_ngram_tokenizer",
    type="edge_ngram",
    min_gram=1,
    max_gram=20,
    token_chars=["letter", "digit", "connector_punctuation"]
)

autocomplete_analyzer = analyzer(
    "autocomplete_analyzer",
    tokenizer=edge_ngram_tokenizer,
    filter=["lowercase"]
)

lowercase_normalizer = normalizer(
    "lowercase_normalizer",
    type="custom",
    filter=["lowercase"]
)


class SpeciesDocument(Document):
    scientific_name = Text(fields={"keyword": Keyword()})
    common_name = Text()
    acronym = Keyword()
    taxonomy_id = Integer()

    class Index:
        name = "species_index"

    def save(self, **kwargs):
        """ set `_id` as `acronym` """
        self.meta.id = self.acronym
        return super().save(**kwargs)


class StrainDocument(Document):
    strain_id = Integer()

    species_scientific_name = Keyword()

    isolate_name = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    assembly_name = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    assembly_accession = Keyword()

    fasta_file = Keyword()
    gff_file = Keyword()  # Nullable

    type_strain = Boolean()

    contigs = Nested(
        properties={
            "seq_id": Keyword(),
            "length": Integer()
        }
    )

    class Index:
        name = "strain_index"
        settings = {
            "analysis": {
                "analyzer": {
                    "autocomplete_analyzer": autocomplete_analyzer
                },
                "tokenizer": {
                    "edge_ngram_tokenizer": edge_ngram_tokenizer
                }
            }
        }

    def save(self, **kwargs):
        """ set `_id` as `isolate_name` """
        self.meta.id = self.isolate_name
        return super().save(**kwargs)


class GeneDocument(Document):
    gene_id = Integer()
    gene_name = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    alias = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    seq_id = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    locus_tag = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    product = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    product_source = Text(fields={"keyword": Keyword()})

    species_scientific_name = Keyword()
    species_acronym = Keyword()
    isolate_name = Keyword()

    start = Integer()
    end = Integer()

    # cog = Keyword(multi=True, normalizer=lowercase_normalizer)
    cog_funcats = Keyword(multi=True)
    kegg = Keyword(multi=True, normalizer=lowercase_normalizer)
    pfam = Keyword(multi=True, normalizer=lowercase_normalizer)
    eggnog = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    interpro = Keyword(multi=True, normalizer=lowercase_normalizer)

    dbxref = Nested(
        properties={
            "db": Keyword(),
            "ref": Keyword()
        }
    )

    uniprot_id = Keyword()
    cog_id = Keyword()

    ec_number = Keyword()
    essentiality = Keyword(normalizer=lowercase_normalizer)
    inference = Text(fields={"keyword": Keyword()})

    ontology_terms = Nested(
        properties={
            "ontology_type": Keyword(),
            "ontology_id": Keyword(),
            "ontology_description": Text(fields={"keyword": Keyword(ignore_above=256)})
        }
    )

    cross_references = Nested(
        properties={
            "db_name": Keyword(),
            "db_accession": Keyword(),
            "db_description": Text()
        }
    )

    class Index:
        name = "gene_index"
        settings = {
            "analysis": {
                "analyzer": {
                    "autocomplete_analyzer": autocomplete_analyzer
                },
                "tokenizer": {
                    "edge_ngram_tokenizer": edge_ngram_tokenizer
                },
                "normalizer": {
                    "lowercase_normalizer": lowercase_normalizer
                }
            }
        }
        dynamic = "true"

    def save(self, **kwargs):
        """ set `_id` as `locus_tag` """
        self.meta.id = self.locus_tag
        return super().save(**kwargs)
