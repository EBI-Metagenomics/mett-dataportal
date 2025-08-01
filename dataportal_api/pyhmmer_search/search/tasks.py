import json
import logging
import re
import time
import uuid
from datetime import timedelta
from typing import Optional

from Bio import pairwise2
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django_celery_results.models import TaskResult
from pyhmmer.easel import DigitalSequenceBlock
from pyhmmer.easel import TextSequence, Alphabet, SequenceFile
from pyhmmer.plan7 import Pipeline, Background, Builder

from dataportal import settings
from .models import HmmerJob
from .schemas import (
    PyhmmerAlignmentSchema,
    AlignmentDisplay,
    DomainSchema,
    HitSchema,
)
from .utils import AlignmentCalculator

logger = logging.getLogger(__name__)

MAX_RESULT_SIZE = 50 * 1024 * 1024  # 50MB limit


def _log_query_sequences(raw_bytes):
    try:
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
    try:
        if alignment is None:
            return None

        return PyhmmerAlignmentSchema(
            hmm_name=(
                alignment.hmm_name.decode()
                if hasattr(alignment.hmm_name, "decode")
                else str(alignment.hmm_name)
            ),
            hmm_accession=(
                alignment.hmm_accession.decode()
                if alignment.hmm_accession
                and hasattr(alignment.hmm_accession, "decode")
                else str(alignment.hmm_accession) if alignment.hmm_accession else None
            ),
            hmm_from=alignment.hmm_from,
            hmm_to=alignment.hmm_to,
            hmm_length=getattr(alignment, "hmm_length", None),
            hmm_sequence=alignment.hmm_sequence,
            target_name=(
                alignment.target_name.decode()
                if hasattr(alignment.target_name, "decode")
                else str(alignment.target_name)
            ),
            target_from=alignment.target_from,
            target_to=alignment.target_to,
            target_length=getattr(alignment, "target_length", None),
            target_sequence=alignment.target_sequence,
            identity_sequence=alignment.identity_sequence,
            posterior_probabilities=getattr(alignment, "posterior_probabilities", None),
        )
    except Exception as e:
        logger.warning(f"Failed to extract pyhmmer alignment: {e}")
        return None


def create_simple_alignment_display(alignment) -> Optional[AlignmentDisplay]:
    try:
        if alignment is None:
            return None

        # Create our own match line from the sequences
        mline = AlignmentCalculator.create_match_line(
            alignment.hmm_sequence, alignment.target_sequence
        )
        logger.info(f"Created match line: '{mline}' (length: {len(mline)})")
        logger.info(
            f"HMM sequence: '{alignment.hmm_sequence}' (length: {len(alignment.hmm_sequence)})"
        )
        logger.info(
            f"Target sequence: '{alignment.target_sequence}' (length: {len(alignment.target_sequence)})"
        )

        # Calculate identity and similarity using our match line
        (identity_pct, number_of_identical), (
            similarity_pct,
            number_of_identical_and_similar,
        ) = AlignmentCalculator.calculate_identity_and_similarity_from_match_line(
            alignment.hmm_sequence, mline, alignment.target_sequence
        )

        return AlignmentDisplay(
            hmmfrom=alignment.hmm_from,
            hmmto=alignment.hmm_to,
            sqfrom=alignment.target_from,
            sqto=alignment.target_to,
            model=alignment.hmm_sequence,
            aseq=alignment.target_sequence,
            mline=mline,
            ppline=getattr(alignment, "posterior_probabilities", None),
            identity=(identity_pct, number_of_identical),
            similarity=(similarity_pct, number_of_identical_and_similar),
        )
    except Exception as e:
        logger.warning(f"Failed to create simple alignment display: {e}")
        return None


