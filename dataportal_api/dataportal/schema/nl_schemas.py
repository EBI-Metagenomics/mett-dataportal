from dataportal.schema.gene_schemas import GeneQuery, NaturalLanguageGeneQuery

METT_GENE_QUERY_SCHEMA = {
    "name": "interpret_gene_query",
    "description": "Interpret user query for gene data search",
    "parameters": NaturalLanguageGeneQuery.model_json_schema()
}
