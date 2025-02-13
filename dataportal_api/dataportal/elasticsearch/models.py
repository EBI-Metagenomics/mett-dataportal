from elasticsearch_dsl import Document, Text, Keyword, Integer, Boolean, analyzer, tokenizer, Nested

edge_ngram_tokenizer = tokenizer(
    "edge_ngram_tokenizer",
    type="edge_ngram",
    min_gram=1,
    max_gram=20,
    token_chars=["letter", "digit", "symbol"]
)

autocomplete_analyzer = analyzer(
    "autocomplete_analyzer",
    tokenizer=edge_ngram_tokenizer,
    filter=["lowercase"]
)


class SpeciesDocument(Document):
    scientific_name = Text(fields={"keyword": Keyword()})
    common_name = Text()
    acronym = Keyword()
    taxonomy_id = Integer()

    class Index:
        name = "species_index"


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


class GeneDocument(Document):
    gene_id = Integer()
    gene_name = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    seq_id = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    locus_tag = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})
    product = Text(analyzer=autocomplete_analyzer, search_analyzer="standard", fields={"keyword": Keyword()})

    species_scientific_name = Keyword()
    isolate_name = Keyword()

    start = Integer()
    end = Integer()

    cog = Keyword()
    kegg = Keyword()
    pfam = Keyword()
    interpro = Keyword()
    dbxref = Keyword()
    ec_number = Keyword()
    essentiality = Keyword()

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
                }
            }
        }
        dynamic = "true"
