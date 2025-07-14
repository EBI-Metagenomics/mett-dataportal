import json
import logging
from typing import Optional

from Bio import pairwise2
from celery import shared_task
from django.utils import timezone
from django_celery_results.models import TaskResult
from pyhmmer.easel import DigitalSequenceBlock
from pyhmmer.easel import TextSequence, Alphabet, SequenceFile
from pyhmmer.plan7 import Pipeline, Background, Builder
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
import re

from dataportal import settings
from .models import HmmerJob
from .schemas import PyhmmerAlignmentSchema, LegacyAlignmentDisplay, DomainSchema, HitSchema

logger = logging.getLogger(__name__)


def _log_query_sequences(raw_bytes):
    try:
        # For pyhmmer 0.11+, TextSequence.sequence is str
        lines = raw_bytes.decode().strip().splitlines()
        name = lines[0].lstrip(">").encode()
        sequence = "".join(lines[1:])
        text_seq = TextSequence(name=name, sequence=sequence)
        logger.error(
            f"Seq: name={text_seq.name}, type={type(text_seq.sequence)}, first100={text_seq.sequence[:100]}"
        )
    except Exception as e:
        logger.error(f"Error logging query sequences: {e}")


def extract_pyhmmer_alignment(alignment) -> Optional[PyhmmerAlignmentSchema]:
    """Extract alignment data from pyhmmer.plan7.Alignment object"""
    try:
        if alignment is None:
            return None
            
        return PyhmmerAlignmentSchema(
            hmm_name=alignment.hmm_name.decode() if hasattr(alignment.hmm_name, 'decode') else str(alignment.hmm_name),
            hmm_accession=alignment.hmm_accession.decode() if alignment.hmm_accession and hasattr(
                alignment.hmm_accession, 'decode') else str(
                alignment.hmm_accession) if alignment.hmm_accession else None,
            hmm_from=alignment.hmm_from,
            hmm_to=alignment.hmm_to,
            hmm_length=getattr(alignment, 'hmm_length', None),
            hmm_sequence=alignment.hmm_sequence,
            
            target_name=alignment.target_name.decode() if hasattr(alignment.target_name, 'decode') else str(
                alignment.target_name),
            target_from=alignment.target_from,
            target_to=alignment.target_to,
            target_length=getattr(alignment, 'target_length', None),
            target_sequence=alignment.target_sequence,
            
            identity_sequence=alignment.identity_sequence,
            posterior_probabilities=getattr(alignment, 'posterior_probabilities', None),
        )
    except Exception as e:
        logger.warning(f"Failed to extract pyhmmer alignment: {e}")
        return None


def create_legacy_alignment_display(alignment) -> Optional[LegacyAlignmentDisplay]:
    """Create legacy alignment display from pyhmmer alignment for backward compatibility"""
    try:
        if alignment is None:
            return None
            
        # Calculate identity
        matches = sum(1 for a, b in zip(alignment.hmm_sequence, alignment.target_sequence) 
                     if a == b and a != '-')
        min_len = min(len(alignment.hmm_sequence), len(alignment.target_sequence))
        identity_pct = matches / min_len if min_len > 0 else 0
        
        # Create match line
        mline = ''.join('|' if a == b and a != '-' else ' ' 
                       for a, b in zip(alignment.hmm_sequence, alignment.target_sequence))
        
        return LegacyAlignmentDisplay(
            hmmfrom=alignment.hmm_from,
            hmmto=alignment.hmm_to,
            sqfrom=alignment.target_from,
            sqto=alignment.target_to,
            model=alignment.hmm_sequence,
            aseq=alignment.target_sequence,
            mline=mline,
            ppline=getattr(alignment, 'posterior_probabilities', None),
            identity=(identity_pct, matches),
            similarity=(identity_pct, matches),
        )
    except Exception as e:
        logger.warning(f"Failed to create legacy alignment display: {e}")
        return None


