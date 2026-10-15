"""Load a saved job, run PyHMMER, and store the hits.

The steps live in ``execution``. This module is the entry point used by the
background thread and by the Celery task.
"""

from __future__ import annotations

import logging
import uuid
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django_celery_results.models import TaskResult
from pyhmmer.easel import Alphabet

from django.conf import settings

from .constants import STATUS_STARTED
from .execution.engine import search_targets
from .execution.jobs import load_job
from .execution.query import digitize_query
from .execution.schemas import PipelineParameters, SearchScope
from .execution.store import limit_payload, store_failure, store_success
from .execution.targets import load_targets
from .membership import members_for_scope
from .models import HmmerJob

logger = logging.getLogger(__name__)


def execute_search(job_id: str):
    logger.info("=== STARTING HMMER SEARCH ===")
    logger.info("Job ID: %s", job_id)
    try:
        uuid.UUID(str(job_id))
    except ValueError as exc:
        logger.error("Invalid job ID format: %s", job_id)
        raise ValueError(f"Invalid job ID format: {job_id}") from exc

    job = load_job(job_id)
    logger.info("Updating job status to STARTED...")
    job.status = STATUS_STARTED
    job.save(update_fields=["status"])
    if job.task:
        job.task.status = STATUS_STARTED
        job.task.save(update_fields=["status"])

    try:
        return _run(job)
    except Exception as exc:
        logger.error("=== TASK FAILED ===")
        logger.error("Error in execute_search for job %s: %s", job_id, exc, exc_info=True)
        store_failure(job, str(exc))
        raise


def _run(job: HmmerJob):
    scope = SearchScope.from_job(job)
    parameters = PipelineParameters.from_job(job)
    logger.info(
        "Search scope species=%s type_only=%s isolate=%s",
        scope.species or "all",
        scope.type_only,
        scope.isolate or "-",
    )
    db_path = settings.PYHMMER_DB
    if not db_path:
        raise ValueError("PYHMMER_DB is not configured")

    membership = members_for_scope(db_path, scope.species, scope.type_only, scope.isolate)
    if membership is not None and not membership:
        logger.info("Filter matched no proteins")
        store_success(job, [])
        return []

    alphabet = Alphabet.amino()
    query, digital_query = digitize_query(job.input, alphabet)
    logger.info("Query name: %s", query.name)

    digital_targets, target_sequences = load_targets(db_path, alphabet, membership)
    if not digital_targets:
        logger.info("No sequences to search")
        store_success(job, [])
        return []

    hits = search_targets(
        query,
        digital_query,
        digital_targets,
        target_sequences,
        alphabet,
        parameters,
        membership,
    )
    payload = limit_payload([hit.model_dump() for hit in hits])
    store_success(job, payload)
    logger.info("=== TASK COMPLETED SUCCESSFULLY ===")
    return payload


@shared_task(bind=True, queue="pyhmmer_queue", routing_key="pyhmmer.search")
def run_search(self, job_id: str):
    """Celery entry point. The API starts execute_search on a thread instead."""
    return execute_search(job_id)


@shared_task
def cleanup_old_tasks():
    cutoff = timezone.now() - timedelta(days=settings.PYHMMER_TASK_RETENTION_DAYS)
    deleted, _ = TaskResult.objects.filter(date_done__lt=cutoff).delete()
    return f"Deleted {deleted} old task results"
