import logging

from ninja import Router

logger = logging.getLogger(__name__)

ROUTER_PYHMMER_SEARCH = "pyhmmer"
pyhmmer_router = Router(tags=[ROUTER_PYHMMER_SEARCH])

import logging
from django.http import HttpRequest
from ninja import Router

from .models import HmmerJob
from .schemas import SearchRequestSchema, SearchResponseSchema, JobDetailsResponseSchema
from .tasks import run_search

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


@pyhmmer_router.get("/search/{uuid:id}", response=JobDetailsResponseSchema)
def get_job_details(request, id: str):
    job = HmmerJob.objects.get(id=id)
    return job
