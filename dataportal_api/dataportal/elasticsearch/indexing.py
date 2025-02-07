from elasticsearch import Elasticsearch
import json
import os

# Elasticsearch connection
es = Elasticsearch("http://localhost:9200")

# Define available index mappings (e.g., gene, protein, etc.)
MAPPING_FILES = {
    "species_index": "mappings/species_mapping.json",
    "strain_index": "mappings/strain_mapping.json",
    "gene_index": "mappings/gene_mapping.json",
}


def create_index():
    for index_name, mapping_file in MAPPING_FILES.items():
        # Check if the index exists
        if es.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists. Skipping creation.")
            continue  # Skip index creation if it already exists

        # Load the mapping
        with open(mapping_file, "r") as f:
            mapping = json.load(f)

        # Create the index
        es.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created successfully.")


if __name__ == "__main__":
    create_index()
