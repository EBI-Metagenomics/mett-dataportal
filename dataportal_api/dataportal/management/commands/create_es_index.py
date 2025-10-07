from django.core.management.base import BaseCommand, CommandError

from dataportal.elasticsearch.indexing import ProjectIndexManager
from dataportal.models import (
    SpeciesDocument,
    StrainDocument,
    FeatureDocument,
    ProteinProteinDocument,
    OperonDocument,
    OrthologDocument,
    GeneFitnessCorrelationDocument,
)


# Map of model names to document classes
AVAILABLE_MODELS = {
    "SpeciesDocument": SpeciesDocument,
    "StrainDocument": StrainDocument,
    "FeatureDocument": FeatureDocument,
    "ProteinProteinDocument": ProteinProteinDocument,
    "OperonDocument": OperonDocument,
    "OrthologDocument": OrthologDocument,
    "GeneFitnessCorrelationDocument": GeneFitnessCorrelationDocument,
}


class Command(BaseCommand):
    help = "Create versioned Elasticsearch indexes (no aliases)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            default=None,
            help=f"Specific model to create index for (e.g., GeneFitnessCorrelationDocument). "
                 f"If not provided, creates all indices. Available models: {', '.join(AVAILABLE_MODELS.keys())}",
        )
        parser.add_argument(
            "--es-version",
            dest="es_version",
            type=str,
            default=None,
            help="Concrete index version suffix (e.g., 2025.09.03). Defaults to today's UTC date.",
        )
        parser.add_argument(
            "--if-exists",
            dest="if_exists",
            type=str,
            choices=["skip", "recreate", "fail"],
            default="skip",
            help="Behavior if the concrete index already exists.",
        )

    def handle(self, *args, **kwargs):
        es_version = kwargs.get("es_version")
        if_exists = kwargs.get("if_exists", "skip")
        model_name = kwargs.get("model")

        # Determine which models to create
        if model_name:
            # Validate model name
            if model_name not in AVAILABLE_MODELS:
                raise CommandError(
                    f"Unknown model: {model_name}. "
                    f"Available models: {', '.join(AVAILABLE_MODELS.keys())}"
                )
            models_to_create = [AVAILABLE_MODELS[model_name]]
            self.stdout.write(
                self.style.SUCCESS(f"Creating index for {model_name}...")
            )
        else:
            # Create all models
            models_to_create = list(AVAILABLE_MODELS.values())
            self.stdout.write(
                self.style.SUCCESS("Creating all Elasticsearch indexes...")
            )

        # Create the indexes
        pim = ProjectIndexManager(models_to_create)
        created = pim.create_all(version=es_version, if_exists=if_exists)

        # Display results
        for base, concrete in created.items():
            self.stdout.write(self.style.SUCCESS(f"  ✓ {base} -> {concrete}"))

        if model_name:
            self.stdout.write(
                self.style.SUCCESS(f"\nIndex creation for {model_name} completed.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nAll {len(created)} index(es) created successfully.")
            )
