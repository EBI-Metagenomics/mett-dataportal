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
