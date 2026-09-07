"""Read/write helpers for annotation_run provenance."""

from __future__ import annotations

from typing import Optional

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from dataportal.models import AnnotationRun
from dataportal.schema.core.annotation_schemas import (
    AnnotationRunSchema,
    GenomeAnnotationsResponseSchema,
)
from dataportal.services.core.feature_index_resolver import invalidate_feature_index_resolver_cache
from dataportal.utils.exceptions import GenomeNotFoundError


def _to_schema(run: AnnotationRun) -> AnnotationRunSchema:
    return AnnotationRunSchema(
        id=run.pk,
        isolate_name=run.isolate_name,
        strain_id=run.strain_id,
        release_label=run.release_label,
        is_current=run.is_current,
        status=run.status,
        mettannotator_version=run.mettannotator_version,
        pipeline_version=run.pipeline_version,
        doc_link=run.doc_link or None,
        comments=run.comments or None,
        processed_at=run.processed_at,
        created_at=run.created_at,
        es_feature_index=run.es_feature_index,
        gff_file=run.gff_file or None,
        gff_url=run.gff_url(),
    )


class AnnotationRunService:
    def list_for_isolate(self, isolate_name: str) -> GenomeAnnotationsResponseSchema:
        qs = AnnotationRun.objects.filter(isolate_name=isolate_name)
        runs = list(qs)
        if not runs:
            raise GenomeNotFoundError(isolate_name)
        current = next((r for r in runs if r.is_current), None)
        previous = [r for r in runs if not r.is_current]
        previous.sort(key=lambda r: r.processed_at or r.created_at, reverse=True)
        return GenomeAnnotationsResponseSchema(
            isolate_name=isolate_name,
            current=_to_schema(current) if current else None,
            previous=[_to_schema(r) for r in previous],
            runs=[_to_schema(r) for r in runs],
        )

    async def list_for_isolate_async(self, isolate_name: str) -> GenomeAnnotationsResponseSchema:
        return await sync_to_async(self.list_for_isolate)(isolate_name)

    def get_run(self, run_id: int) -> Optional[AnnotationRun]:
        return AnnotationRun.objects.filter(pk=run_id).first()

    def register(
        self,
        *,
        isolate_name: str,
        release_label: str,
        es_feature_index: str,
        make_current: bool = False,
        strain_id: Optional[str] = None,
        mettannotator_version: str = "",
        pipeline_version: str = "",
        doc_link: str = "",
        comments: str = "",
        gff_file: str = "",
        gff_ftp_template: str = "",
        processed_at=None,
        status: Optional[str] = None,
    ) -> AnnotationRun:
        with transaction.atomic():
            if make_current:
                AnnotationRun.objects.filter(isolate_name=isolate_name, is_current=True).update(
                    is_current=False, status=AnnotationRun.STATUS_ARCHIVED
                )
            status = status or (
                AnnotationRun.STATUS_CURRENT if make_current else AnnotationRun.STATUS_PROCESSING
            )
            run, _created = AnnotationRun.objects.update_or_create(
                isolate_name=isolate_name,
                release_label=release_label,
                defaults={
                    "strain_id": strain_id,
                    "is_current": make_current,
                    "status": status,
                    "mettannotator_version": mettannotator_version,
                    "pipeline_version": pipeline_version,
                    "doc_link": doc_link,
                    "comments": comments,
                    "es_feature_index": es_feature_index,
                    "gff_file": gff_file,
                    "gff_ftp_template": gff_ftp_template,
                    "processed_at": processed_at or timezone.now(),
                },
            )
        invalidate_feature_index_resolver_cache()
        return run
