import gzip
import json
import logging
import uuid

from celery.result import AsyncResult
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from ninja import Router, Query
from ninja.errors import HttpError

from dataportal.utils.response_wrappers import wrap_success_response
from .schemas import (
    JobDetailsResponseSchema,
    ResultQuerySchema,
    DomainDetailsResponseSchema,
    AlignmentDetailsResponseSchema,
)
from .services import DownloadService, FastaService, AlignmentService
from ..search.models import HmmerJob, Database

logger = logging.getLogger(__name__)

pyhmmer_router_result = Router(tags=["PyHMMER Results"])


@pyhmmer_router_result.get("/{uuid:id}/download")
def download_results(request, id: uuid.UUID, format: str):
    """Download search results in various formats (tab, fasta, aligned_fasta)"""
    try:
        logger.info("=== DOWNLOAD REQUEST ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Format: {format}")

        # Validate format
        if format not in ["tab", "fasta", "aligned_fasta"]:
            raise HttpError(
                400,
                f"Invalid format: {format}. Supported formats: tab, fasta, aligned_fasta",
            )

        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data:
            raise HttpError(404, "No results found for this job")

        db_path = settings.HMMER_DATABASES.get(job.database)
        if not db_path:
            raise HttpError(500, f"Database {job.database} not configured")

        if format == "tab":
            content = DownloadService.generate_tsv_content(result_data)
            filename = f"pyhmmer_hits_{id}.tsv"
            content_type = "text/tab-separated-values"
        elif format == "fasta":
            content = FastaService.generate_enhanced_fasta_content(
                result_data, db_path, job.input
            )
            filename = f"pyhmmer_hits_{id}.fasta.gz"
            content_type = "application/gzip"
            logger.info(f"Generated FASTA content type: {type(content)}")
            logger.info(f"Generated FASTA content length: {len(content)}")
        elif format == "aligned_fasta":
            content = AlignmentService.generate_enhanced_aligned_fasta_content(
                result_data, db_path, job.input
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
                    FastaService.generate_enhanced_fasta_content(
                        result_data, db_path, job.input
                    )
                    if format == "fasta"
                    else AlignmentService.generate_enhanced_aligned_fasta_content(
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
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}", response=JobDetailsResponseSchema)
def get_result(request, id: uuid.UUID, query: Query[ResultQuerySchema]):
    try:
        logger.info("=== GET_RESULT CALLED ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Query params: {query}")

        logger.info("Fetching job from database...")
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
                    logger.warning(
                        "Raw result is None, checking AsyncResult for fallback..."
                    )
                    if async_result.result is not None:
                        logger.info("Using AsyncResult result as fallback")
                        task_result_data = async_result.result
                    else:
                        logger.warning(
                            "Both database and AsyncResult have no result, setting empty list"
                        )
                        task_result_data = []
                elif isinstance(raw_result, str):
                    logger.info("Raw result is string, attempting JSON decode...")

                    task_result_data = json.loads(raw_result)
                else:
                    logger.info("Raw result is already a list/dict, using as is")
                    task_result_data = raw_result
            except Exception as e:
                logger.error(f"Error parsing result: {e}")
                task_result_data = []

            logger.info(f"Parsed result data type: {type(task_result_data)}")
            logger.info(
                f"Result list length: {len(task_result_data) if isinstance(task_result_data, list) else 'N/A'}"
            )
        else:
            logger.warning("Job has no task associated")

        logger.info(f"Final task_status: {task_status}")
        logger.info(f"Final task_result_data type: {type(task_result_data)}")
        logger.info(
            f"Final task_result_data length: {len(task_result_data) if isinstance(task_result_data, list) else 'N/A'}"
        )

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
                "bias_filter": job.bias_filter,
                "mx": job.mx,
            }
            return response_data

        # Process successful results
        logger.info("Processing successful results...")
        logger.info(f"Task result data: {task_result_data}")

        # Apply pagination
        page = query.page
        page_size = query.page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        logger.info(f"Pagination: page={page}, page_size={page_size}")
        logger.info(f"Pagination indices: start_idx={start_idx}, end_idx={end_idx}")

        # Apply filters
        filtered_results = []
        for hit in task_result_data:
            # Apply taxonomy filter
            if query.taxonomy_ids:
                # TODO: Implement taxonomy filtering
                pass

            # Apply architecture filter
            if query.architecture:
                # TODO: Implement architecture filtering
                pass

            # Apply domain filter
            if query.with_domains:
                if not hit.get("domains"):
                    continue

            filtered_results.append(hit)

        logger.info(f"Filtered results count: {len(filtered_results)}")

        # Apply pagination to filtered results
        paginated_results = filtered_results[start_idx:end_idx]
        logger.info(f"Paginated results count: {len(paginated_results)}")

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

        response_data = {
            "status": task_status,
            "task": {
                "status": job.task.status if job.task else "PENDING",
                "date_created": job.task.date_created if job.task else None,
                "date_done": job.task.date_done if job.task else None,
                "result": paginated_results,
            },
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
            "bias_filter": job.bias_filter,
            "mx": job.mx,
        }

        logger.info("=== GET_RESULT COMPLETED ===")
        return response_data

    except Exception as e:
        logger.error(f"Error in get_result: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get("/{uuid:id}/domains", response=DomainDetailsResponseSchema)
def get_domains_by_target(request, id: uuid.UUID, target: str):
    """Get domain information for a specific target."""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data:
            raise HttpError(404, "No results found for this job")

        # Find the target in the results
        target_data = None
        for hit in result_data:
            if hit.get("target") == target:
                target_data = hit
                break

        if not target_data:
            raise HttpError(404, f"Target '{target}' not found in results")

        # Extract domains
        domains = target_data.get("domains", [])
        logger.info(f"Found {len(domains)} domains for target {target}")

        return {"target": target_data.get("target", ""), "domains": domains}

    except Exception as e:
        logger.error(f"Error in get_domains_by_target: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get(
    "/{uuid:id}/domains/{int:domain_index}", response=DomainDetailsResponseSchema
)
@wrap_success_response
def get_domain_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed information for a specific domain."""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data or domain_index >= len(result_data):
            raise HttpError(404, "Domain not found")

        target_data = result_data[domain_index]
        domains = target_data.get("domains", [])

        if not domains:
            raise HttpError(404, "No domains found for this target")

        return {"target": target_data.get("target", ""), "domains": domains}

    except Exception as e:
        logger.error(f"Error in get_domain_details: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


@pyhmmer_router_result.get(
    "/{uuid:id}/alignment/{int:domain_index}", response=AlignmentDetailsResponseSchema
)
@wrap_success_response
def get_alignment_details(request, id: uuid.UUID, domain_index: int):
    """Get detailed alignment information for a specific domain."""
    try:
        job = get_object_or_404(HmmerJob, id=id)

        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")

        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []

        if not result_data or domain_index >= len(result_data):
            raise HttpError(404, "Domain not found")

        target_data = result_data[domain_index]
        domains = target_data.get("domains", [])

        if not domains:
            raise HttpError(404, "No domains found for this target")

        # Return the first domain's alignment (you might want to add a domain parameter)
        domain = domains[0]

        return {
            "status": "success",
            "target": target_data.get("target", ""),
            "domain_index": domain_index,
            "alignment": domain.get("alignment"),
            "simple_alignment": domain.get("alignment_display"),
        }

    except Exception as e:
        logger.error(f"Error in get_alignment_details: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")
