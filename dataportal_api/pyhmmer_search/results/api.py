import gzip
import json
import logging
import uuid

from celery.result import AsyncResult
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Query
from dataportal.schema.response_schemas import (
    ErrorCode,
    SuccessResponseSchema,
    create_success_response,
)
from dataportal.utils.errors import (
    raise_validation_error,
    raise_not_found_error,
    raise_internal_server_error,
)
from dataportal.utils.response_wrappers import wrap_success_response
from .schemas import (
    ResultQuerySchema,
)
from .services import (
    DownloadTSVService,
    DownloadFastaService,
    DownloadAlignedFastaService,
)
from ..search.models import HmmerJob, Database

logger = logging.getLogger(__name__)

pyhmmer_router_result = Router(tags=["PyHMMER Results"])


def job_status_and_results(job):
    """Prefer status stored on the job. Fall back to a legacy Celery task."""
    if job.status:
        result = job.result if isinstance(job.result, list) else []
        task = {
            "status": job.status,
            "date_created": job.created_at,
            "date_done": job.finished_at,
            "result": result if job.status == "SUCCESS" else None,
        }
        return job.status, result, task

    if not job.task:
        task = {
            "status": "PENDING",
            "date_created": None,
            "date_done": None,
            "result": None,
        }
        return "PENDING", [], task

    async_result = AsyncResult(job.task.task_id)
    task_status = async_result.status or job.task.status or "PENDING"
    raw_result = job.task.result
    if raw_result is None and async_result.result is not None:
        task_result_data = async_result.result
    elif isinstance(raw_result, str):
        try:
            task_result_data = json.loads(raw_result)
        except json.JSONDecodeError:
            task_result_data = []
    else:
        task_result_data = raw_result or []
    if not isinstance(task_result_data, list):
        task_result_data = []
    task = {
        "status": job.task.status or task_status,
        "date_created": job.task.date_created,
        "date_done": job.task.date_done,
        "result": task_result_data if task_status == "SUCCESS" else None,
    }
    return task_status, task_result_data, task


def protein_db_path(job) -> str:
    if not job.status and job.database in settings.HMMER_DATABASES:
        return settings.HMMER_DATABASES[job.database]
    if not job.status and str(job.database).startswith("isolate_"):
        return settings.get_isolate_database_path(
            job.database.replace("isolate_", "", 1)
        )
    return settings.PYHMMER_DB


@pyhmmer_router_result.get("/{uuid:id}/download")
def download_results(request, id: uuid.UUID, format: str):
    """Download search results in various formats (tab, fasta, aligned_fasta)"""
    try:
        logger.info("=== DOWNLOAD REQUEST ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Format: {format}")

        # Validate format
        if format not in ["tab", "fasta", "aligned_fasta"]:
            raise_validation_error(
                f"Invalid format: {format}. Supported formats: tab, fasta, aligned_fasta"
            )

        job = get_object_or_404(HmmerJob, id=id)
        task_status, result_data, _task = job_status_and_results(job)

        if task_status != "SUCCESS":
            raise_validation_error("Job not completed successfully")

        if not result_data:
            raise_not_found_error(
                message="No results found for this job",
                error_code=ErrorCode.RESULT_NOT_FOUND,
            )

        db_path = protein_db_path(job)
        if not db_path:
            raise_internal_server_error(f"Database {job.database} not configured")

        if format == "tab":
            content = DownloadTSVService.generate_tsv_content(result_data)
            filename = f"pyhmmer_hits_{id}.tsv"
            content_type = "text/tab-separated-values"
        elif format == "fasta":
            content = DownloadFastaService.generate_enhanced_fasta_content(
                result_data, db_path, job.input
            )
            filename = f"pyhmmer_hits_{id}.fasta.gz"
            content_type = "application/gzip"
            logger.info(f"Generated FASTA content type: {type(content)}")
            logger.info(f"Generated FASTA content length: {len(content)}")
        elif format == "aligned_fasta":
            content = (
                DownloadAlignedFastaService.generate_enhanced_aligned_fasta_content(
                    result_data, db_path, job.input
                )
            )
            filename = f"pyhmmer_hits_{id}.aligned.fasta.gz"
            content_type = "application/gzip"
            logger.info(f"Generated aligned FASTA content type: {type(content)}")
            logger.info(f"Generated aligned FASTA content length: {len(content)}")

        # Create response
        if format in ["fasta", "aligned_fasta"]:
            if isinstance(content, str):
                content = content.encode("utf-8")

            try:
                test_decompressed = gzip.decompress(content)
                logger.info(
                    f"Decompression test passed: {len(test_decompressed)} bytes"
                )
            except Exception as decompress_error:
                logger.error(f"Decompression test failed: {decompress_error}")
                # If decompression fails, return uncompressed content
                logger.warning(
                    "Returning uncompressed content due to compression failure"
                )
                content = (
                    DownloadFastaService.generate_enhanced_fasta_content(
                        result_data, db_path, job.input
                    )
                    if format == "fasta"
                    else DownloadAlignedFastaService.generate_enhanced_aligned_fasta_content(
                        result_data, db_path, job.input
                    )
                )
                if isinstance(content, str):
                    content = content.encode("utf-8")

        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Error in download_results: {e}")
        raise_internal_server_error(f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}", response=SuccessResponseSchema)
