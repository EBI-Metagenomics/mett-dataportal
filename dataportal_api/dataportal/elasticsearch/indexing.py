from dataportal.models import GeneDocument, SpeciesDocument, StrainDocument

# Note: Elasticsearch connection is already established in settings.py via elasticsearch_client.py
# This module uses the existing connection

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