@shared_task(bind=True, queue="pyhmmer_queue", routing_key="pyhmmer.search")
def run_search(self, job_id: str):
    task_id = self.request.id
    logger.info(f"=== STARTING HMMER SEARCH ===")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Celery task ID: {self.request.id}")
    
    try:
        logger.info(f"Fetching job from database...")
        job = HmmerJob.objects.select_related("task").get(id=job_id)
        logger.info(f"Found job: {job}")
        logger.info(f"Job task: {job.task}")
        logger.info(f"Job task ID: {job.task.task_id if job.task else 'None'}")
        logger.info(f"Job input length: {len(job.input) if job.input else 0}")
        logger.info(f"Job database: {job.database}")
        logger.info(f"Job threshold: {job.threshold}")
        logger.info(f"Job threshold_value: {job.threshold_value}")

        logger.info(f"Updating task state to STARTED...")
        self.update_state(state="STARTED")
        if job.task:
            logger.info(f"Updating database task status to STARTED...")
            job.task.status = "STARTED"
            job.task.save()
            logger.info(f"Database task status updated successfully")

        logger.info(f"Getting database path for: {job.database}")
        db_path = settings.HMMER_DATABASES[job.database]
        logger.info(f"Database path: {db_path}")
        if not db_path:
            raise ValueError(f"Invalid database ID '{job.database}'")

        # Prepare alphabet and background
        logger.info(f"Setting up alphabet and background...")
        alphabet = Alphabet.amino()
        background = Background(alphabet)
        
        # Configure pipeline with threshold parameters
        pipeline_kwargs = {
            'E': job.E, 'domE': job.domE, 'incE': job.incE, 'incdomE': job.incdomE,
            'T': job.T, 'domT': job.domT, 'incT': job.incT, 'incdomT': job.incdomT,
        }
        logger.info(f"Pipeline kwargs: {pipeline_kwargs}")
        # Filter out None values before passing to Pipeline
        filtered_kwargs = {k: v for k, v in pipeline_kwargs.items() if v is not None}
        logger.info(f"Filtered pipeline kwargs: {filtered_kwargs}")
        pipeline = Pipeline(alphabet, **filtered_kwargs)
        logger.info(f"Pipeline configured successfully")

        # Parse query
        logger.info(f"Parsing query input...")
        lines = job.input.strip().splitlines()
        logger.info(f"Input lines count: {len(lines)}")
        if not lines or not lines[0].startswith(">") or len(lines) < 2:
            raise ValueError("Invalid FASTA input format for query.")

        name = lines[0].lstrip(">").encode("utf-8")
        sequence = "".join(lines[1:])
        logger.info(f"Query name: {name}")
        logger.info(f"Query sequence length: {len(sequence)}")
        logger.info(f"Query sequence preview: {sequence[:100]}...")
        
        text_seq = TextSequence(name=name, sequence=sequence)
        digital_seq = text_seq.digitize(alphabet)
        logger.info(f"Query digitized successfully")

        # Read target sequences
        logger.info(f"Reading target sequences from: {db_path}")
        with SequenceFile(db_path, format="fasta") as target_file:
            digital_targets = [seq.digitize(alphabet) for seq in target_file]
        logger.info(f"Digitized {len(digital_targets)} target sequences from {db_path}")

        # Also build a mapping from name to TextSequence for alignment
        logger.info(f"Building target sequence mapping...")
        target_sequences = {}
        with SequenceFile(db_path, format="fasta") as target_file:
            for seq in target_file:
                target_sequences[seq.name.decode()] = seq
        logger.info(f"Target sequence mapping built with {len(target_sequences)} entries")

        # Create a Builder and configure it with gap penalties and score matrix
        logger.info(f"Configuring builder...")
        builder_kwargs = {}
        if job.popen is not None:
            builder_kwargs['popen'] = job.popen
        if job.pextend is not None:
            builder_kwargs['pextend'] = job.pextend
        if job.mx:
            builder_kwargs['score_matrix'] = job.mx
            
        builder = Builder(alphabet, **builder_kwargs)
        logger.info(f"Builder configured with parameters: {builder_kwargs}")

        # Run search using the builder
        logger.info(f"Starting HMMER search...")
        results = []
        block = DigitalSequenceBlock(alphabet)
        block.extend(digital_targets)
        logger.info(f"Digital sequence block created with {len(digital_targets)} targets")

        hits = pipeline.search_seq(digital_seq, block, builder=builder)
        logger.info(f"Search completed, processing hits...")

        try:
            hit_list = list(hits)
            logger.info(f"Total hits found: {len(hit_list)}")
            logger.info(f"Top 5 hit names: {[hit.name.decode() for hit in hit_list[:5]]}")
        except Exception as e:
            logger.error(f"Could not log top hits due to error: {e}")

        logger.info(f"Processing individual hits...")
        for i, hit in enumerate(hit_list):
            logger.info(f"Processing hit {i+1}/{len(hit_list)}: {hit.name.decode()}")
            logger.info(f"Hit evalue: {hit.evalue}, score: {hit.score}")
            
            domains = []
            if hasattr(hit, "domains") and hit.domains:
                logger.info(f"Hit has {len(hit.domains)} domains")
                for domain in hit.domains:
                    # Extract alignment from pyhmmer.plan7.Alignment
                    alignment = getattr(domain, "alignment", None)
                    
                    # Extract both new and legacy alignment formats
                    pyhmmer_alignment = extract_pyhmmer_alignment(alignment)
                    legacy_alignment = create_legacy_alignment_display(alignment)
                    
                    domain_obj = DomainSchema(
                        env_from=domain.env_from,
                        env_to=domain.env_to,
                        bitscore=domain.score,
                        ievalue=domain.i_evalue,
                        cevalue=getattr(domain, "c_evalue", None),
                        bias=getattr(domain, "bias", None),
                        strand=getattr(domain, "strand", None),
                        alignment=pyhmmer_alignment,
                        alignment_display=legacy_alignment,
                    )
                    domains.append(domain_obj)
            else:
                logger.info(f"Hit has no domains (phmmer case)")
                # For hits without domains (phmmer case), create alignment with Biopython
                target_seq = target_sequences.get(hit.name.decode())
                pyhmmer_alignment = None
                legacy_alignment = None
                
                if target_seq is not None:
                    try:
                        query_seq_str = str(sequence)
                        target_seq_str = str(target_seq.sequence)
                        logger.info(f"Creating Biopython alignment for {hit.name.decode()}")
                        alignments = pairwise2.align.globalxx(query_seq_str, target_seq_str)
                        if alignments:
                            aln = alignments[0]
                            aligned_query, aligned_target, score, begin, end = aln
                            pyhmmer_alignment = PyhmmerAlignmentSchema(
                                hmm_name=name.decode(),
                                hmm_accession=None,
                                hmm_from=1,
                                hmm_to=len(query_seq_str),
                                hmm_length=len(query_seq_str),
                                hmm_sequence=aligned_query,
                                target_name=hit.name.decode(),
                                target_from=1,
                                target_to=len(target_seq_str),
                                target_length=len(target_seq_str),
                                target_sequence=aligned_target,
                                identity_sequence=''.join('|' if a == b else ' ' for a, b in zip(aligned_query, aligned_target)),
                                posterior_probabilities=None
                            )
                        legacy_alignment = parse_biopython_alignment(query_seq_str, target_seq_str)

                    except Exception as e:
                        logger.warning(f"Biopython alignment failed for {hit.name.decode()}: {e}")

                domain_obj = DomainSchema(
                    env_from=getattr(hit, "envelope_from", None),
                    env_to=getattr(hit, "envelope_to", None),
                    bitscore=hit.score,
                    ievalue=hit.evalue,
                    cevalue=getattr(hit, "c_evalue", None),
                    bias=getattr(hit, "bias", None),
                    strand=None,
                    alignment=pyhmmer_alignment,
                    alignment_display=legacy_alignment,
                )
                domains.append(domain_obj)
                
            first_domain_seq = None
            if domains and domains[0].alignment and domains[0].alignment.target_sequence:
                first_domain_seq = domains[0].alignment.target_sequence.replace('-', '')

            # Truncate bracketed content from description
            desc = hit.description.decode() if hit.description else ""
            desc = re.sub(r"\s*\[.*\]$", "", desc)
            hit_obj = HitSchema(
                target=hit.name.decode(),
                description=desc,
                evalue=f"{hit.evalue:.2e}",
                score=f"{hit.score:.2f}",
                sequence=first_domain_seq,
                num_hits=len(hit_list) or None,
                num_significant=sum(1 for h in hit_list if h.evalue < 0.01),
                domains=domains
            )
            
            logger.info(f"Checking if hit passes filter...")
            logger.info(f"Job threshold: {job.threshold}, threshold_value: {job.threshold_value}")
            logger.info(f"Hit evalue: {hit.evalue}, score: {hit.score}")
            
            if (
                job.threshold == HmmerJob.ThresholdChoices.EVALUE
                and hit.evalue < job.threshold_value
            ):
                logger.info(f"Hit passes EVALUE filter")
                results.append(hit_obj)
            elif (
                job.threshold == HmmerJob.ThresholdChoices.BITSCORE
                and hit.score > job.threshold_value
            ):
                logger.info(f"Hit passes BITSCORE filter")
                results.append(hit_obj)
            else:
                logger.info(f"Hit does not pass filter")

        logger.info(f"=== SEARCH COMPLETED ===")
        logger.info(f"Total hits processed: {len(hit_list)}")
        logger.info(f"Hits passing filter: {len(results)}")

        logger.info(f"Saving results to database...")
        if job.task:
            logger.info(f"Updating task status to SUCCESS...")
            job.task.status = "SUCCESS"
            
            logger.info(f"Converting results to JSON...")
            result_dicts = [h.model_dump() for h in results]
            logger.info(f"Result dicts created: {len(result_dicts)}")
            logger.info(f"First result dict: {result_dicts[0] if result_dicts else 'None'}")
            
            result_json = json.dumps(result_dicts)
            logger.info(f"Result JSON created, length: {len(result_json)}")
            logger.info(f"Result JSON preview: {result_json[:500]}...")
            
            job.task.result = result_json
            job.task.date_done = timezone.now()
            
            logger.info(f"Saving task to database...")
            logger.info(f"Task ID before save: {job.task.task_id}")
            logger.info(f"Task status before save: {job.task.status}")
            logger.info(f"Task result length before save: {len(job.task.result) if job.task.result else 0}")
            
            try:
                from django.db import transaction
                with transaction.atomic():
                    job.task.save()
                    logger.info(f"Task saved successfully within transaction")
                    
                    # Verify the save worked by refetching
                    job.task.refresh_from_db()
                    logger.info(f"Task status after save: {job.task.status}")
                    logger.info(f"Task result after save: {job.task.result is not None}")
                    logger.info(f"Task result length after save: {len(job.task.result) if job.task.result else 0}")
                    
            except Exception as save_error:
                logger.error(f"Error saving task to database: {save_error}")
                logger.error(f"Save error details: {str(save_error)}", exc_info=True)
                raise
            
            logger.info(f"Updated database record for task {task_id} to SUCCESS")
            logger.info(f"Saved result JSON length: {len(result_json)}")
            logger.info(f"Saved result JSON preview: {result_json[:200]}...")
        else:
            logger.error(f"No task found for job {job_id}")

        logger.info(f"=== TASK COMPLETED SUCCESSFULLY ===")
        return result_dicts

    except Exception as e:
        logger.error(f"=== TASK FAILED ===")
        logger.error(f"Error in run_search for job {job_id}: {str(e)}", exc_info=True)
        if "job" in locals() and job.task:
            logger.info(f"Updating task status to FAILURE...")
            job.task.status = "FAILURE"
            job.task.result = str(e)
            job.task.date_done = timezone.now()
            job.task.save()
            logger.info(f"Updated database record for task {task_id} to FAILURE")
        raise