@shared_task(bind=True, queue="pyhmmer_queue", routing_key="pyhmmer.search")
def run_search(self, job_id: str):
    task_id = self.request.id
    logger.info("=== STARTING HMMER SEARCH ===")
    logger.info(f"Job ID: {job_id}")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"Celery task ID: {self.request.id}")

    try:

        job_uuid = uuid.UUID(job_id)
        logger.info(f"Job ID validated as UUID: {job_uuid}")
    except ValueError as e:
        logger.error(f"Invalid job ID format: {job_id}")
        logger.error(f"UUID validation error: {e}")
        raise ValueError(f"Invalid job ID format: {job_id}")

    try:
        logger.info("Fetching job from database...")
        logger.info(f"Looking for job with ID: {job_id}")
        logger.info(f"Job ID type: {type(job_id)}")

        logger.info(f"HmmerJob model app_label: {HmmerJob._meta.app_label}")
        logger.info(f"HmmerJob model db_table: {HmmerJob._meta.db_table}")
        logger.info(f"HmmerJob model pk field: {HmmerJob._meta.pk.name}")

        try:
            total_jobs = HmmerJob.objects.count()
            logger.info(f"Total jobs in database: {total_jobs}")

            max_retries = 5
            retry_delay = 0.5  # seconds

            for attempt in range(max_retries):
                try:
                    job = HmmerJob.objects.select_related("task").get(id=job_id)
                    logger.info(f"Found job on attempt {attempt + 1}: {job}")
                    break
                except HmmerJob.DoesNotExist:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Job not found on attempt {attempt + 1}, retrying in {retry_delay} seconds..."
                        )

                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Gradual backoff
                    else:
                        logger.error(
                            f"Job with ID {job_id} does not exist in database after {max_retries} attempts"
                        )
                        logger.error("Available jobs in database:")
                        try:
                            all_jobs = HmmerJob.objects.all()[:10]
                            for j in all_jobs:
                                logger.error(f"  - Job ID: {j.id}, Created: {j.pk}")
                        except Exception as e:
                            logger.error(f"Could not list jobs: {e}")
                        raise

            logger.info(f"Job task: {job.task}")
            logger.info(f"Job task ID: {job.task.task_id if job.task else 'None'}")
        except Exception as e:
            logger.error(f"Unexpected error fetching job {job_id}: {e}")
            raise

        logger.info("Updating task state to STARTED...")
        self.update_state(state="STARTED")
        if job.task:
            logger.info("Updating database task status to STARTED...")
            job.task.status = "STARTED"
            job.task.save()
            logger.info("Database task status updated successfully")

        logger.info(f"Getting database path for: {job.database}")
        db_path = settings.HMMER_DATABASES[job.database]
        logger.info(f"Database path: {db_path}")
        if not db_path:
            raise ValueError(f"Invalid database ID '{job.database}'")

        alphabet = Alphabet.amino()
        background = Background(alphabet)

        # Configure pipeline with threshold parameters
        pipeline_kwargs = {
            "E": job.E,
            "domE": job.domE,
            "incE": job.incE,
            "incdomE": job.incdomE,
            "T": job.T,
            "domT": job.domT,
            "incT": job.incT,
            "incdomT": job.incdomT,
        }
        logger.info(f"Pipeline kwargs: {pipeline_kwargs}")
        filtered_kwargs = {k: v for k, v in pipeline_kwargs.items() if v is not None}
        logger.info(f"Filtered pipeline kwargs: {filtered_kwargs}")
        logger.info("=== PIPELINE CONFIGURATION DETAILS ===")
        logger.info(
            f"Pipeline kwargs after filtering (None values removed): {filtered_kwargs}"
        )
        pipeline = Pipeline(alphabet, **filtered_kwargs)

        if hasattr(job, "bias_filter") and job.bias_filter == "off":
            logger.info("Disabling bias composition filter")
            pipeline.bias_filter = False
        else:
            logger.info("Using default bias composition filter (enabled)")

        logger.info("Pipeline configured successfully")

        # Parse query
        logger.info("Parsing query input...")
        lines = job.input.strip().splitlines()
        logger.info(f"Input lines count: {len(lines)}")
        if not lines or not lines[0].startswith(">") or len(lines) < 2:
            raise ValueError("Invalid FASTA input format for query.")

        name = lines[0].lstrip(">").encode("utf-8")
        sequence = "".join(lines[1:])
        logger.info(f"Query name: {name}")

        text_seq = TextSequence(name=name, sequence=sequence)
        digital_seq = text_seq.digitize(alphabet)
        logger.info("Query digitized successfully")

        # Read target sequences
        logger.info(f"Reading target sequences from: {db_path}")
        with SequenceFile(db_path, format="fasta") as target_file:
            digital_targets = [seq.digitize(alphabet) for seq in target_file]
        logger.info(f"Digitized {len(digital_targets)} target sequences from {db_path}")

        # Also build a mapping from name to TextSequence for alignment
        logger.info("Building target sequence mapping...")
        target_sequences = {}
        with SequenceFile(db_path, format="fasta") as target_file:
            for seq in target_file:
                target_sequences[seq.name.decode()] = seq
        logger.info(
            f"Target sequence mapping built with {len(target_sequences)} entries"
        )

        logger.info("Configuring builder...")
        builder_kwargs = {}
        if job.popen is not None:
            builder_kwargs["popen"] = job.popen
        if job.pextend is not None:
            builder_kwargs["pextend"] = job.pextend

        # TODO - Log matrix request but still resolve - PyHMMER uses internal scoring
        if job.mx:
            logger.info(
                f"Scoring matrix requested: {job.mx}, but PyHMMER uses internal scoring system"
            )
            logger.info("Using PyHMMER's default scoring matrix")

        logger.info("=== BUILDER CONFIGURATION DETAILS ===")
        logger.info(f"Builder kwargs: {builder_kwargs}")
        logger.info(
            f"Gap open penalty (popen): {job.popen} -> {'included' if job.popen is not None else 'excluded'}"
        )
        logger.info(
            f"Gap extend penalty (pextend): {job.pextend} -> {'included' if job.pextend is not None else 'excluded'}"
        )
        logger.info(f"Substitution matrix (mx): {job.mx} -> ignored (PyHMMER internal)")
        logger.info(f"Number of parameters passed to Builder: {len(builder_kwargs)}")

        builder = Builder(alphabet, **builder_kwargs)
        logger.info(f"Builder configured with parameters: {builder_kwargs}")

        # Run search using the builder
        logger.info("Starting HMMER search...")
        results = []
        block = DigitalSequenceBlock(alphabet)
        block.extend(digital_targets)
        logger.info(
            f"Digital sequence block created with {len(digital_targets)} targets"
        )

        hits = pipeline.search_seq(digital_seq, block, builder=builder)
        logger.info("Search completed, processing hits...")

        try:
            hit_list = list(hits)
            logger.info(f"Total hits found: {len(hit_list)}")
            logger.info(
                f"Top 5 hit names: {[hit.name.decode() for hit in hit_list[:5]]}"
            )
        except Exception as e:
            logger.error(f"Could not log top hits due to error: {e}")

        logger.info("Processing individual hits...")
        for i, hit in enumerate(hit_list):
            logger.info(f"Processing hit {i + 1}/{len(hit_list)}: {hit.name.decode()}")
            logger.info(f"Hit evalue: {hit.evalue}, score: {hit.score}")

            domains = []
            if hasattr(hit, "domains") and hit.domains:
                logger.info(f"Hit has {len(hit.domains)} domains")
                for domain in hit.domains:
                    # Extract alignment from pyhmmer.plan7.Alignment
                    alignment = getattr(domain, "alignment", None)

                    # Extract both detailed and simple alignment formats
                    pyhmmer_alignment = extract_pyhmmer_alignment(alignment)
                    simple_alignment = create_simple_alignment_display(alignment)

                    domain_obj = DomainSchema(
                        env_from=domain.env_from,
                        env_to=domain.env_to,
                        bitscore=domain.score,
                        ievalue=domain.i_evalue,
                        cevalue=getattr(domain, "c_evalue", None),
                        bias=getattr(domain, "bias", None),
                        strand=getattr(domain, "strand", None),
                        alignment=pyhmmer_alignment,
                        alignment_display=simple_alignment,
                    )
                    domains.append(domain_obj)
            else:
                logger.info("Hit has no domains (phmmer case)")
                # For hits without domains (phmmer case), create alignment with Biopython
                target_seq = target_sequences.get(hit.name.decode())
                pyhmmer_alignment = None
                simple_alignment = None

                if target_seq is not None:
                    try:
                        query_seq_str = str(sequence)
                        target_seq_str = str(target_seq.sequence)
                        logger.info(
                            f"Creating Biopython alignment for {hit.name.decode()}"
                        )
                        alignments = pairwise2.align.globalxx(
                            query_seq_str, target_seq_str
                        )
                        if alignments:
                            aln = alignments[0]
                            aligned_query, aligned_target, score, begin, end = aln

                            identity_sequence = AlignmentCalculator.create_match_line(
                                aligned_query, aligned_target
                            )

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
                                identity_sequence=identity_sequence,
                                posterior_probabilities=None,
                            )
                        simple_alignment = parse_biopython_alignment(
                            query_seq_str, target_seq_str
                        )

                    except Exception as e:
                        logger.warning(
                            f"Biopython alignment failed for {hit.name.decode()}: {e}"
                        )

                domain_obj = DomainSchema(
                    env_from=getattr(hit, "envelope_from", None),
                    env_to=getattr(hit, "envelope_to", None),
                    bitscore=hit.score,
                    ievalue=hit.evalue,
                    cevalue=getattr(hit, "c_evalue", None),
                    bias=getattr(hit, "bias", None),
                    strand=None,
                    alignment=pyhmmer_alignment,
                    alignment_display=simple_alignment,
                )
                domains.append(domain_obj)

            first_domain_seq = None
            if (
                domains
                and domains[0].alignment
                and domains[0].alignment.target_sequence
            ):
                first_domain_seq = domains[0].alignment.target_sequence.replace("-", "")

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
                domains=domains,
            )

            logger.info("Checking if hit passes filter...")
            logger.info(
                f"Job threshold: {job.threshold}, threshold_value: {job.threshold_value}"
            )
            logger.info(f"Hit evalue: {hit.evalue}, score: {hit.score}")

            if (
                job.threshold == HmmerJob.ThresholdChoices.EVALUE
                and hit.evalue < job.threshold_value
            ):
                logger.info(
                    f"Hit passes EVALUE filter: {hit.evalue} < {job.threshold_value}"
                )
                results.append(hit_obj)
            elif (
                job.threshold == HmmerJob.ThresholdChoices.BITSCORE
                and hit.score > job.threshold_value
            ):
                logger.info(
                    f"Hit passes BITSCORE filter: {hit.score} > {job.threshold_value}"
                )
                results.append(hit_obj)
            else:
                if job.threshold == HmmerJob.ThresholdChoices.EVALUE:
                    logger.info(
                        f"Hit does not pass EVALUE filter: {hit.evalue} >= {job.threshold_value}"
                    )
                else:
                    logger.info(
                        f"Hit does not pass BITSCORE filter: {hit.score} <= {job.threshold_value}"
                    )

        logger.info("=== SEARCH COMPLETED ===")
        logger.info(f"Total hits processed: {len(hit_list)}")
        logger.info(f"Hits passing filter: {len(results)}")

        # Convert results to dicts for return
        result_dicts = [h.model_dump() for h in results]
        logger.info(f"Result dicts created: {len(result_dicts)}")
        logger.info(f"First result dict: {result_dicts[0] if result_dicts else 'None'}")

        logger.info("Saving results to database...")
        if job.task:
            logger.info("Updating task status to SUCCESS...")
            job.task.status = "SUCCESS"

            logger.info("Converting results to JSON...")
            result_json = json.dumps(result_dicts)

            if len(result_json) > MAX_RESULT_SIZE:
                # Truncate the result to prevent database issues
                truncated_results = result_dicts[:10]
                result_json = json.dumps(truncated_results)
                logger.warning(
                    f"Truncated to {len(truncated_results)} results, new size: {len(result_json)} bytes"
                )

            job.task.result = result_json
            job.task.date_done = timezone.now()

            logger.info("Saving task to database...")
            logger.info(f"Task ID before save: {job.task.task_id}")
            logger.info(f"Task status before save: {job.task.status}")
            logger.info(
                f"Task result length before save: {len(job.task.result) if job.task.result else 0}"
            )

            try:

                with transaction.atomic():
                    job.task.save()
                    logger.info("Task saved successfully within transaction")

                    # Verify the save worked by refetching
                    job.task.refresh_from_db()
                    logger.info(f"Task status after save: {job.task.status}")
                    logger.info(
                        f"Task result after save: {job.task.result is not None}"
                    )
                    logger.info(
                        f"Task result length after save: {len(job.task.result) if job.task.result else 0}"
                    )

            except Exception as save_error:
                logger.error(f"Error saving task to database: {save_error}")
                logger.error(f"Save error details: {str(save_error)}", exc_info=True)
                raise

            logger.info(f"Updated database record for task {task_id} to SUCCESS")
            logger.info(f"Saved result JSON length: {len(result_json)}")
            logger.info(f"Saved result JSON preview: {result_json[:200]}...")
        else:
            logger.error(f"No task found for job {job_id}")

        logger.info("=== TASK COMPLETED SUCCESSFULLY ===")
        return result_dicts

    except Exception as e:
        logger.error("=== TASK FAILED ===")
        logger.error(f"Error in run_search for job {job_id}: {str(e)}", exc_info=True)
        if "job" in locals() and job.task:
            logger.info("Updating task status to FAILURE...")
            job.task.status = "FAILURE"
            job.task.result = str(e)
            job.task.date_done = timezone.now()
            job.task.save()
            logger.info(f"Updated database record for task {task_id} to FAILURE")
        raise


