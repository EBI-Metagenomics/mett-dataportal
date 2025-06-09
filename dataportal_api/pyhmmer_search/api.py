import logging
from typing import List

from celery import chain, group
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, ModelSchema

from .models import HmmerJob, Database
from .schemas import DatabaseResponseSchema, TaskResultSchema, SearchResponseSchema, SearchRequestSchema, \
    JobDetailsResponseSchema, JobsResponseSchema
from .tasks import run_search

logger = logging.getLogger(__name__)

ROUTER_PYHMMER_SEARCH = "pyhmmer"
pyhmmer_router = Router(tags=[ROUTER_PYHMMER_SEARCH])


@pyhmmer_router.get("/databases", response=List[DatabaseResponseSchema], tags=["search"])
def get_databases(request):
    return Database.objects.all().order_by("order")



@pyhmmer_router.get("/{uuid:id}", response=JobDetailsResponseSchema, tags=["search"])
def get_job_details(request, id: str):
    job = get_object_or_404(HmmerJob, id=id)

    return job


@pyhmmer_router.get("/{uuid:id}/query", tags=["search"])
def get_job_query(request, id: str):
    job = get_object_or_404(HmmerJob, id=id)

    response = HttpResponse(job.input, content_type="text/plain")

    response["Content-Disposition"] = 'inline; filename="query.txt"'

    return response


@pyhmmer_router.post("{algo}", response=SearchResponseSchema, tags=["search"])
def search(request: HttpRequest, algo: HmmerJob.AlgoChoices, body: SearchRequestSchema):
    job = HmmerJob(**body.dict(), algo=algo)

    job.clean()
    job.save()

    request.session["job_ids"] = request.session.get("job_ids", []) + [str(job.id)]

    subsequent_tasks = []

    workflow = chain(
        run_search.si(job.id),
        group(*subsequent_tasks),
    )

    transaction.on_commit(lambda: workflow.delay())

    return {"id": job.id}


@pyhmmer_router.get("", response=List[JobsResponseSchema], tags=["search"])
def get_jobs(request):
    job_ids = request.session.get("job_ids", [])

    return HmmerJob.objects.filter(id__in=job_ids).select_related("task").order_by("-task__date_created")