@shared_task(bind=True, queue="pyhmmer_queue", routing_key="pyhmmer.search")
def test_task(self):
    task_id = self.request.id
    logger.info(f">>> Starting test task with ID: {task_id}")

    try:
        # Update task state using Celery's state management
        self.update_state(state="STARTED")
        logger.info(f"Updated task {task_id} state to STARTED")

        # Update database record
        task_result = TaskResult.objects.get(task_id=task_id)
        task_result.status = "STARTED"
        task_result.save()
        logger.info(f"Updated database record for task {task_id} to STARTED")

        # Simulate some work
        logger.info(">>> Hello from test_task")

        # Check if any jobs are linked to this task
        linked_jobs = HmmerJob.objects.filter(task__task_id=task_id)
        logger.info(f"Found {linked_jobs.count()} jobs linked to task {task_id}")
        for job in linked_jobs:
            logger.info(
                f"Linked job: {job.id}, Status: {job.task.status if job.task else 'No task'}"
            )

        # Update database record with success
        task_result.status = "SUCCESS"
        task_result.result = "OK"
        task_result.date_done = timezone.now()
        task_result.save()
        logger.info(f"Updated database record for task {task_id} to SUCCESS")

    except Exception as e:
        logger.error(f"Error in test_task: {str(e)}", exc_info=True)
        # Update database record with failure
        if "task_result" in locals():
            task_result.status = "FAILURE"
            task_result.result = str(e)
            task_result.date_done = timezone.now()
            task_result.save()
            logger.info(f"Updated database record for task {task_id} to FAILURE")
        raise

    logger.info(f">>> Completed test task {task_id}")
    return "OK"


