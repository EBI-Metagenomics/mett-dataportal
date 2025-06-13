import json
import logging
import math
import uuid

from django.shortcuts import get_object_or_404
from django_celery_results.models import TaskResult
from ninja import Router, Query
from ninja.errors import HttpError

from dataportal import settings

logger = logging.getLogger(__name__)

ROUTER_PYHMMER_SEARCH = "pyhmmer"
pyhmmer_router = Router(tags=[ROUTER_PYHMMER_SEARCH])

import logging
from django.http import HttpRequest
from ninja import Router

from .models import HmmerJob, Database
from .schemas import SearchRequestSchema, SearchResponseSchema, JobDetailsResponseSchema, ResultQuerySchema
from .tasks import run_search, test_task

logger = logging.getLogger(__name__)

pyhmmer_router = Router(tags=["pyhmmer"])

@pyhmmer_router.post("/search", response=SearchResponseSchema)
def search(request: HttpRequest, body: SearchRequestSchema):
    try:
        job = HmmerJob(**body.dict(), algo=HmmerJob.AlgoChoices.PHMMER)
        job.clean()
        job.save()

        run_search.delay(job.id)

        return {"id": job.id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

@pyhmmer_router.post("/testtask")
def search(request: HttpRequest):
    try:
        result = test_task.delay()
        job = HmmerJob.objects.create(
            input="mock-seq",  # dummy
            database=HmmerJob.DbChoices.BU_TYPE_STRAINS
        )
        return {"job_id": str(job.id)}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


@pyhmmer_router.get("/search/{uuid:id}", response=JobDetailsResponseSchema)
def get_result(request, id: uuid.UUID, query: Query[ResultQuerySchema]):
    try:
        logger.info(f"Fetching job with ID: {id}")
        job = get_object_or_404(HmmerJob, id=id)
        logger.info(f"Found job: {job}")

        try:
            status = job.task.status if job.task else "PENDING"
            logger.info(f"Job status: {status}")
        except AttributeError as e:
            logger.error(f"Error getting task status: {str(e)}")
            status = "PENDING"

        if status != "SUCCESS":
            logger.info(f"Job not successful, returning status: {status}")
            return {
                "status": status,
                "task": None,
                "database": None,
                "id": job.id,
                "algo": job.algo,
                "input": job.input,
                "threshold": job.threshold,
                "threshold_value": job.threshold_value
            }

        db_config = settings.HMMER_DATABASES.get(job.database)
        if not db_config:
            logger.error(f"Database {job.database} not configured")
            raise HttpError(500, f"Database {job.database} not configured")

        try:
            # Get the database object
            database = Database.objects.get(id=job.database)
            logger.info(f"Found database: {database}")
        except Database.DoesNotExist:
            logger.error(f"Database with id {job.database} does not exist")
            raise HttpError(500, f"Database {job.database} not found")
        
        # Get the task result
        task_result = job.task
        logger.info(f"Task result: {task_result}")

        response = {
            "status": status,
            "task": task_result,
            "database": database,
            "id": job.id,
            "algo": job.algo,
            "input": job.input,
            "threshold": job.threshold,
            "threshold_value": job.threshold_value
        }
        logger.info(f"Returning response: {response}")
        return response

    except Exception as e:
        logger.error(f"Unexpected error in get_result: {str(e)}", exc_info=True)
        raise HttpError(500, f"Internal server error: {str(e)}")