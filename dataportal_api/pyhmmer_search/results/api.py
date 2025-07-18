import logging
import uuid
import gzip
import io
import os
import re
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import HttpResponse
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


@pyhmmer_router_result.get("/{uuid:id}/download")
def download_results(request, id: uuid.UUID, format: str):
    """Download search results in various formats (tab, fasta, aligned_fasta)"""
    try:
        logger.info(f"=== DOWNLOAD REQUEST ===")
        logger.info(f"Job ID: {id}")
        logger.info(f"Format: {format}")
        
        # Validate format
        if format not in ['tab', 'fasta', 'aligned_fasta']:
            raise HttpError(400, f"Invalid format: {format}. Supported formats: tab, fasta, aligned_fasta")
        
        # Get job and results
        job = get_object_or_404(HmmerJob, id=id)
        
        if not job.task or job.task.status != "SUCCESS":
            raise HttpError(400, "Job not completed successfully")
        
        # Parse the result
        import json
        if isinstance(job.task.result, str):
            result_data = json.loads(job.task.result)
        else:
            result_data = job.task.result or []
        
        if not result_data:
            raise HttpError(404, "No results found for this job")
        
        # Get database path
        db_path = settings.HMMER_DATABASES.get(job.database)
        if not db_path:
            raise HttpError(500, f"Database {job.database} not configured")
        
        # Generate content based on format
        if format == 'tab':
            content = generate_tsv_content(result_data)
            filename = f"pyhmmer_hits_{id}.tsv"
            content_type = "text/tab-separated-values"
        elif format == 'fasta':
            content = generate_enhanced_fasta_content(result_data, db_path, job.input)
            filename = f"pyhmmer_hits_{id}.fasta.gz"
            content_type = "application/gzip"
        elif format == 'aligned_fasta':
            content = generate_enhanced_aligned_fasta_content(result_data, db_path, job.input)
            filename = f"pyhmmer_hits_{id}.aligned.fasta.gz"
            content_type = "application/gzip"
        
        # Create response
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"Download generated successfully: {filename}")
        return response
        
    except Exception as e:
        logger.error(f"Error in download_results: {e}")
        raise HttpError(500, f"Internal server error: {str(e)}")


def generate_tsv_content(results):
    """Generate TSV content from search results"""
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    
    # Write header
    writer.writerow([
        'Target', 'Description', 'E-value', 'Score', 'Bias',
        'Query_Start', 'Query_End', 'Target_Start', 'Target_End',
        'Query_Length', 'Target_Length', 'Identity_Pct', 'Identity_Count',
        'Similarity_Pct', 'Similarity_Count'
    ])
    
    # Write data rows
    for hit in results:
        target = hit.get('target', '')
        description = hit.get('description', '')
        evalue = hit.get('evalue', '')
        score = hit.get('score', '')
        
        # Get domain information if available
        domains = hit.get('domains', [])
        if domains:
            domain = domains[0]  # Use first domain
            bias = domain.get('bias', '')
            env_from = domain.get('env_from', '')
            env_to = domain.get('env_to', '')
            
            # Get alignment information
            alignment = domain.get('alignment', {})
            if alignment:
                query_start = alignment.get('hmm_from', '')
                query_end = alignment.get('hmm_to', '')
                target_start = alignment.get('target_from', '')
                target_end = alignment.get('target_to', '')
                query_length = alignment.get('hmm_length', '')
                target_length = alignment.get('target_length', '')
            else:
                query_start = query_end = target_start = target_end = query_length = target_length = ''
            
            # Get identity/similarity from alignment_display
            alignment_display = domain.get('alignment_display', {})
            if alignment_display:
                identity = alignment_display.get('identity', [0, 0])
                similarity = alignment_display.get('similarity', [0, 0])
                identity_pct = f"{identity[0]*100:.1f}" if len(identity) > 0 else "0.0"
                identity_count = str(identity[1]) if len(identity) > 1 else "0"
                similarity_pct = f"{similarity[0]*100:.1f}" if len(similarity) > 0 else "0.0"
                similarity_count = str(similarity[1]) if len(similarity) > 1 else "0"
            else:
                identity_pct = identity_count = similarity_pct = similarity_count = "0"
        else:
            bias = env_from = env_to = query_start = query_end = target_start = target_end = query_length = target_length = "0"
            identity_pct = identity_count = similarity_pct = similarity_count = "0"
        
        writer.writerow([
            target, description, evalue, score, bias,
            query_start, query_end, target_start, target_end,
            query_length, target_length, identity_pct, identity_count,
            similarity_pct, similarity_count
        ])
    
    return output.getvalue()


def fetch_sequence_from_database(target_name: str, db_path: str) -> str:
    """Fetch a sequence from the database file using PyHMMER"""
    try:
        from pyhmmer.easel import SequenceFile, SSIReader
        
        # Check if SSI index exists
        ssi_path = f"{db_path}.ssi"
        if os.path.exists(ssi_path):
            # Use SSI for fast lookup
            with SSIReader(ssi_path) as ssi_reader:
                try:
                    entry = ssi_reader.find_name(target_name.encode())
                    with open(db_path, 'rt') as fh:
                        fh.seek(entry.data_offset)
                        return fh.read(entry.record_length)
                except (KeyError, ValueError):
                    logger.warning(f"Target {target_name} not found in SSI index")
        
        # Fallback: scan through the file
        with SequenceFile(db_path, format="fasta") as seqfile:
            for seq in seqfile:
                if seq.name.decode() == target_name:
                    return f">{seq.name.decode()}\n{seq.sequence}\n"
        
        logger.warning(f"Target {target_name} not found in database")
        return ""
        
    except Exception as e:
        logger.error(f"Error fetching sequence for {target_name}: {e}")
        return ""


