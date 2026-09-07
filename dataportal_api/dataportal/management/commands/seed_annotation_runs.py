from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from elasticsearch_dsl import Search

from dataportal.services.core.annotation_run_service import AnnotationRunService
from dataportal.utils.constants import (
    DEFAULT_ANNOTATION_DOC_LINK,
    DEFAULT_ANNOTATION_RELEASE,
    DEFAULT_METTANNOTATOR_VERSION,
    DEFAULT_PIPELINE_VERSION,
    INDEX_FEATURES,
    INDEX_STRAINS,
)


class Command(BaseCommand):
    help = "Create current annotation_run rows for every isolate in strain_index (baseline 1.0)."

    def add_arguments(self, parser):
        parser.add_argument("--strain-index", default=INDEX_STRAINS)
        parser.add_argument("--es-feature-index", default=INDEX_FEATURES)
        parser.add_argument("--release-label", default=DEFAULT_ANNOTATION_RELEASE)
        parser.add_argument("--mettannotator-version", default=DEFAULT_METTANNOTATOR_VERSION)
        parser.add_argument("--pipeline-version", default=DEFAULT_PIPELINE_VERSION)
        parser.add_argument("--doc-link", default=DEFAULT_ANNOTATION_DOC_LINK)
        parser.add_argument(
            "--gff-ftp-template",
            default="https://ftp.ebi.ac.uk/pub/databases/mett/annotations/v1_2024-04-15/{}/functional_annotation/merged_gff/",
        )
        parser.add_argument(
            "--processed-at",
            default="2024-04-15",
            help="ISO date or datetime for processed_at",
        )

    def handle(self, *args, **options):
        raw = options["processed_at"]
        parsed = datetime.fromisoformat(raw)
        processed_at = parsed if timezone.is_aware(parsed) else timezone.make_aware(parsed)
        service = AnnotationRunService()
        s = Search(index=options["strain_index"]).source(["isolate_name", "strain_id", "gff_file"])
        count = 0
        for hit in s.scan():
            isolate = getattr(hit, "isolate_name", None) or hit.meta.id
            service.register(
                isolate_name=isolate,
                release_label=options["release_label"],
                es_feature_index=options["es_feature_index"],
                make_current=True,
                strain_id=getattr(hit, "strain_id", None),
                mettannotator_version=options["mettannotator_version"],
                pipeline_version=options["pipeline_version"],
                doc_link=options["doc_link"],
                gff_file=getattr(hit, "gff_file", None) or "",
                gff_ftp_template=options["gff_ftp_template"],
                processed_at=processed_at,
                status="current",
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded {count} annotation run(s)."))
