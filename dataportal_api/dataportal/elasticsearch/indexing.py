from elasticsearch import Elasticsearch
import json
import os

# Elasticsearch connection with authentication
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", "")
ES_PASSWORD = os.getenv("ES_PASSWORD", "")

es = Elasticsearch(
    ES_HOST,
    basic_auth=(ES_USER, ES_PASSWORD)  # Use basic authentication
)

# Get the absolute path of the directory containing this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPINGS_DIR = os.path.join(BASE_DIR, "mappings")

MAPPING_FILES = {
    "species_index": os.path.join(MAPPINGS_DIR, "species_mapping.json"),
    "strain_index": os.path.join(MAPPINGS_DIR, "strain_mapping.json"),
    "gene_index": os.path.join(MAPPINGS_DIR, "gene_mapping.json"),
}


def create_index():
    for index_name, mapping_file in MAPPING_FILES.items():
        # Check if the index exists
        if es.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists. Skipping creation.")
            continue  # Skip index creation if it already exists

        # Ensure the mapping file exists before proceeding
        if not os.path.exists(mapping_file):
            print(f"Error: Mapping file '{mapping_file}' not found. Skipping index creation for '{index_name}'.")
            continue

        # Load the mapping
        with open(mapping_file, "r") as f:
            mapping = json.load(f)

        # Create the index
        es.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created successfully.")


if __name__ == "__main__":
    create_index()