def parse_biopython_alignment(query: str, target: str) -> Optional[LegacyAlignmentDisplay]:
    """Create legacy alignment display using Biopython for phmmer cases"""
    try:
        alignments = pairwise2.align.globalxx(query, target)
        if not alignments:
            return None
        aln = alignments[0]
        aligned_query, aligned_target, score, begin, end = aln
        mline = ''.join('|' if a == b and a != '-' else ' ' for a, b in zip(aligned_query, aligned_target))
        
        def first_non_gap(seq):
            for i, c in enumerate(seq):
                if c != '-':
                    return i
            return 0
            
        def last_non_gap(seq):
            for i in range(len(seq) - 1, -1, -1):
                if seq[i] != '-':
                    return i
            return len(seq) - 1
            
        hmmfrom = first_non_gap(aligned_query) + 1
        hmmto = last_non_gap(aligned_query) + 1
        sqfrom = first_non_gap(aligned_target) + 1
        sqto = last_non_gap(aligned_target) + 1
        matches = sum(1 for a, b in zip(aligned_query, aligned_target) if a == b and a != '-')
        min_len = min(len(query), len(target))
        identity_pct = matches / min_len if min_len else 0
        
        return LegacyAlignmentDisplay(
            hmmfrom=hmmfrom,
            hmmto=hmmto,
            sqfrom=sqfrom,
            sqto=sqto,
            model=aligned_query,
            aseq=aligned_target,
            mline=mline,
            ppline=None,
            identity=(identity_pct, matches),
            similarity=(identity_pct, matches),
        )
    except Exception as e:
        logger.warning(f"Biopython alignment parsing failed: {e}")
        return None


@shared_task
def cleanup_old_tasks():
    from django_celery_results.models import TaskResult
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = TaskResult.objects.filter(date_done__lt=cutoff).delete()
    return f"Deleted {deleted} old task results"
