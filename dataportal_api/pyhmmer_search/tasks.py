import json
import logging

from Bio import pairwise2
from Bio.pairwise2 import format_alignment
from celery import shared_task
from django.utils import timezone
from django_celery_results.models import TaskResult
from pyhmmer.easel import DigitalSequenceBlock
from pyhmmer.easel import TextSequence, Alphabet, SequenceFile
from pyhmmer.plan7 import Pipeline, Background

from dataportal import settings
from .models import HmmerJob

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


@shared_task(bind=True, queue="pyhmmer_queue", routing_key="pyhmmer.search")
def run_search(self, job_id: str):
    task_id = self.request.id
    logger.info(f"Running HMMER search for job {job_id} with task ID {task_id}")
    try:
        job = HmmerJob.objects.select_related("task").get(id=job_id)
        logger.info(
            f"Found job {job_id} with task {job.task.task_id if job.task else 'No task'}"
        )

        self.update_state(state="STARTED")
        if job.task:
            job.task.status = "STARTED"
            job.task.save()

        db_path = settings.HMMER_DATABASES[job.database]
        if not db_path:
            raise ValueError(f"Invalid database ID '{job.database}'")

        # Prepare alphabet and background
        alphabet = Alphabet.amino()
        background = Background(alphabet)
        pipeline = Pipeline(
            alphabet,
            background=background,
            bias_filter=True,
            null2=True,
            domE=(
                job.threshold_value
                if job.threshold == HmmerJob.ThresholdChoices.EVALUE
                else None
            ),
            domT=(
                job.threshold_value
                if job.threshold == HmmerJob.ThresholdChoices.BITSCORE
                else None
            ),
            mx=job.mx if job.mx else "BLOSUM62",
        )

        # Parse query
        lines = job.input.strip().splitlines()
        if not lines or not lines[0].startswith(">") or len(lines) < 2:
            raise ValueError("Invalid FASTA input format for query.")

        name = lines[0].lstrip(">").encode("utf-8")
        sequence = "".join(lines[1:])
        text_seq = TextSequence(name=name, sequence=sequence)
        digital_seq = text_seq.digitize(alphabet)

        # Read target sequences
        with SequenceFile(db_path, format="fasta") as target_file:
            digital_targets = [seq.digitize(alphabet) for seq in target_file]
        logger.info(f"Digitized {len(digital_targets)} target sequences from {db_path}")

        # Also build a mapping from name to TextSequence for alignment
        target_sequences = {}
        with SequenceFile(db_path, format="fasta") as target_file:
            for seq in target_file:
                target_sequences[seq.name.decode()] = seq

        # Run search
        results = []
        block = DigitalSequenceBlock(alphabet)
        block.extend(digital_targets)

        hits = pipeline.search_seq(digital_seq, block)

        try:
            hit_list = list(hits)
            logger.debug(f"Top hits: {[hit.name.decode() for hit in hit_list[:5]]}")
        except Exception as e:
            logger.debug(f"Could not log top hits due to error: {e}")

        for hit in hit_list:
            # Build domains info for this hit
            domains = []
            if hasattr(hit, "domains") and hit.domains:
                for domain in hit.domains:
                    alignment = getattr(domain, "alignment", None)
                    if alignment is not None:
                        try:
                            pretty_alignment = alignment.pretty()
                            sqfrom = getattr(alignment, "sqfrom", None)
                            sqto = getattr(alignment, "sqto", None)
                            hmmfrom = getattr(alignment, "hmmfrom", None)
                            hmmto = getattr(alignment, "hmmto", None)
                            model = getattr(alignment, "model", None)
                            aseq = getattr(alignment, "aseq", None)
                            mline = getattr(alignment, "mline", None)
                            ppline = getattr(alignment, "ppline", None)
                        except Exception:
                            pretty_alignment = None
                            sqfrom = sqto = hmmfrom = hmmto = model = aseq = mline = (
                                ppline
                            ) = None
                    else:
                        pretty_alignment = None
                        sqfrom = sqto = hmmfrom = hmmto = model = aseq = mline = (
                            ppline
                        ) = None

                    if hasattr(domain, "segments") and domain.segments:
                        for i, (start, end) in enumerate(domain.segments):
                            domain_dict = {
                                "env_from": domain.env_from,
                                "env_to": domain.env_to,
                                "bitscore": domain.score,
                                "ievalue": domain.i_evalue,
                                "cevalue": domain.c_evalue,
                                "bias": getattr(domain, "bias", None),
                                "alignment_display": pretty_alignment,
                                "sqfrom": sqfrom,
                                "sqto": sqto,
                                "hmmfrom": hmmfrom,
                                "hmmto": hmmto,
                                "model": model,
                                "aseq": aseq,
                                "mline": mline,
                                "ppline": ppline,
                            }
                            domains.append(domain_dict)
                    else:
                        domain_dict = {
                            "env_from": domain.env_from,
                            "env_to": domain.env_to,
                            "seq_from": getattr(domain, "seq_from", None),
                            "seq_to": getattr(domain, "seq_to", None),
                            "hmm_from": getattr(domain, "hmm_from", None),
                            "hmm_to": getattr(domain, "hmm_to", None),
                            "bitscore": f"{hit.score:.2f}",
                            "ievalue": domain.i_evalue,
                            "cevalue": domain.c_evalue,
                            "bias": getattr(domain, "bias", None),
                            "alignment_display": pretty_alignment,
                        }
                        domains.append(domain_dict)
            else:
                # Fallback for phmmer: create a pseudo-domain from hit and compute alignment
                target_seq = target_sequences.get(hit.name.decode())
                alignment_str = None
                if target_seq is not None:
                    try:
                        query_seq_str = str(sequence)
                        target_seq_str = str(target_seq.sequence.decode())
                        logger.info(
                            f"Aligning query ({len(query_seq_str)}) to target ({len(target_seq_str)}) for hit {hit.name.decode()}"
                        )
                        alignments = pairwise2.align.globalxx(
                            query_seq_str, target_seq_str
                        )
                        if alignments:
                            alignment_str = format_alignment(*alignments[0])
                            logger.info(
                                f"Alignment for {hit.name.decode()} successful."
                            )
                        else:
                            logger.warning(
                                f"No alignment produced for {hit.name.decode()}."
                            )
                    except Exception as e:
                        logger.warning(f"Alignment failed for {hit.name.decode()}: {e}")
                        alignment_str = None
                else:
                    logger.warning(
                        f"Target sequence not found for hit {hit.name.decode()}"
                    )
                domains.append(
                    {
                        "env_from": getattr(hit, "envelope_from", None),
                        "env_to": getattr(hit, "envelope_to", None),
                        "bitscore": f"{hit.score:.2f}",
                        "ievalue": hit.evalue,
                        "cevalue": getattr(hit, "c_evalue", None),
                        "bias": getattr(hit, "bias", None),
                        "alignment_display": alignment_str,
                    }
                )

            hit_dict = {
                "target": hit.name.decode(),
                "description": hit.description.decode(),
                "evalue": f"{hit.evalue:.2e}",
                "score": f"{hit.score:.2f}",
                "num_hits": len(hit_list) or None,
                "num_significant": sum(1 for h in hit_list if h.evalue < 0.01),
                "domains": domains,
            }
            if (
                job.threshold == HmmerJob.ThresholdChoices.EVALUE
                and hit.evalue < job.threshold_value
            ):
                results.append(hit_dict)
            elif (
                job.threshold == HmmerJob.ThresholdChoices.BITSCORE
                and hit.score > job.threshold_value
            ):
                results.append(hit_dict)

        logger.info(f"{len(results)} hits passed the filter for job {job_id}")

        if job.task:
            job.task.status = "SUCCESS"
            job.task.result = json.dumps(results)
            job.task.date_done = timezone.now()
            job.task.save()
            logger.info(f"Updated database record for task {task_id} to SUCCESS")

        return results

    except Exception as e:
        logger.error(f"Error in run_search for job {job_id}: {str(e)}", exc_info=True)
        if "job" in locals() and job.task:
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


@shared_task
def cleanup_old_tasks():
    from django_celery_results.models import TaskResult
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = TaskResult.objects.filter(date_done__lt=cutoff).delete()
    return f"Deleted {deleted} old task results"
