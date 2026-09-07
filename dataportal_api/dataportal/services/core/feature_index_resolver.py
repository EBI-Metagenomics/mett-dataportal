"""Resolve which feature Elasticsearch index(es) to query for a gene request."""

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional, Tuple, Union

from django.db.utils import ProgrammingError, OperationalError

from dataportal.utils.constants import INDEX_FEATURES

IndexSpec = Union[str, List[str]]


class FeatureIndexResolver:
    """Maps current/archived annotation runs to feature index names."""

    def resolve(self, annotation_run_id: Optional[int | str] = None) -> Tuple[IndexSpec, List[str]]:
        """
        Returns (index_or_indexes, annotation_run_ids_to_filter).

        Empty run-id list means do not filter (legacy indexes without the field).
        """
        if annotation_run_id:
            run = self._get_run(annotation_run_id)
            if run:
                return run.es_feature_index or INDEX_FEATURES, [str(run.pk)]
            return INDEX_FEATURES, [str(annotation_run_id)]

        indexes, run_ids = self._current()
        return indexes, run_ids

    def _get_run(self, annotation_run_id: int | str):
        try:
            from dataportal.models import AnnotationRun

            return AnnotationRun.objects.filter(pk=annotation_run_id).first()
        except (ProgrammingError, OperationalError):
            return None

    def _current(self) -> Tuple[IndexSpec, List[str]]:
        try:
            from dataportal.models import AnnotationRun

            rows = list(
                AnnotationRun.objects.filter(is_current=True).values_list("id", "es_feature_index")
            )
        except (ProgrammingError, OperationalError):
            return INDEX_FEATURES, []

        if not rows:
            return INDEX_FEATURES, []

        indexes = sorted({idx for _, idx in rows if idx}) or [INDEX_FEATURES]
        run_ids = [str(pk) for pk, _ in rows]
        if len(indexes) == 1:
            return indexes[0], run_ids
        return indexes, run_ids


@lru_cache(maxsize=1)
def get_feature_index_resolver() -> FeatureIndexResolver:
    return FeatureIndexResolver()


def invalidate_feature_index_resolver_cache() -> None:
    get_feature_index_resolver.cache_clear()
