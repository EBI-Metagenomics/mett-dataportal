"""Stamp annotation_run fields onto existing strain and feature Elasticsearch docs."""

from django.core.management.base import BaseCommand, CommandError
from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.connections import connections

from dataportal.models import AnnotationRun
from dataportal.utils.constants import INDEX_FEATURES, INDEX_STRAINS


def _index_exists(es, name: str) -> bool:
    if not name:
        return False
    try:
        return bool(es.indices.exists(index=name))
    except Exception:
        return False


class Command(BaseCommand):
    help = (
        "Update strain_index and feature indexes with current_annotation_run_id / "
        "annotation_run_id from PostgreSQL annotation_run rows. "
        "Missing feature indexes are skipped (strain stamps still run)."
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
        parser.add_argument(
            "--skip-features",
            action="store_true",
            help="Only stamp strain_index (use when feature indexes are not created yet)",
        )

    def handle(self, *args, **options):
        es = connections.get_connection()
        strain_index = options["strain_index"]
        if not _index_exists(es, strain_index):
            raise CommandError(
                f"Strain index '{strain_index}' does not exist. "
                "Create it (or pass --strain-index) before backfill."
            )

        qs = AnnotationRun.objects.all()
        if options["current_only"]:
            qs = qs.filter(is_current=True)

        strain_updated = 0
        feature_updated = 0
        missing_feature_indexes: dict[str, int] = {}
        skip_features = options["skip_features"]

        for run in qs:
            if run.is_current:
                strain_updated += self._stamp_strain(es, strain_index, run)

            if skip_features:
                continue

            feature_index = options["feature_index"] or run.es_feature_index or INDEX_FEATURES
            if not _index_exists(es, feature_index):
                missing_feature_indexes[feature_index] = (
                    missing_feature_indexes.get(feature_index, 0) + 1
                )
                continue

            feature_updated += self._stamp_features(es, feature_index, run)

        for name, n in sorted(missing_feature_indexes.items()):
            self.stdout.write(
                self.style.WARNING(
                    f"Skipped feature backfill for {n} run(s): index '{name}' does not exist. "
                    f"Create it with: python manage.py create_es_index "
                    f"--model FeatureDocument --es-version <release> "
                    f"then re-run, or pass --skip-features."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete. strain docs updated≈{strain_updated}, "
                f"feature docs updated≈{feature_updated}"
            )
        )

    def _stamp_strain(self, es, strain_index: str, run: AnnotationRun) -> int:
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
        try:
            res = es.update_by_query(index=strain_index, body=body, refresh=True)
            return res.get("updated", 0)
        except NotFoundError:
            self.stdout.write(
                self.style.WARNING(f"Strain index vanished during backfill: {strain_index}")
            )
            return 0
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Strain backfill failed for {run.isolate_name}: {e}; retrying by _id"
                )
            )
            body["query"] = {"term": {"_id": run.isolate_name}}
            try:
                res = es.update_by_query(index=strain_index, body=body, refresh=True)
                return res.get("updated", 0)
            except Exception as e2:
                self.stdout.write(
                    self.style.WARNING(f"Strain backfill retry failed for {run.isolate_name}: {e2}")
                )
                return 0

    def _stamp_features(self, es, feature_index: str, run: AnnotationRun) -> int:
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
            return res.get("updated", 0)
        except NotFoundError:
            self.stdout.write(
                self.style.WARNING(f"Feature index not found during update: {feature_index}")
            )
            return 0
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Feature backfill failed {run.isolate_name}@{feature_index}: {e}"
                )
            )
            return 0
