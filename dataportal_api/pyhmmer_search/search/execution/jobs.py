"""Load the job row the search will run."""

from __future__ import annotations

import logging
import time

from ..models import HmmerJob

logger = logging.getLogger(__name__)


def load_job(job_id: str) -> HmmerJob:
    """Fetch the job, retrying briefly so a just-committed row is visible."""
    retry_delay = 0.5
    last_error = None
    for attempt in range(5):
        try:
            return HmmerJob.objects.select_related("task").get(id=job_id)
        except HmmerJob.DoesNotExist as exc:
            last_error = exc
            if attempt == 4:
                break
            logger.warning(
                "Job %s not found on attempt %s, retrying in %.1fs",
                job_id,
                attempt + 1,
                retry_delay,
            )
            time.sleep(retry_delay)
            retry_delay *= 1.5
    raise HmmerJob.DoesNotExist(f"Job {job_id} does not exist") from last_error
