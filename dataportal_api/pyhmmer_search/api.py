import json
import logging
import uuid
from typing import List

from django.utils import timezone

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
from .schemas import (
    DomainDetailsResponseSchema,
    SearchRequestSchema,
    SearchResponseSchema,
    JobDetailsResponseSchema,
    ResultQuerySchema,
    DatabaseResponseSchema,
)
from .tasks import run_search, test_task

logger = logging.getLogger(__name__)

pyhmmer_router = Router(tags=["pyhmmer"])


@pyhmmer_router.post("/search", response=SearchResponseSchema)
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


@pyhmmer_router.post("/testtask")
def search(request: HttpRequest):
    try:
        # Create the job first
        job = HmmerJob.objects.create(
            input="mock-seq", database=HmmerJob.DbChoices.BU_TYPE_STRAINS  # dummy
        )

        # Run the test task
        result = test_task.delay()
        task_id = result.id
        logger.info(f"Started test task with ID: {task_id}")

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

        # Verify task status using AsyncResult
        from celery.result import AsyncResult

        async_result = AsyncResult(task_id)
        logger.info(f"Task {task_id} status from AsyncResult: {async_result.status}")

        return {"job_id": str(job.id)}

    except Exception as e:
        logger.error(f"Error in testtask: {str(e)}", exc_info=True)
        raise HttpError(500, f"Error creating test task: {str(e)}")


@pyhmmer_router.get("/search/{uuid:id}", response=JobDetailsResponseSchema)
def get_result(request, id: uuid.UUID, query: Query[ResultQuerySchema]):
    from celery.result import AsyncResult

    try:
        logger.info(f"Fetching job with ID: {id}")
        job = get_object_or_404(HmmerJob, id=id)
        logger.info(f"Found job: {job}")

        task_status = "PENDING"
        task_result_data = None

        if job.task:
            async_result = AsyncResult(job.task.task_id)
            task_status = async_result.status
            logger.info(f"Task {job.task.task_id} status: {task_status}")

            # Attempt to load result from DB
            raw_result = job.task.result
            try:
                task_result_data = (
                    json.loads(raw_result)
                    if isinstance(raw_result, str)
                    else raw_result
                )
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON result: {raw_result}")
                task_result_data = raw_result  # fallback

        if task_status != "SUCCESS":
            logger.info(f"Job not successful, returning status: {task_status}")
            return {
                "status": task_status,
                "task": {
                    "status": job.task.status if job.task else "PENDING",
                    "date_created": job.task.date_created if job.task else None,
                    "date_done": job.task.date_done if job.task else None,
                    "result": None,
                },
                "database": None,
                "id": job.id,
                "algo": job.algo,
                "input": job.input,
                "threshold": job.threshold,
                "threshold_value": job.threshold_value,
            }

        db_config = settings.HMMER_DATABASES.get(job.database)
        if not db_config:
            logger.error(f"Database {job.database} not configured")
            raise HttpError(500, f"Database {job.database} not configured")

        try:
            database = Database.objects.get(id=job.database)
            logger.info(f"Found database: {database}")
        except Database.DoesNotExist:
            logger.error(f"Database with id {job.database} does not exist")
            raise HttpError(500, f"Database {job.database} not found")

        response = {
            "status": task_status,
            "task": {
                "status": job.task.status,
                "date_created": job.task.date_created,
                "date_done": job.task.date_done,
                "result": task_result_data or [],
            },
            "database": database,
            "id": job.id,
            "algo": job.algo,
            "input": job.input,
            "threshold": job.threshold,
            "threshold_value": job.threshold_value,
        }
        logger.info(f"Returning response with {len(task_result_data or [])} hits")
        return response

    except Exception as e:
        logger.error(f"Unexpected error in get_result: {str(e)}", exc_info=True)
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router.get("/debug/task/{task_id}")
def debug_task(request, task_id: str):
    try:
        from celery.result import AsyncResult

        # First try to get the task status directly
        task_result = AsyncResult(task_id)
        logger.info(f"Task {task_id} status from AsyncResult: {task_result.status}")

        # If the task exists, get its linked jobs
        if task_result.status != "PENDING" or task_result.result is not None:
            linked_jobs = HmmerJob.objects.filter(task__task_id=task_id)
            logger.info(f"Found {linked_jobs.count()} jobs linked to task {task_id}")

            return {
                "task": {
                    "id": task_id,
                    "status": task_result.status,
                    "result": task_result.result,
                    "date_created": (
                        task_result.date_created
                        if hasattr(task_result, "date_created")
                        else None
                    ),
                    "date_done": (
                        task_result.date_done
                        if hasattr(task_result, "date_done")
                        else None
                    ),
                    "traceback": task_result.traceback,
                    "meta": task_result.info,
                },
                "linked_jobs": [
                    {
                        "id": str(job.id),
                        "status": task_result.status,  # Use the same task status
                        "input": job.input,
                        "database": job.database,
                        "task_id": task_id,
                    }
                    for job in linked_jobs
                ],
            }

        # If the task doesn't exist, try to find a job with this ID
        try:
            job = HmmerJob.objects.get(id=task_id)
            if job.task:
                # Get the actual task status
                job_task = AsyncResult(job.task.task_id)
                logger.info(
                    f"Found job {task_id} with task {job.task.task_id}, status: {job_task.status}"
                )

                return {
                    "task": {
                        "id": job.task.task_id,
                        "status": job_task.status,
                        "result": job_task.result,
                        "date_created": (
                            job_task.date_created
                            if hasattr(job_task, "date_created")
                            else None
                        ),
                        "date_done": (
                            job_task.date_done
                            if hasattr(job_task, "date_done")
                            else None
                        ),
                        "traceback": job_task.traceback,
                        "meta": job_task.info,
                    },
                    "linked_jobs": [
                        {
                            "id": str(job.id),
                            "status": job_task.status,
                            "input": job.input,
                            "database": job.database,
                            "task_id": job.task.task_id,
                        }
                    ],
                }
        except HmmerJob.DoesNotExist:
            pass

        # If we get here, neither a task nor a job was found
        return {
            "task": {
                "id": task_id,
                "status": "PENDING",
                "result": None,
                "date_created": None,
                "date_done": None,
                "traceback": None,
                "meta": None,
            },
            "linked_jobs": [],
        }

    except Exception as e:
        logger.error(f"Error in debug_task: {str(e)}", exc_info=True)
        raise HttpError(500, f"Error getting task info: {str(e)}")


