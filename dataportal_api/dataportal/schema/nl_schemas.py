from dataportal.schema.gene_schemas import GeneQuery

METT_GENE_QUERY_SCHEMA = {
    "name": "interpret_gene_query",
    "description": "Interpret user query for gene data search",
    "parameters": GeneQuery.model_json_schema()
}
