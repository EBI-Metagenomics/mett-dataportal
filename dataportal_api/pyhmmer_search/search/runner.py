"""Run a PyHMMER search on a background thread inside the Django process."""

from __future__ import annotations

import logging
import threading

from django.db import close_old_connections

logger = logging.getLogger(__name__)

# One search at a time. Two "all species" searches would each hold the
# matching sequences in memory.
_lock = threading.Lock()


def start_search(job_id: str) -> None:
    thread = threading.Thread(
        target=_run, args=(str(job_id),), name=f"pyhmmer-{job_id}", daemon=True
    )
    thread.start()


def _run(job_id: str) -> None:
    close_old_connections()
    try:
        with _lock:
            close_old_connections()
            from ..tasks import execute_search

            execute_search(job_id)
    except Exception:
        logger.exception("PyHMMER search failed for job %s", job_id)
    finally:
        close_old_connections()
