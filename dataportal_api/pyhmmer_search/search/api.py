import json
import logging
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.tasks import TaskResult
from django.utils import timezone
from ninja import Router

from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    create_success_response,
)
from dataportal.utils.errors import (
    raise_validation_error,
    raise_internal_server_error,
)
from dataportal.utils.response_wrappers import wrap_success_response
from .membership import DATABASE_ID, catalog_path
from .models import HmmerJob
from .runner import start_search
from .schemas import SearchRequestSchema

logger = logging.getLogger(__name__)

pyhmmer_router_search = Router(tags=["PyHMMER Search"])


@pyhmmer_router_search.post("", response=SuccessResponseSchema)
@wrap_success_response
def search(request, body: SearchRequestSchema):
    try:
        logger.info("=== SEARCH REQUEST RECEIVED ===")
        logger.debug("Request metadata captured; input sequence omitted for privacy.")

        # Create the job
        logger.info("Creating HmmerJob...")
        job = HmmerJob(**body.dict(), algo=HmmerJob.AlgoChoices.PHMMER)
        logger.info(f"Job object created: {job}")
        logger.info(f"Job ID before save: {job.id}")

        job.status = "PENDING"
        job.clean()
        job.save()
        logger.info(f"Job saved to database with ID: {job.id}")

        job_id_str = str(job.id)
        transaction.on_commit(lambda: start_search(job_id_str))
        logger.info("=== SEARCH REQUEST COMPLETED ===")
        logger.info(f"Job ID: {job.id}")

        return create_success_response(
            data={"id": job.id},
            message=f"PyHMMER search job created successfully with ID {job.id}",
        )

    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise_internal_server_error(f"Internal server error: {str(e)}")


def load_catalog() -> dict:
    path = catalog_path(settings.PYHMMER_DB)
    if path.is_file():
        return json.loads(path.read_text())
    species_csv = (
        Path(settings.BASE_DIR).parent
        / "data-generators"
        / "data"
        / "reference"
        / "species.csv"
    )
    species = []
    if species_csv.is_file():
        import csv

        with species_csv.open(newline="") as handle:
            for row in csv.DictReader(handle):
                acronym = (row.get("acronym") or "").strip()
                if not acronym:
                    continue
                species.append(
                    {
                        "acronym": acronym,
                        "name": (row.get("scientific_name") or acronym).strip(),
                        "isolates": 0,
                        "type_strain": (row.get("type_strain_isolate") or "").strip(),
                        "collection": "hd" if acronym in {"BU", "PV"} else "20hm",
                    }
                )
    return {
        "id": DATABASE_ID,
        "name": "METT proteins",
        "shortcuts": [
            {"id": "all", "label": "All species", "species": []},
            {
                "id": "hd",
                "label": "B. uniformis + P. vulgatus",
                "species": ["BU", "PV"],
            },
        ],
        "species": species,
    }


@pyhmmer_router_search.get("/databases", include_in_schema=False)
@wrap_success_response
def get_databases(request):
    """The search form uses one database. Species is a filter, not a second file."""
    return [
        {
            "id": DATABASE_ID,
            "name": "METT proteins",
            "type": "seq",
            "version": "1",
            "release_date": None,
            "order": 0,
        }
    ]


@pyhmmer_router_search.get("/catalog", include_in_schema=False)
@wrap_success_response
def get_catalog(request):
    """Species and shortcuts for the search form."""
    try:
        return load_catalog()
    except Exception as e:
        logger.error(f"Error getting protein catalog: {e}")
        return {
            "id": DATABASE_ID,
            "name": "METT proteins",
            "shortcuts": [{"id": "all", "label": "All species", "species": []}],
            "species": [],
        }


# @pyhmmer_router_search.get("/mx-choices", include_in_schema=False)
# @wrap_success_response
# def get_mx_choices(request):
#     try:
#         choices = [
#             {"value": choice[0], "label": choice[1]}
#             for choice in HmmerJob.MXChoices.choices
#         ]
#         return choices
#     except Exception as e:
#         logger.error(f"Error getting MX choices: {e}")
#         raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_search.get("/tasks-status", include_in_schema=False)
@wrap_success_response
def get_tasks_status(request, threshold_days: int = 30):
    """Get current status of PyHMMER task results in the database."""
    try:
        # Validate threshold_days parameter
        if threshold_days < 1 or threshold_days > 365:
            raise_validation_error("threshold_days must be between 1 and 365")

        cutoff = timezone.now() - timedelta(days=threshold_days)

        total_tasks = TaskResult.objects.count()
        old_tasks = TaskResult.objects.filter(date_done__lt=cutoff).count()
        recent_tasks = total_tasks - old_tasks

        return {
            "total_tasks": total_tasks,
            "old_tasks_eligible_for_cleanup": old_tasks,
            "recent_tasks": recent_tasks,
            "cutoff_date": cutoff.isoformat(),
            "cleanup_threshold_days": threshold_days,
        }
    except Exception as e:
        logger.error(f"Error getting PyHMMER tasks status: {e}")
        raise_internal_server_error(f"Failed to get tasks status: {str(e)}")


@pyhmmer_router_search.post("/cleanup-tasks", include_in_schema=False)
@wrap_success_response
def cleanup_tasks_manual(request, threshold_days: int = 30):
    """Manually trigger cleanup of old PyHMMER task results."""
    try:
        # Validate threshold_days parameter
        if threshold_days < 1 or threshold_days > 365:
            raise_validation_error("threshold_days must be between 1 and 365")

        # Use the same logic as the scheduled task
        cutoff = timezone.now() - timedelta(days=threshold_days)
        deleted, _ = TaskResult.objects.filter(date_done__lt=cutoff).delete()

        logger.info(
            f"Manual PyHMMER cleanup triggered: Deleted {deleted} old task results (threshold: {threshold_days} days)"
        )

        return {
            "message": f"Successfully deleted {deleted} old PyHMMER task results (older than {threshold_days} days)",
            "deleted_count": deleted,
            "cutoff_date": cutoff.isoformat(),
            "cleanup_threshold_days": threshold_days,
        }
    except Exception as e:
        logger.error(f"Error during manual PyHMMER cleanup: {e}")
        raise_internal_server_error(f"Failed to cleanup old PyHMMER tasks: {str(e)}")