def fetch_sequences_parallel(target_names: List[str], db_path: str, max_workers: int = 4) -> dict:
    """Fetch multiple sequences in parallel"""
    sequences = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_name = {
            executor.submit(fetch_sequence_from_database, name, db_path): name 
            for name in target_names
        }
        
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                sequence = future.result()
                if sequence:
                    sequences[name] = sequence
            except Exception as e:
                logger.error(f"Error fetching sequence for {name}: {e}")
    
    return sequences


def generate_enhanced_fasta_content(results, db_path: str, query_input: str):
    """Generate enhanced FASTA content with actual sequences from database"""
    output = io.StringIO()
    
    # Extract target names
    target_names = [hit.get('target', '') for hit in results if hit.get('target')]
    
    # Fetch sequences from database
    logger.info(f"Fetching {len(target_names)} sequences from database: {db_path}")
    sequences = fetch_sequences_parallel(target_names, db_path)
    
    for hit in results:
        target = hit.get('target', '')
        description = hit.get('description', '')
        
        if target in sequences:
            # Use the actual sequence from database
            output.write(sequences[target])
        else:
            # Fallback to existing logic
            sequence = None
            
            # Try to get from hit sequence field
            if hit.get('sequence'):
                sequence = hit.get('sequence')
            else:
                # Try to get from domain alignment data
                domains = hit.get('domains', [])
                if domains:
                    domain = domains[0]
                    alignment = domain.get('alignment', {})
                    if alignment and alignment.get('target_sequence'):
                        sequence = alignment.get('target_sequence').replace('-', '')
                    else:
                        alignment_display = domain.get('alignment_display', {})
                        if alignment_display and alignment_display.get('aseq'):
                            sequence = alignment_display.get('aseq').replace('-', '')
            
            # Write FASTA entry
            output.write(f">{target} {description}\n")
            if sequence:
                for i in range(0, len(sequence), 60):
                    output.write(sequence[i:i+60] + "\n")
            else:
                output.write("N/A\n")
    
    # Compress the content
    content = output.getvalue()
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode='wb') as gz:
        gz.write(content.encode('utf-8'))
    
    return compressed.getvalue()


def generate_enhanced_aligned_fasta_content(results, db_path: str, query_input: str):
    """Generate enhanced aligned FASTA content with actual sequences and alignments"""
    output = io.StringIO()
    
    # Parse query sequence
    query_match = re.match(r"^>(.*$)\n([\s\S]+)", query_input, re.MULTILINE)
    if query_match:
        query_header, query_sequence = query_match.groups()
        query_sequence = query_sequence.replace('\n', '').replace('\r', '')
    else:
        query_header = "query"
        query_sequence = ""
    
    # Extract target names
    target_names = [hit.get('target', '') for hit in results if hit.get('target')]
    
    # Fetch sequences from database
    logger.info(f"Fetching {len(target_names)} sequences from database: {db_path}")
    sequences = fetch_sequences_parallel(target_names, db_path)
    
    for hit in results:
        target = hit.get('target', '')
        description = hit.get('description', '')
        
        # Get alignment information
        domains = hit.get('domains', [])
        if domains:
            domain = domains[0]
            alignment = domain.get('alignment', {})
            alignment_display = domain.get('alignment_display', {})
            
            if alignment:
                # Use PyHMMER alignment data
                query_seq = alignment.get('hmm_sequence', '')
                target_seq = alignment.get('target_sequence', '')
                identity_seq = alignment.get('identity_sequence', '')
                
                output.write(f">{target}_query {description}\n")
                if query_seq:
                    for i in range(0, len(query_seq), 60):
                        output.write(query_seq[i:i+60] + "\n")
                else:
                    output.write("N/A\n")
                
                output.write(f">{target}_target {description}\n")
                if target_seq:
                    for i in range(0, len(target_seq), 60):
                        output.write(target_seq[i:i+60] + "\n")
                else:
                    output.write("N/A\n")
                
                if identity_seq:
                    output.write(f">{target}_identity {description}\n")
                    for i in range(0, len(identity_seq), 60):
                        output.write(identity_seq[i:i+60] + "\n")
            elif alignment_display:
                # Use legacy alignment display data
                query_seq = alignment_display.get('model', '')
                target_seq = alignment_display.get('aseq', '')
                match_line = alignment_display.get('mline', '')
                
                output.write(f">{target}_query {description}\n")
                if query_seq:
                    for i in range(0, len(query_seq), 60):
                        output.write(query_seq[i:i+60] + "\n")
                else:
                    output.write("N/A\n")
                
                output.write(f">{target}_target {description}\n")
                if target_seq:
                    for i in range(0, len(target_seq), 60):
                        output.write(target_seq[i:i+60] + "\n")
                else:
                    output.write("N/A\n")
                
                if match_line:
                    output.write(f">{target}_match {description}\n")
                    for i in range(0, len(match_line), 60):
                        output.write(match_line[i:i+60] + "\n")
            else:
                # No alignment data - try to get full sequence from database
                if target in sequences:
                    output.write(f">{target}_full {description}\n")
                    output.write(sequences[target])
                else:
                    output.write(f">{target} {description} (no alignment data)\n")
                    output.write("N/A\n")
        else:
            # No domains - try to get full sequence from database
            if target in sequences:
                output.write(f">{target}_full {description}\n")
                output.write(sequences[target])
            else:
                output.write(f">{target} {description} (no domain data)\n")
                output.write("N/A\n")
    
    # Compress the content
    content = output.getvalue()
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode='wb') as gz:
        gz.write(content.encode('utf-8'))
    
    return compressed.getvalue()


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
        
        # Return the data directly - the frontend will treat this as a legacy response
        return {
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