@pyhmmer_router.get("/search/{uuid:id}/domains", response=DomainDetailsResponseSchema)
def get_domain_details(request, id: uuid.UUID, target: str):
    from celery.result import AsyncResult

    try:
        logger.info(f"Fetching domain details for job {id}, target {target}")
        job = get_object_or_404(HmmerJob, id=id)
        if not job.task:
            return {"status": "PENDING", "target": target, "domains": None}
        async_result = AsyncResult(job.task.task_id)
        if async_result.status != "SUCCESS":
            return {"status": async_result.status, "target": target, "domains": None}
        raw_result = job.task.result
        try:
            task_result_data = (
                json.loads(raw_result) if isinstance(raw_result, str) else raw_result
            )
        except json.JSONDecodeError:
            logger.warning(f"Failed to decode JSON result: {raw_result}")
            task_result_data = raw_result
        # Find the hit for the given target
        hit = None
        for h in task_result_data or []:
            if (
                h.get("target") == target
                or h.get("target_name") == target
                or h.get("name") == target
            ):
                hit = h
                break
        if not hit:
            return {"status": "NOT_FOUND", "target": target, "domains": None}
        # Return the domains/alignment details (assuming 'domains' or similar key)
        domains = hit.get("domains") or hit.get("alignments") or []
        return {"status": "SUCCESS", "target": target, "domains": domains}
    except Exception as e:
        logger.error(f"Error in get_domain_details: {str(e)}", exc_info=True)
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router.get(
    "/databases", response=List[DatabaseResponseSchema], tags=["search"]
)
def get_databases(request):
    return Database.objects.all().order_by("order")


@pyhmmer_router.get("/mxchoices", tags=["search"])
def get_matrices(request):
    from .models import HmmerJob

    return [
        {"value": choice[0], "label": choice[1]}
        for choice in HmmerJob.MXChoices.choices
    ]
