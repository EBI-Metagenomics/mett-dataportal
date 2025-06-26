from elasticsearch_dsl import connections
from dataportal.models import SpeciesDocument, StrainDocument, GeneDocument
import os

# Load environment variables for Elasticsearch
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER")
ES_PASSWORD = os.getenv("ES_PASSWORD")

# Create Elasticsearch connection parameters
es_connection_params = {"hosts": [ES_HOST]}

# Only set authentication if both username and password are available
if ES_USER and ES_PASSWORD:
    es_connection_params["basic_auth"] = (ES_USER, ES_PASSWORD)

# Establish connection
connections.create_connection(**es_connection_params)

# List of Elasticsearch document classes
INDEX_MODELS = [SpeciesDocument, StrainDocument, GeneDocument]


def create_indexes():

    for model in INDEX_MODELS:
        if not model._index.exists():
            model.init()
            print(f"Index '{model.Index.name}' created successfully.")
        else:
            print(f"Index '{model.Index.name}' already exists. Skipping creation.")


if __name__ == "__main__":
    create_indexes()
