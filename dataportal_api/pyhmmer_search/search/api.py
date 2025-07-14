import logging
from typing import List

from django.utils import timezone
from django_celery_results.models import TaskResult
from ninja import Router
from ninja.errors import HttpError

logger = logging.getLogger(__name__)

ROUTER_PYHMMER_SEARCH = "pyhmmer_search"
pyhmmer_router_search = Router(tags=[ROUTER_PYHMMER_SEARCH])

import logging
from django.http import HttpRequest

from .models import HmmerJob, Database
from .schemas import (
    SearchRequestSchema,
    SearchResponseSchema,
    DatabaseResponseSchema,
)
from .tasks import run_search

logger = logging.getLogger(__name__)


@pyhmmer_router_search.post("", response=SearchResponseSchema)
def search(request: HttpRequest, body: SearchRequestSchema):
    try:
        logger.info(f"=== SEARCH REQUEST RECEIVED ===")
        logger.info(f"Request body: {body.dict()}")
        
        # Create the job
        logger.info(f"Creating HmmerJob...")
        job = HmmerJob(**body.dict(), algo=HmmerJob.AlgoChoices.PHMMER)
        logger.info(f"Job object created: {job}")
        logger.info(f"Job ID before save: {job.id}")
        
        job.clean()
        logger.info(f"Job cleaned successfully")
        
        job.save()
        logger.info(f"Job saved to database with ID: {job.id}")

        # Start the task
        logger.info(f"Starting Celery task...")
        result = run_search.delay(job.id)
        task_id = result.id
        logger.info(f"Celery task started with ID: {task_id}")
        logger.info(f"Celery result state: {result.state}")

        # Create task result entry
        logger.info(f"Creating TaskResult entry...")
        task_result = TaskResult.objects.create(
            task_id=task_id,
            status="PENDING",
            result=None,
            traceback=None,
            meta=None,
            date_done=None,
            date_created=timezone.now(),
        )
        logger.info(f"TaskResult created: {task_result}")
        logger.info(f"TaskResult ID: {task_result.id}")

        # Link the task to the job
        logger.info(f"Linking task to job...")
        job.task = task_result
        job.save(update_fields=["task"])
        logger.info(f"Task linked to job successfully")
        logger.info(f"Job task after linking: {job.task}")
        logger.info(f"Job task ID after linking: {job.task.task_id if job.task else 'None'}")

        response = {"id": job.id}
        logger.info(f"=== SEARCH REQUEST COMPLETED ===")
        logger.info(f"Returning response: {response}")
        return response
        
    except Exception as e:
        logger.error(f"=== SEARCH REQUEST FAILED ===")
        logger.error(f"Error in search: {str(e)}", exc_info=True)
        raise HttpError(500, f"Error creating search job: {str(e)}")


@pyhmmer_router_search.get(
    "/databases", response=List[DatabaseResponseSchema], tags=["search"]
)
def get_databases(request):
    return Database.objects.all().order_by("order")


@pyhmmer_router_search.get("/mxchoices", tags=["search"])
def get_matrices(request):
    from .models import HmmerJob

    return [
        {"value": choice[0], "label": choice[1]}
        for choice in HmmerJob.MXChoices.choices
    ]
