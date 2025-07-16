import logging
import uuid
from typing import List

from django.shortcuts import get_object_or_404
from django.conf import settings
from ninja import Router, Query
from ninja.errors import HttpError
from celery.result import AsyncResult
from asgiref.sync import sync_to_async

from ..search.models import HmmerJob, Database
from ..search.schemas import SearchRequestSchema
from .schemas import (
    JobDetailsResponseSchema,
    ResultQuerySchema,
    DomainDetailsResponseSchema,
    AlignmentDetailsResponseSchema
)
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.schema.response_schemas import create_success_response

logger = logging.getLogger(__name__)

pyhmmer_router_result = Router(tags=["PyHMMER Results"])


@pyhmmer_router_result.get("/{uuid:id}", response=JobDetailsResponseSchema)
def get_result(request, id: uuid.UUID, query: Query[ResultQuerySchema]):
    from celery.result import AsyncResult

    try:
        logger.info(f"=== GET_RESULT CALLED ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Query params: {query}")
        
        logger.info(f"Fetching job from database...")
        job = get_object_or_404(HmmerJob, id=id)
        logger.info(f"Found job: {job}")
        logger.info(f"Job ID: {job.id}")
        logger.info(f"Job database: {job.database}")
        logger.info(f"Job threshold: {job.threshold}")
        logger.info(f"Job threshold_value: {job.threshold_value}")

        task_status = "PENDING"
        task_result_data = []

        if job.task:
            logger.info(f"Job has task: {job.task}")
            logger.info(f"Task ID: {job.task.task_id}")
            logger.info(f"Task status in DB: {job.task.status}")
            logger.info(f"Task date_created: {job.task.date_created}")
            logger.info(f"Task date_done: {job.task.date_done}")
            
            async_result = AsyncResult(job.task.task_id)
            task_status = async_result.status
            logger.info(f"AsyncResult status: {task_status}")
            logger.info(f"AsyncResult state: {async_result.state}")
            logger.info(f"AsyncResult info: {async_result.info}")
            logger.info(f"AsyncResult task_id: {async_result.task_id}")
            logger.info(f"Database task_id: {job.task.task_id}")
            logger.info(f"Task IDs match: {async_result.task_id == job.task.task_id}")
            
            # Get raw result from database
            raw_result = job.task.result
            logger.info(f"Raw result from database: {raw_result}")
            logger.info(f"Raw result type: {type(raw_result)}")
            logger.info(f"Raw result is None: {raw_result is None}")
            
            try:
                if raw_result is None:
                    logger.warning("Raw result is None, checking AsyncResult for fallback...")
                    if async_result.result is not None:
                        logger.info("Using AsyncResult result as fallback")
                        task_result_data = async_result.result
                    else:
                        logger.warning("Both database and AsyncResult have no result, setting empty list")
                        task_result_data = []
                elif isinstance(raw_result, str):
                    logger.info("Raw result is string, attempting JSON decode...")
                    import json
                    task_result_data = json.loads(raw_result)
                else:
                    logger.info("Raw result is already a list/dict, using as is")
                    task_result_data = raw_result
            except Exception as e:
                logger.error(f"Error parsing result: {e}")
                task_result_data = []
            
            logger.info(f"Parsed result data type: {type(task_result_data)}")
            logger.info(f"Result list length: {len(task_result_data) if isinstance(task_result_data, list) else 'N/A'}")
        else:
            logger.warning("Job has no task associated")

        logger.info(f"Final task_status: {task_status}")
        logger.info(f"Final task_result_data type: {type(task_result_data)}")
        logger.info(f"Final task_result_data length: {len(task_result_data) if isinstance(task_result_data, list) else 'N/A'}")

        if task_status != "SUCCESS":
            logger.info(f"Job not successful, returning status: {task_status}")
            response_data = {
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
            logger.info(f"Returning non-success response: {response_data}")
            # Return the data directly for the wrapper to handle
            return response_data

        logger.info(f"Job is successful, getting database info...")
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

        response_data = {
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
        
        logger.info(f"=== RETURNING SUCCESS RESPONSE ===")
        logger.info(f"Response status: {response_data['status']}")
        logger.info(f"Response task status: {response_data['task']['status']}")
        logger.info(f"Response result length: {len(response_data['task']['result']) if response_data['task']['result'] else 0}")
        logger.info(f"Response preview: {response_data}")
        
        # Return the data directly for the wrapper to handle
        return response_data

    except Exception as e:
        logger.error(f"Error in get_result: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/domains", response=DomainDetailsResponseSchema)
def get_domains_by_target(request, id: uuid.UUID, target: str):
    """Get domains for a specific target in a search result."""
    try:
        job = get_object_or_404(HmmerJob, id=id)
        
        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")
        
        # Parse the result to get domain details
        import json
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []
        
        # Find the target in the results
        target_data = None
        for item in result_data:
            if item.get('target') == target:
                target_data = item
                break
        
        if not target_data:
            raise HttpError(404, f"Target '{target}' not found in results")
        
        domains = target_data.get('domains', [])
        
        return {
            "status": "success",
            "target": target_data.get('target', ''),
            "domains": domains
        }
        
    except Exception as e:
        logger.error(f"Error in get_domains_by_target: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/domains/{int:domain_index}", response=DomainDetailsResponseSchema)
@wrap_success_response
def get_domain_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed information about a specific domain in a search result."""
    try:
        job = get_object_or_404(HmmerJob, id=id)
        
        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")
        
        # Parse the result to get domain details
        import json
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []
        
        if not result_data or domain_index >= len(result_data):
            raise HttpError(404, "Domain not found")
        
        target_data = result_data[domain_index]
        domains = target_data.get('domains', [])
        
        return {
            "status": "success",
            "target": target_data.get('target', ''),
            "domains": domains
        }
        
    except Exception as e:
        logger.error(f"Error in get_domain_details: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/alignment/{int:domain_index}", response=AlignmentDetailsResponseSchema)
@wrap_success_response
def get_alignment_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed alignment information for a specific domain."""
    try:
        job = get_object_or_404(HmmerJob, id=id)
        
        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")
        
        # Parse the result to get alignment details
        import json
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []
        
        if not result_data or domain_index >= len(result_data):
            raise HttpError(404, "Domain not found")
        
        target_data = result_data[domain_index]
        domains = target_data.get('domains', [])
        
        if not domains:
            raise HttpError(404, "No domains found for this target")
        
        # Return the first domain's alignment (you might want to add a domain parameter)
        domain = domains[0]
        
        return {
            "status": "success",
            "target": target_data.get('target', ''),
            "domain_index": domain_index,
            "alignment": domain.get('alignment'),
            "legacy_alignment": domain.get('alignment_display')
        }
        
    except Exception as e:
        logger.error(f"Error in get_alignment_details: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")
