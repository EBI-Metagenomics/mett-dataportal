from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from dataportal.services.core.annotation_run_service import AnnotationRunService
from dataportal.utils.constants import INDEX_FEATURES


class Command(BaseCommand):
    help = "Register an annotation run for an isolate (used for 2.0 test genomes and upgrades)."

    def add_arguments(self, parser):
        parser.add_argument("--isolate-name", required=True)
        parser.add_argument("--release-label", required=True)
        parser.add_argument("--es-feature-index", default=INDEX_FEATURES)
        parser.add_argument("--make-current", action="store_true")
        parser.add_argument("--strain-id", default="")
        parser.add_argument("--mettannotator-version", default="")
        parser.add_argument("--pipeline-version", default="")
        parser.add_argument("--doc-link", default="")
        parser.add_argument("--comments", default="")
        parser.add_argument("--gff-file", default="")
        parser.add_argument("--gff-ftp-template", default="")
        parser.add_argument("--processed-at", default=None, help="ISO datetime")

    def handle(self, *args, **options):
        processed_at = None
        if options.get("processed_at"):
            processed_at = parse_datetime(options["processed_at"])
            if processed_at is None:
                raise CommandError("Invalid --processed-at; use ISO datetime")
        run = AnnotationRunService().register(
            isolate_name=options["isolate_name"],
            release_label=options["release_label"],
            es_feature_index=options["es_feature_index"],
            make_current=options["make_current"],
            strain_id=options["strain_id"] or None,
            mettannotator_version=options["mettannotator_version"],
            pipeline_version=options["pipeline_version"],
            doc_link=options["doc_link"],
            comments=options["comments"],
            gff_file=options["gff_file"],
            gff_ftp_template=options["gff_ftp_template"],
            processed_at=processed_at,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Registered annotation run id={run.pk} {run.isolate_name}@{run.release_label} "
                f"current={run.is_current} index={run.es_feature_index}"
            )
        )
