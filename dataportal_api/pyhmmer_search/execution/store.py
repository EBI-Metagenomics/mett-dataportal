"""Persist a finished search on the job row."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.utils import timezone

from ..constants import STATUS_FAILURE, STATUS_SUCCESS

logger = logging.getLogger(__name__)


def limit_payload(payload: list[dict]) -> list[dict]:
    if len(json.dumps(payload)) > settings.PYHMMER_RESULT_MAX_BYTES:
        logger.warning("Truncated results to 10 hits")
        return payload[:10]
    return payload


def store_success(job, payload: list[dict]) -> None:
    job.status = STATUS_SUCCESS
    job.result = payload
    job.error = ""
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "result", "error", "finished_at"])


def store_failure(job, error: str) -> None:
    job.status = STATUS_FAILURE
    job.error = error
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "error", "finished_at"])
