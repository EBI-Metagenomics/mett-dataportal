import logging
import uuid
from typing import List

from django.conf import settings
from django.utils import timezone
from django_celery_results.models import TaskResult
from ninja import Router
from ninja.errors import HttpError
from asgiref.sync import sync_to_async

from .models import HmmerJob, Database
from .schemas import SearchRequestSchema, SearchResponseSchema
from .tasks import run_search
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.schema.response_schemas import create_success_response

logger = logging.getLogger(__name__)

pyhmmer_router_search = Router(tags=["PyHMMER Search"])


@pyhmmer_router_search.post("", response=SearchResponseSchema)
def search(request, body: SearchRequestSchema):
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
        result = run_search.delay(str(job.id))
        logger.info(f"Celery task started with ID: {result.id}")
        
        # Create TaskResult entry
        logger.info(f"Creating TaskResult entry...")
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
        
        # Link the task to the job
        logger.info(f"Linking task to job...")
        job.task = task_result
        job.save()
        logger.info(f"Task linked successfully")
        
        logger.info(f"=== SEARCH REQUEST COMPLETED ===")
        logger.info(f"Job ID: {job.id}")
        logger.info(f"Task ID: {result.id}")
        
        return {"id": job.id}
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_search.get("/databases")
@wrap_success_response
def get_databases(request):
    """Get available databases for PyHMMER search."""
    try:
        databases = Database.objects.all().order_by('order')
        
        # If no databases exist, return default ones
        if not databases.exists():
            default_databases = [
                {
                    "id": "bu_all",
                    "name": "BU All Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 1
                },
                {
                    "id": "bu_type_strains",
                    "name": "BU Type Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 2
                },
                {
                    "id": "pv_all",
                    "name": "PV All Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 3
                },
                {
                    "id": "pv_type_strains",
                    "name": "PV Type Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 4
                },
                {
                    "id": "bu_pv_all",
                    "name": "BU+PV All Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 5
                },
                {
                    "id": "bu_pv_type_strains",
                    "name": "BU+PV Type Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 6
                }
            ]
            return default_databases
        
        return [
            {
                "id": db.id, 
                "name": db.name, 
                "type": db.type,
                "version": db.version,
                "release_date": db.release_date.isoformat() if db.release_date else None,
                "order": db.order
            }
            for db in databases
        ]
    except Exception as e:
        logger.error(f"Error getting databases: {e}")
        # Return default databases as fallback
        return [
            {
                "id": "bu_all",
                "name": "BU All Strains",
                "type": "seq",
                "version": "1.0",
                "release_date": "2024-01-01",
                "order": 1
            }
        ]


@pyhmmer_router_search.get("/mx-choices")
@wrap_success_response
def get_mx_choices(request):
    """Get available substitution matrices for PyHMMER search."""
    try:
        choices = [
            {"value": "BLOSUM62", "label": "BLOSUM62"},
            {"value": "BLOSUM45", "label": "BLOSUM45"},
            {"value": "BLOSUM90", "label": "BLOSUM90"},
            {"value": "PAM30", "label": "PAM30"},
            {"value": "PAM70", "label": "PAM70"},
            {"value": "PAM250", "label": "PAM250"},
        ]
        return choices
    except Exception as e:
        logger.error(f"Error getting MX choices: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")
