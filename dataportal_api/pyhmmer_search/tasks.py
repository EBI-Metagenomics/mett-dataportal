import io
import logging
from django.utils import timezone

from celery import shared_task
from django_celery_results.models import TaskResult
from pyhmmer.easel import SequenceFile, Alphabet, TextSequence, DigitalSequenceBlock
from pyhmmer.plan7 import Pipeline, HMMFile, Background

from dataportal import settings
from dataportal.celery import app
from .models import HmmerJob

logger = logging.getLogger(__name__)


def _log_query_sequences(raw_bytes):
    try:
        # For pyhmmer 0.11+, TextSequence.sequence is str
        lines = raw_bytes.decode().strip().splitlines()
        name = lines[0].lstrip('>').encode()
        sequence = ''.join(lines[1:])
        text_seq = TextSequence(name=name, sequence=sequence)
        logger.error(f"Seq: name={text_seq.name}, type={type(text_seq.sequence)}, first100={text_seq.sequence[:100]}")
    except Exception as e:
        logger.error(f"Error logging query sequences: {e}")


@shared_task(bind=True, queue="pyhmmer_queue", routing_key="pyhmmer.search")
def run_search(self, job_id: str):
    import json
    from pyhmmer.easel import TextSequence, Alphabet, SequenceFile
    from pyhmmer.plan7 import Pipeline, Background
    from django.utils import timezone

    task_id = self.request.id
    logger.info(f"Running HMMER search for job {job_id} with task ID {task_id}")
    try:
        job = HmmerJob.objects.select_related("task").get(id=job_id)
        logger.info(f"Found job {job_id} with task {job.task.task_id if job.task else 'No task'}")

        self.update_state(state='STARTED')
        if job.task:
            job.task.status = 'STARTED'
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
            domE=job.threshold_value if job.threshold == HmmerJob.ThresholdChoices.EVALUE else None,
            domT=job.threshold_value if job.threshold == HmmerJob.ThresholdChoices.BITSCORE else None,
        )

        # Parse query
        lines = job.input.strip().splitlines()
        if not lines or not lines[0].startswith(">") or len(lines) < 2:
            raise ValueError("Invalid FASTA input format for query.")

        name = lines[0].lstrip(">").encode("utf-8")
        sequence = ''.join(lines[1:])
        text_seq = TextSequence(name=name, sequence=sequence)
        digital_seq = text_seq.digitize(alphabet)

        # Read target sequences
        with SequenceFile(db_path, format="fasta") as target_file:
            digital_targets = [seq.digitize(alphabet) for seq in target_file]
        logger.info(f"Digitized {len(digital_targets)} target sequences from {db_path}")

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
            for domain in hit.domains:
                domain_dict = {
                    "ienv": domain.env_from,
                    "jenv": domain.env_to,
                    # "seq_from": domain.seq_from,
                    # "seq_to": domain.seq_to,
                    # "hmm_from": domain.hmm_from,
                    # "hmm_to": domain.hmm_to,
                    "bitscore": domain.score,
                    "ievalue": domain.i_evalue,
                    "cevalue": domain.c_evalue,
                    "bias": getattr(domain, 'bias', None),
                    # Add alignment display if available
                    # "alignment_display": ...
                }
                # Optionally, add pretty alignment if available
                if hasattr(domain, 'alignment') and domain.alignment is not None:
                    try:
                        domain_dict["alignment_display"] = domain.alignment.pretty()
                    except Exception:
                        pass
                domains.append(domain_dict)

            hit_dict = {
                "target": hit.name.decode(),
                "description": hit.description.decode(),
                "evalue": hit.evalue,
                "score": hit.score,
                "num_hits": len(hit_list) or None,
                "num_significant": sum(1 for h in hit_list if h.evalue < 0.01),  # Example threshold
                "domains": domains
            }
            if job.threshold == HmmerJob.ThresholdChoices.EVALUE and hit.evalue < job.threshold_value:
                results.append(hit_dict)
            elif job.threshold == HmmerJob.ThresholdChoices.BITSCORE and hit.score > job.threshold_value:
                results.append(hit_dict)

        logger.info(f"{len(results)} hits passed the filter for job {job_id}")

        if job.task:
            job.task.status = 'SUCCESS'
            job.task.result = json.dumps(results)
            job.task.date_done = timezone.now()
            job.task.save()
            logger.info(f"Updated database record for task {task_id} to SUCCESS")

        return results

    except Exception as e:
        logger.error(f"Error in run_search for job {job_id}: {str(e)}", exc_info=True)
        if 'job' in locals() and job.task:
            job.task.status = 'FAILURE'
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
        self.update_state(state='STARTED')
        logger.info(f"Updated task {task_id} state to STARTED")

        # Update database record
        task_result = TaskResult.objects.get(task_id=task_id)
        task_result.status = 'STARTED'
        task_result.save()
        logger.info(f"Updated database record for task {task_id} to STARTED")

        # Simulate some work
        logger.info(">>> Hello from test_task")

        # Check if any jobs are linked to this task
        linked_jobs = HmmerJob.objects.filter(task__task_id=task_id)
        logger.info(f"Found {linked_jobs.count()} jobs linked to task {task_id}")
        for job in linked_jobs:
            logger.info(f"Linked job: {job.id}, Status: {job.task.status if job.task else 'No task'}")

        # Update database record with success
        task_result.status = 'SUCCESS'
        task_result.result = "OK"
        task_result.date_done = timezone.now()
        task_result.save()
        logger.info(f"Updated database record for task {task_id} to SUCCESS")

    except Exception as e:
        logger.error(f"Error in test_task: {str(e)}", exc_info=True)
        # Update database record with failure
        if 'task_result' in locals():
            task_result.status = 'FAILURE'
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