@wrap_success_response
def get_result(request, id: uuid.UUID, query: Query[ResultQuerySchema]):
    try:
        logger.info("=== GET_RESULT CALLED ===")
        logger.info(f"Job ID: {id}")

        logger.info("Fetching job from database...")
        job = get_object_or_404(HmmerJob, id=id)
        logger.info(f"Found job: {job}")

        task_status, task_result_data, task_block = job_status_and_results(job)
        logger.info(f"Final task_status: {task_status}")
        logger.info(f"Final task_result_data type: {type(task_result_data)}")
        logger.info(
            f"Final task_result_data length: {len(task_result_data) if isinstance(task_result_data, list) else 'N/A'}"
        )

        if task_status != "SUCCESS":
            logger.info(f"Job not successful, returning status: {task_status}")
            response_data = {
                "status": task_status,
                "task": task_block,
                "database": None,
                "id": job.id,
                "algo": job.algo,
                "input": job.input,
                "threshold": job.threshold,
                "threshold_value": job.threshold_value,
                "database_name": job.database,
                "E": job.E,
                "domE": job.domE,
                "T": job.T,
                "domT": job.domT,
                "incE": job.incE,
                "incdomE": job.incdomE,
                "incT": job.incT,
                "incdomT": job.incdomT,
                "popen": job.popen,
                "pextend": job.pextend,
                "mx": job.mx,
            }
            return create_success_response(
                data=response_data, message=f"Job {id} status: {task_status}"
            )

        # Process successful results
        logger.info("Processing successful results...")
        logger.info(f"Task result data: {task_result_data}")

        # Filter results
        filtered_results = []
        for hit in task_result_data:
            if query.with_domains:
                if not hit.get("domains"):
                    continue
            filtered_results.append(hit)

        logger.info(f"Filtered results count: {len(filtered_results)}")

        # Apply pagination only if explicitly requested (not default values)
        # For polling purposes, return all results by default
        page = query.page
        page_size = query.page_size
        default_page_size = 50  # Match the schema default

        # If using default pagination (page=1, page_size=50), return all results for polling
        # Otherwise, apply pagination for explicit pagination requests
        if page == 1 and page_size == default_page_size:
            # Return all results (no pagination) - this is likely a polling request
            paginated_results = filtered_results
            logger.info(
                f"Returning all {len(paginated_results)} results (polling mode)"
            )
        else:
            # Apply explicit pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_results = filtered_results[start_idx:end_idx]
            logger.info(
                f"Pagination: page={page}, page_size={page_size}, returning {len(paginated_results)} results"
            )

        # Get database info
        try:
            database = Database.objects.get(id=job.database)
            database_data = {
                "id": database.id,
                "type": database.type,
                "name": database.name,
                "version": database.version,
                "release_date": database.release_date,
                "order": database.order,
            }
        except Database.DoesNotExist:
            database_data = None

        task_block["result"] = paginated_results
        response_data = {
            "status": task_status,
            "task": task_block,
            "database": database_data,
            "id": job.id,
            "algo": job.algo,
            "input": job.input,
            "threshold": job.threshold,
            "threshold_value": job.threshold_value,
            "database_name": job.database,
            "E": job.E,
            "domE": job.domE,
            "T": job.T,
            "domT": job.domT,
            "incE": job.incE,
            "incdomE": job.incdomE,
            "incT": job.incT,
            "incdomT": job.incdomT,
            "popen": job.popen,
            "pextend": job.pextend,
            "mx": job.mx,
        }

        logger.info("=== GET_RESULT COMPLETED ===")
        return create_success_response(
            data=response_data, message=f"Job {id} results retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Error in get_result: {e}")
        raise_internal_server_error(f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/domains", response=SuccessResponseSchema)
@wrap_success_response
def get_domains_by_target(request, id: uuid.UUID, target: str):
    """Get domain information for a specific target."""
    try:
        job = get_object_or_404(HmmerJob, id=id)
        task_status, result_data, _task = job_status_and_results(job)

        if task_status != "SUCCESS":
            raise_validation_error("Job not completed successfully")

        if not result_data:
            raise_not_found_error(
                message="No results found for this job",
                error_code=ErrorCode.RESULT_NOT_FOUND,
            )

        # Find the target in the results
        target_data = None
        for hit in result_data:
            if hit.get("target") == target:
                target_data = hit
                break

        if not target_data:
            raise_not_found_error(
                message=f"Target '{target}' not found in results",
                error_code=ErrorCode.RESULT_NOT_FOUND,
            )

        # Extract domains
        domains = target_data.get("domains", [])
        logger.info(f"Found {len(domains)} domains for target {target}")

        return create_success_response(
            data={"target": target_data.get("target", ""), "domains": domains},
            message=f"Retrieved {len(domains)} domains for target {target}",
        )

    except Exception as e:
        logger.error(f"Error in get_domains_by_target: {e}")
        raise_internal_server_error(f"Internal server error: {str(e)}")


@pyhmmer_router_result.get(
    "/{uuid:id}/domains/{int:domain_index}",
    response=SuccessResponseSchema,
    include_in_schema=False,
)
@wrap_success_response
def get_domain_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed information for a specific domain."""
    try:
        job = get_object_or_404(HmmerJob, id=id)
        task_status, result_data, _task = job_status_and_results(job)

        if task_status != "SUCCESS":
            raise_validation_error("Job not completed successfully")

        if not result_data or domain_index >= len(result_data):
            raise_not_found_error(
                message="Domain not found",
                error_code=ErrorCode.RESULT_NOT_FOUND,
            )

        target_data = result_data[domain_index]
        domains = target_data.get("domains", [])

        if not domains:
            raise_not_found_error(
                message="No domains found for this target",
                error_code=ErrorCode.RESULT_NOT_FOUND,
            )

        return create_success_response(
            data={"target": target_data.get("target", ""), "domains": domains},
            message=f"Retrieved {len(domains)} domains for target",
        )

    except Exception as e:
        logger.error(f"Error in get_domain_details: {e}")
        raise_internal_server_error(f"Internal server error: {str(e)}")


@pyhmmer_router_result.get(
    "/{uuid:id}/alignment/{int:domain_index}",
    response=SuccessResponseSchema,
    include_in_schema=False,
)
@wrap_success_response
def get_alignment_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed alignment information for a specific domain."""
    try:
        job = get_object_or_404(HmmerJob, id=id)
        task_status, result_data, _task = job_status_and_results(job)

        if task_status != "SUCCESS":
            raise_validation_error("Job not completed successfully")

        if not result_data or domain_index >= len(result_data):
            raise_not_found_error(
                message="Domain not found",
                error_code=ErrorCode.RESULT_NOT_FOUND,
            )

        target_data = result_data[domain_index]
        domains = target_data.get("domains", [])

        if not domains:
            raise_not_found_error(
                message="No domains found for this target",
                error_code=ErrorCode.RESULT_NOT_FOUND,
            )

        # Return the first domain's alignment (you might want to add a domain parameter)
        domain = domains[0]

        return create_success_response(
            data={
                "target": target_data.get("target", ""),
                "domain_index": domain_index,
                "alignment": domain.get("alignment"),
                "simple_alignment": domain.get("alignment_display"),
            },
            message="Alignment details retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Error in get_alignment_details: {e}")
        raise_internal_server_error(f"Internal server error: {str(e)}")
