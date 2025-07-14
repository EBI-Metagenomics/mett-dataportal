import json
import logging
import uuid

from django.shortcuts import get_object_or_404
from ninja import Router, Query
from ninja.errors import HttpError
from django.http import StreamingHttpResponse, HttpResponse
import gzip
from io import BytesIO, StringIO

from dataportal import settings

logger = logging.getLogger(__name__)

ROUTER_PYHMMER_RESULT = "pyhmmer_result"
pyhmmer_router_result = Router(tags=[ROUTER_PYHMMER_RESULT])

import logging

from ..search.models import HmmerJob, Database
from .schemas import (
    DomainDetailsResponseSchema,
    JobDetailsResponseSchema,
    ResultQuerySchema,
    AlignmentDetailsResponseSchema,
)

logger = logging.getLogger(__name__)


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
        task_result_data = None

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

            # Attempt to load result from DB
            raw_result = job.task.result
            logger.info(f"Raw result from database: {raw_result}")
            logger.info(f"Raw result type: {type(raw_result)}")
            logger.info(f"Raw result is None: {raw_result is None}")
            
            if raw_result is not None:
                logger.info(f"Raw result length: {len(str(raw_result))}")
                logger.info(f"Raw result preview: {str(raw_result)[:200]}...")
            
            # Also check if AsyncResult has the result
            logger.info(f"AsyncResult has result: {async_result.result is not None}")
            if async_result.result is not None:
                logger.info(f"AsyncResult result type: {type(async_result.result)}")
                if isinstance(async_result.result, list):
                    logger.info(f"AsyncResult result length: {len(async_result.result)}")
                    logger.info(f"AsyncResult first result: {async_result.result[0] if async_result.result else 'None'}")
            
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
                    task_result_data = json.loads(raw_result)
                    logger.info("JSON decode successful")
                else:
                    logger.info("Raw result is not string, using as-is...")
                    task_result_data = raw_result
                
                logger.info(f"Final parsed result data type: {type(task_result_data)}")
                if isinstance(task_result_data, list):
                    logger.info(f"Final result list length: {len(task_result_data)}")
                    if task_result_data:
                        logger.info(f"Final first result item: {task_result_data[0]}")
                        logger.info(f"Final first result item type: {type(task_result_data[0])}")
                else:
                    logger.info(f"Final result data is not a list: {task_result_data}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON result: {e}")
                logger.error(f"Raw result that failed to decode: {raw_result}")
                # Try AsyncResult as fallback
                if async_result.result is not None:
                    logger.info("Using AsyncResult result as fallback after JSON decode error")
                    task_result_data = async_result.result
                else:
                    task_result_data = raw_result  # fallback
            except Exception as e:
                logger.error(f"Unexpected error parsing result: {e}")
                # Try AsyncResult as fallback
                if async_result.result is not None:
                    logger.info("Using AsyncResult result as fallback after parsing error")
                    task_result_data = async_result.result
                else:
                    task_result_data = raw_result  # fallback
        else:
            logger.warning("Job has no task associated")

        logger.info(f"Final task_status: {task_status}")
        logger.info(f"Final task_result_data type: {type(task_result_data)}")
        if isinstance(task_result_data, list):
            logger.info(f"Final task_result_data length: {len(task_result_data)}")

        if task_status != "SUCCESS":
            logger.info(f"Job not successful, returning status: {task_status}")
            response = {
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
            logger.info(f"Returning non-success response: {response}")
            return response

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
        logger.info(f"=== RETURNING SUCCESS RESPONSE ===")
        logger.info(f"Response status: {response['status']}")
        logger.info(f"Response task status: {response['task']['status']}")
        logger.info(f"Response result length: {len(response['task']['result'])}")
        logger.info(f"Response preview: {str(response)[:500]}...")
        return response

    except Exception as e:
        logger.error(f"=== UNEXPECTED ERROR IN GET_RESULT ===")
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/domains", response=DomainDetailsResponseSchema)
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
        # Return the domains/alignment details
        domains = hit.get("domains") or []
        return {"status": "SUCCESS", "target": target, "domains": domains}
    except Exception as e:
        logger.error(f"Error in get_domain_details: {str(e)}", exc_info=True)
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/alignment", response=AlignmentDetailsResponseSchema)
def get_alignment_details(request, id: uuid.UUID, target: str, domain_index: int = 0):
    """Get detailed alignment information for a specific domain"""
    from celery.result import AsyncResult

    try:
        logger.info(f"Fetching alignment details for job {id}, target {target}, domain {domain_index}")
        job = get_object_or_404(HmmerJob, id=id)
        if not job.task:
            return {"status": "PENDING", "target": target, "domain_index": domain_index, "alignment": None,
                    "legacy_alignment": None}

        async_result = AsyncResult(job.task.task_id)
        if async_result.status != "SUCCESS":
            return {"status": async_result.status, "target": target, "domain_index": domain_index, "alignment": None,
                    "legacy_alignment": None}

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
            return {"status": "NOT_FOUND", "target": target, "domain_index": domain_index, "alignment": None,
                    "legacy_alignment": None}

        # Get the specific domain
        domains = hit.get("domains") or []
        if domain_index >= len(domains):
            return {"status": "DOMAIN_NOT_FOUND", "target": target, "domain_index": domain_index, "alignment": None,
                    "legacy_alignment": None}

        domain = domains[domain_index]
        alignment = domain.get("alignment")
        legacy_alignment = domain.get("alignment_display")

        return {
            "status": "SUCCESS",
            "target": target,
            "domain_index": domain_index,
            "alignment": alignment,
            "legacy_alignment": legacy_alignment
        }

    except Exception as e:
        logger.error(f"Error in get_alignment_details: {str(e)}", exc_info=True)
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/download")
def download_results(request, id: uuid.UUID, format: str = 'tsv'):
    """
    Download significant hits in various formats: tab, fasta, aligned_fasta (all significant hits only)
    """
    from celery.result import AsyncResult
    import csv

    job = get_object_or_404(HmmerJob, id=id)
    if not job.task:
        raise HttpError(404, "Job not found or not finished")
    async_result = AsyncResult(job.task.task_id)
    if async_result.status != "SUCCESS":
        raise HttpError(400, "Job not finished")
    raw_result = job.task.result
    try:
        task_result_data = (
            json.loads(raw_result) if isinstance(raw_result, str) else raw_result
        )
    except json.JSONDecodeError:
        task_result_data = raw_result

    # Only significant hits
    significant_hits = [h for h in (task_result_data or []) if h.get('num_significant', 0) > 0 or (h.get('domains') and len(h.get('domains')) > 0)]

    if format == 'tsv':
        def tsv_stream():
            output = StringIO()
            writer = csv.writer(output, delimiter='\t')
            writer.writerow(["Target", "E-value", "Score", "Hits", "Significant Hits", "Description"])
            for h in significant_hits:
                writer.writerow([
                    h.get('target', ''),
                    h.get('evalue', ''),
                    h.get('score', ''),
                    h.get('num_hits', ''),
                    h.get('num_significant', ''),
                    h.get('description', '')
                ])
            yield output.getvalue()
        response = StreamingHttpResponse(tsv_stream(), content_type='text/tab-separated-values')
        response['Content-Disposition'] = f'attachment; filename="pyhmmer_hits_{id}.tsv"'
        return response

    elif format == 'fasta':
        def fasta_stream():
            buf = BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='w') as gz:
                for h in significant_hits:
                    domains = h.get('domains', [])
                    if domains:
                        aln = domains[0].get('alignment')
                        if aln and aln.get('target_sequence'):
                            seq = aln['target_sequence'].replace('-', '')
                            header = f">{h.get('target', '')}"
                            gz.write((header + "\n" + seq + "\n").encode('utf-8'))
            buf.seek(0)
            yield buf.read()
        response = StreamingHttpResponse(fasta_stream(), content_type='application/gzip')
        response['Content-Disposition'] = f'attachment; filename="pyhmmer_hits_{id}.fasta.gz"'
        return response

    elif format == 'aligned_fasta':
        def aligned_fasta_stream():
            buf = BytesIO()
            with gzip.GzipFile(fileobj=buf, mode='w') as gz:
                for h in significant_hits:
                    domains = h.get('domains', [])
                    for i, d in enumerate(domains):
                        aln = d.get('alignment')
                        if aln and aln.get('target_sequence'):
                            seq = aln['target_sequence']
                            header = f">{h.get('target', '')}"
                            if len(domains) > 1:
                                header += f"_{i+1}"
                            gz.write((header + "\n" + seq + "\n").encode('utf-8'))
            buf.seek(0)
            yield buf.read()
        response = StreamingHttpResponse(aligned_fasta_stream(), content_type='application/gzip')
        response['Content-Disposition'] = f'attachment; filename="pyhmmer_hits_{id}.aligned.fasta.gz"'
        return response

    else:
        raise HttpError(400, "Invalid format. Use one of: tsv, fasta, aligned_fasta")
