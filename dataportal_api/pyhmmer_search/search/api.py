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
        
        # Enhanced logging for all user-selected parameters
        logger.info(f"=== USER SELECTED PARAMETERS ===")
        logger.info(f"Database: {body.database}")
        logger.info(f"Threshold type: {body.threshold}")
        logger.info(f"Threshold value: {body.threshold_value}")
        logger.info(f"Substitution matrix (mx): {body.mx}")
        logger.info(f"Input sequence length: {len(body.input) if body.input else 0}")
        
        # E-value parameters
        logger.info(f"=== E-VALUE PARAMETERS ===")
        logger.info(f"E (Report E-values - Sequence): {body.E}")
        logger.info(f"domE (Report E-values - Hit): {body.domE}")
        logger.info(f"incE (Significance E-values - Sequence): {body.incE}")
        logger.info(f"incdomE (Significance E-values - Hit): {body.incdomE}")
        
        # Bit score parameters
        logger.info(f"=== BIT SCORE PARAMETERS ===")
        logger.info(f"T (Report Bit scores - Sequence): {body.T}")
        logger.info(f"domT (Report Bit scores - Hit): {body.domT}")
        logger.info(f"incT (Significance Bit scores - Sequence): {body.incT}")
        logger.info(f"incdomT (Significance Bit scores - Hit): {body.incdomT}")
        
        # Gap penalties
        logger.info(f"=== GAP PENALTIES ===")
        logger.info(f"popen (Gap open penalty): {body.popen}")
        logger.info(f"pextend (Gap extend penalty): {body.pextend}")
        
        # Create the job
        logger.info(f"Creating HmmerJob...")
        job = HmmerJob(**body.dict(), algo=HmmerJob.AlgoChoices.PHMMER)
        logger.info(f"Job object created: {job}")
        logger.info(f"Job ID before save: {job.id}")
        
        # Log the job parameters after creation
        logger.info(f"=== JOB PARAMETERS VERIFICATION ===")
        logger.info(f"Job database: {job.database}")
        logger.info(f"Job threshold: {job.threshold}")
        logger.info(f"Job threshold_value: {job.threshold_value}")
        logger.info(f"Job mx: {job.mx}")
        logger.info(f"Job E: {job.E}")
        logger.info(f"Job domE: {job.domE}")
        logger.info(f"Job incE: {job.incE}")
        logger.info(f"Job incdomE: {job.incdomE}")
        logger.info(f"Job T: {job.T}")
        logger.info(f"Job domT: {job.domT}")
        logger.info(f"Job incT: {job.incT}")
        logger.info(f"Job incdomT: {job.incdomT}")
        logger.info(f"Job popen: {job.popen}")
        logger.info(f"Job pextend: {job.pextend}")
        
        job.clean()
        logger.info(f"Job cleaned successfully")
        
        # Save job first and ensure it's committed
        job.save()
        logger.info(f"Job saved to database with ID: {job.id}")
        
        # Verify job exists in database before starting task
        try:
            # Refresh from database to ensure we have the latest state
            job.refresh_from_db()
            logger.info(f"Job verified in database with ID: {job.id}")
            
            # Add a small delay to ensure the job is fully committed
            import time
            time.sleep(0.1)
            logger.info(f"Job {job.id} should be committed to database")
        except Exception as e:
            logger.error(f"Failed to verify job in database: {e}")
            raise HttpError(500, f"Failed to create job: {str(e)}")

        # Start the task
        logger.info(f"Starting Celery task...")
        job_id_str = str(job.id)
        logger.info(f"Passing job ID to task: {job_id_str}")
        logger.info(f"Job ID type: {type(job_id_str)}")
        logger.info(f"Job ID length: {len(job_id_str)}")
        
        result = run_search.delay(job_id_str)
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
                    "name": "Bacteroides uniformis All Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 1
                },
                {
                    "id": "bu_type_strains",
                    "name": "Bacteroides uniformis Type Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 2
                },
                {
                    "id": "pv_all",
                    "name": "Phocaeicola vulgatus All Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 3
                },
                {
                    "id": "pv_type_strains",
                    "name": "Phocaeicola vulgatus Type Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 4
                },
                {
                    "id": "bu_pv_all",
                    "name": "Bacteroides uniformis + Phocaeicola vulgatus All Strains",
                    "type": "seq",
                    "version": "1.0",
                    "release_date": "2024-01-01",
                    "order": 5
                },
                {
                    "id": "bu_pv_type_strains",
                    "name": "Bacteroides uniformis + Phocaeicola vulgatus Type Strains",
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
                "name": "Burkholderia ubonensis All Strains",
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
