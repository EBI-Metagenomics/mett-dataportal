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
        # Create the job
        job = HmmerJob(**body.dict(), algo=HmmerJob.AlgoChoices.PHMMER)
        job.clean()
        job.save()
        logger.info(f"Created job with ID: {job.id}")

        # Start the task
        result = run_search.delay(job.id)
        task_id = result.id
        logger.info(f"Started search task with ID: {task_id}")

        # Create task result entry
        task_result = TaskResult.objects.create(
            task_id=task_id,
            status="PENDING",
            result=None,
            traceback=None,
            meta=None,
            date_done=None,
            date_created=timezone.now(),
        )
        logger.info(f"Created task result for task ID: {task_id}")

        # Link the task to the job
        job.task = task_result
        job.save(update_fields=["task"])
        logger.info(f"Linked task {task_id} to job {job.id}")

        return {"id": job.id}
    except Exception as e:
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
