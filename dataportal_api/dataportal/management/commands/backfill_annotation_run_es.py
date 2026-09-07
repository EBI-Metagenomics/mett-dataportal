"""Stamp annotation_run fields onto existing strain and feature Elasticsearch docs."""

from django.core.management.base import BaseCommand
from elasticsearch_dsl.connections import connections

from dataportal.models import AnnotationRun
from dataportal.utils.constants import INDEX_FEATURES, INDEX_STRAINS


class Command(BaseCommand):
    help = (
        "Update strain_index and feature indexes with current_annotation_run_id / "
        "annotation_run_id from PostgreSQL annotation_run rows."
    )

    def add_arguments(self, parser):
        parser.add_argument("--strain-index", default=INDEX_STRAINS)
        parser.add_argument(
            "--feature-index",
            default=None,
            help="Override feature index; default is each run's es_feature_index or feature_index",
        )
        parser.add_argument(
            "--current-only",
            action="store_true",
            help="Only backfill current runs (default: all runs)",
        )

    def handle(self, *args, **options):
        es = connections.get_connection()
        qs = AnnotationRun.objects.all()
        if options["current_only"]:
            qs = qs.filter(is_current=True)
        strain_updated = 0
        feature_updated = 0
        for run in qs:
            if run.is_current:
                body = {
                    "script": {
                        "source": """
ctx._source.current_annotation_run_id = params.run_id;
ctx._source.current_annotation_release = params.release;
ctx._source.annotation_doc_link = params.doc_link;
ctx._source.mettannotator_version = params.ma;
ctx._source.pipeline_version = params.pipe;
""",
                        "params": {
                            "run_id": str(run.pk),
                            "release": run.release_label,
                            "doc_link": run.doc_link or "",
                            "ma": run.mettannotator_version or "",
                            "pipe": run.pipeline_version or "",
                        },
                    },
                    "query": {"term": {"isolate_name.keyword": run.isolate_name.lower()}},
                }
                # isolate_name.keyword uses lowercase_normalizer
                try:
                    res = es.update_by_query(index=options["strain_index"], body=body, refresh=True)
                    strain_updated += res.get("updated", 0)
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Strain backfill failed for {run.isolate_name}: {e}; retrying term isolate_name"
                        )
                    )
                    body["query"] = {"term": {"_id": run.isolate_name}}
                    res = es.update_by_query(index=options["strain_index"], body=body, refresh=True)
                    strain_updated += res.get("updated", 0)

            feature_index = options["feature_index"] or run.es_feature_index or INDEX_FEATURES
            feat_body = {
                "script": {
                    "source": """
ctx._source.annotation_run_id = params.run_id;
ctx._source.annotation_release = params.release;
""",
                    "params": {
                        "run_id": str(run.pk),
                        "release": run.release_label,
                    },
                },
                "query": {"term": {"isolate_name": run.isolate_name}},
            }
            try:
                res = es.update_by_query(index=feature_index, body=feat_body, refresh=True)
                feature_updated += res.get("updated", 0)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Feature backfill failed {run.isolate_name}@{feature_index}: {e}"
                    )
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete. strain docs updated≈{strain_updated}, feature docs updated≈{feature_updated}"
            )
        )
