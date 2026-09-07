"""Register annotation 2.0 test genomes (metadata only; ingest GFF separately)."""

from django.core.management.base import BaseCommand

from dataportal.services.core.annotation_run_service import AnnotationRunService
from dataportal.utils.constants import (
    DEFAULT_ANNOTATION_DOC_LINK,
)


class Command(BaseCommand):
    help = (
        "Register annotation release 2.0 for one or more isolates and mark them current. "
        "Follow with import_strains and import_features --index feature_index-2.0 "
        "--annotation-release 2.0 --annotation-run-id <id>."
    )

    def add_arguments(self, parser):
        parser.add_argument("--isolates", nargs="+", required=True)
        parser.add_argument("--es-feature-index", default="feature_index-2.0")
        parser.add_argument("--mettannotator-version", default="2.0")
        parser.add_argument("--pipeline-version", default="2.0")
        parser.add_argument("--doc-link", default=DEFAULT_ANNOTATION_DOC_LINK)
        parser.add_argument("--gff-ftp-template", default="")
        parser.add_argument("--gff-file", default="")
        parser.add_argument("--make-current", action="store_true", default=True)

    def handle(self, *args, **options):
        service = AnnotationRunService()
        for isolate in options["isolates"]:
            run = service.register(
                isolate_name=isolate,
                release_label="2.0",
                es_feature_index=options["es_feature_index"],
                make_current=options["make_current"],
                mettannotator_version=options["mettannotator_version"],
                pipeline_version=options["pipeline_version"],
                doc_link=options["doc_link"],
                gff_file=options["gff_file"],
                gff_ftp_template=options["gff_ftp_template"],
                comments="Annotation 2.0 test genome",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{isolate}: annotation_run_id={run.pk} index={run.es_feature_index} "
                    f"current={run.is_current}"
                )
            )
        self.stdout.write(
            "Next: create_es_index --model FeatureDocument --es-version 2.0 "
            "then import_features --index feature_index-2.0 --annotation-release 2.0 "
            "--annotation-run-id <id> --isolates ..."
        )
