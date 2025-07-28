import logging

from django.utils import timezone
from django_celery_results.models import TaskResult
from ninja import Router
from ninja.errors import HttpError

from dataportal.utils.response_wrappers import wrap_success_response
from .models import Database
from .models import HmmerJob
from .schemas import SearchRequestSchema, SearchResponseSchema
from .tasks import run_search

logger = logging.getLogger(__name__)

pyhmmer_router_search = Router(tags=["PyHMMER Search"])


@pyhmmer_router_search.post("", response=SearchResponseSchema)
def search(request, body: SearchRequestSchema):
    try:
        logger.info("=== SEARCH REQUEST RECEIVED ===")
        logger.info(f"Request body: {body.dict()}")

        # Create the job
        logger.info("Creating HmmerJob...")
        job = HmmerJob(**body.dict(), algo=HmmerJob.AlgoChoices.PHMMER)
        logger.info(f"Job object created: {job}")
        logger.info(f"Job ID before save: {job.id}")

        job.clean()
        logger.info("Job cleaned successfully")

        job.save()
        logger.info(f"Job saved to database with ID: {job.id}")

        try:
            job.refresh_from_db()
            logger.info(f"Job verified in database with ID: {job.id}")

            import time

            time.sleep(0.1)
            logger.info(f"Job {job.id} should be committed to database")
        except Exception as e:
            logger.error(f"Failed to verify job in database: {e}")
            raise HttpError(500, f"Failed to create job: {str(e)}")

        # Start the task
        logger.info("Starting Celery task...")
        job_id_str = str(job.id)

        result = run_search.delay(job_id_str)
        logger.info(f"Celery task started with ID: {result.id}")

        # Create TaskResult entry
        logger.info("Creating TaskResult entry...")
        task_result = TaskResult.objects.create(
            task_id=result.id,
            status="PENDING",
            result=None,
            traceback=None,
            meta=None,
            date_done=None,
            date_created=timezone.now(),
        )
        logger.info(f"TaskResult created: {task_result}")

        job.task = task_result
        job.save()
        logger.info("Task linked successfully")

        logger.info("=== SEARCH REQUEST COMPLETED ===")
        logger.info(f"Job ID: {job.id}")
        logger.info(f"Task ID: {result.id}")

        return {"id": job.id}

    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_search.get("/databases", include_in_schema=False)
@wrap_success_response
def get_databases(request):
    """Get available databases for PyHMMER search."""
    try:
        databases = Database.objects.all().order_by("order")

        return [
            {
                "id": db.id,
                "name": db.name,
                "type": db.type,
                "version": db.version,
                "release_date": (
                    db.release_date.isoformat() if db.release_date else None
                ),
                "order": db.order,
            }
            for db in databases
        ]
    except Exception as e:
        logger.error(f"Error getting databases: {e}")
        return [
            {
                "id": "bu_pv_all",
                "name": "Bacteroides uniformis + Phocaeicola vulgatus All Strains",
                "type": "seq",
                "version": "1.0",
                "release_date": "2024-01-01",
                "order": 1,
            }
        ]


@pyhmmer_router_search.get("/mx-choices", include_in_schema=False)
@wrap_success_response
def get_mx_choices(request):
    try:
        choices = [
            {"value": choice[0], "label": choice[1]}
            for choice in HmmerJob.MXChoices.choices
        ]
        return choices
    except Exception as e:
        logger.error(f"Error getting MX choices: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")
