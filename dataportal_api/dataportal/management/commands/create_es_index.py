from django.core.management.base import BaseCommand

from dataportal.elasticsearch.indexing import ProjectIndexManager
from dataportal.models import SpeciesDocument, StrainDocument, FeatureDocument, ProteinProteinDocument


class Command(BaseCommand):
    help = "Create versioned Elasticsearch indexes (no aliases)."

    def add_arguments(self, parser):
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

        self.stdout.write(self.style.SUCCESS("Starting Elasticsearch index creation..."))

        pim = ProjectIndexManager([SpeciesDocument, StrainDocument, FeatureDocument, ProteinProteinDocument])
        created = pim.create_all(version=es_version, if_exists=if_exists)

        for base, concrete in created.items():
            self.stdout.write(self.style.SUCCESS(f"{base} -> {concrete}"))

        self.stdout.write(self.style.SUCCESS("Elasticsearch index creation completed."))