def parse_biopython_alignment(query: str, target: str) -> Optional[AlignmentDisplay]:
    """Create simple alignment display using Biopython for phmmer cases"""
    try:
        alignments = pairwise2.align.globalxx(query, target)
        if not alignments:
            return None
        aln = alignments[0]
        aligned_query, aligned_target, score, begin, end = aln
        mline = AlignmentCalculator.create_match_line(aligned_query, aligned_target)

        def first_non_gap(seq):
            for i, c in enumerate(seq):
                if c != "-":
                    return i
            return 0

        def last_non_gap(seq):
            for i in range(len(seq) - 1, -1, -1):
                if seq[i] != "-":
                    return i
            return len(seq) - 1

        hmmfrom = first_non_gap(aligned_query) + 1
        hmmto = last_non_gap(aligned_query) + 1
        sqfrom = first_non_gap(aligned_target) + 1
        sqto = last_non_gap(aligned_target) + 1

        (identity_pct, number_of_identical), (
            similarity_pct,
            number_of_identical_and_similar,
        ) = AlignmentCalculator.calculate_identity_and_similarity_from_sequences(
            aligned_query, aligned_target
        )

        return AlignmentDisplay(
            hmmfrom=hmmfrom,
            hmmto=hmmto,
            sqfrom=sqfrom,
            sqto=sqto,
            model=aligned_query,
            aseq=aligned_target,
            mline=mline,
            ppline=None,
            identity=(identity_pct, number_of_identical),
            similarity=(similarity_pct, number_of_identical_and_similar),
        )
    except Exception as e:
        logger.warning(f"Biopython alignment parsing failed: {e}")
        return None


@shared_task
def cleanup_old_tasks():
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = TaskResult.objects.filter(date_done__lt=cutoff).delete()
    return f"Deleted {deleted} old task results"
