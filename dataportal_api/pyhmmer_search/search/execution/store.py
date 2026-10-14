"""Persist a finished search on the job row."""

from __future__ import annotations

import json
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)

MAX_RESULT_SIZE = 50 * 1024 * 1024


def limit_payload(payload: list[dict]) -> list[dict]:
    if len(json.dumps(payload)) > MAX_RESULT_SIZE:
        logger.warning("Truncated results to 10 hits")
        return payload[:10]
    return payload


def store_success(job, payload: list[dict]) -> None:
    job.status = "SUCCESS"
    job.result = payload
    job.error = ""
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "result", "error", "finished_at"])
    if job.task:
        job.task.status = "SUCCESS"
        job.task.result = json.dumps(payload)
        job.task.date_done = timezone.now()
        job.task.save()


def store_failure(job, error: str) -> None:
    job.status = "FAILURE"
    job.error = error
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "error", "finished_at"])
    if job.task:
        job.task.status = "FAILURE"
        job.task.result = error
        job.task.date_done = timezone.now()
        job.task.save()
