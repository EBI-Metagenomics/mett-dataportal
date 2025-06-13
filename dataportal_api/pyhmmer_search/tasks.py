import io
import logging
from django.utils import timezone

from celery import shared_task
from django_celery_results.models import TaskResult
from pyhmmer.easel import SequenceFile, Alphabet
from pyhmmer.plan7 import Pipeline, HMMFile, Background

from dataportal import settings
from dataportal.celery import app
from .models import HmmerJob

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="pyhmmer_queue", routing_key="pyhmmer.search")
def run_search(self, job_id: str):
    task_id = self.request.id
    logger.info(f"Running HMMER search for job {job_id} with task ID {task_id}")
    try:
        job = HmmerJob.objects.select_related("task").get(id=job_id)
        logger.info(f"Found job {job_id} with task {job.task.task_id if job.task else 'No task'}")

        # Update task state using Celery's state management
        self.update_state(state='STARTED')
        logger.info(f"Updated task {task_id} state to STARTED")
        
        # Update database record
        if job.task:
            job.task.status = 'STARTED'
            job.task.save()
            logger.info(f"Updated database record for task {task_id} to STARTED")

        db_path = settings.HMMER_DATABASES[job.database]
        if not db_path:
            raise ValueError(f"Invalid database ID '{job.database}'")

        logger.debug(f"Using database: {db_path}")

        results = []

        # phmmer search
        with SequenceFile(io.BytesIO(job.input.encode())) as query_file:
            with open(db_path, "rb") as db_f:
                with SequenceFile(db_f) as target_file:
                    # Get the alphabet from the target file
                    alphabet = target_file.alphabet
                    if not alphabet:
                        raise ValueError("Could not determine alphabet from target file")
                    logger.info(f"Using alphabet: {alphabet}")
                    
                    # Create background model with explicit alphabet type
                    try:
                        background = Background(alphabet=alphabet)
                        logger.info(f"Created background model for alphabet: {alphabet}")
                    except Exception as e:
                        logger.error(f"Failed to create background model: {str(e)}")
                        raise ValueError(f"Failed to create background model: {str(e)}")
                    
                    # Create pipeline with default configuration
                    pipeline = Pipeline(
                        alphabet,  # First positional argument - the alphabet
                        background=background,  # Background model
                        bias_filter=True,  # Enable bias filter
                        null2=True,  # Use null2 model
                        domE=job.threshold_value if job.threshold == HmmerJob.ThresholdChoices.EVALUE else None,
                        domT=job.threshold_value if job.threshold == HmmerJob.ThresholdChoices.BITSCORE else None,
                    )
                    
                    # Search using the pipeline
                    for hits in pipeline.search(query_file, target_file):
                        for hit in hits:
                            if job.threshold == HmmerJob.ThresholdChoices.EVALUE:
                                if hit.evalue < job.threshold_value:
                                    results.append({
                                        "target": hit.name.decode(),
                                        "evalue": hit.evalue,
                                        "score": hit.score,
                                    })
                            elif job.threshold == HmmerJob.ThresholdChoices.BITSCORE:
                                if hit.score > job.threshold_value:
                                    results.append({
                                        "target": hit.name.decode(),
                                        "evalue": hit.evalue,
                                        "score": hit.score,
                                    })

        logger.info(f"{len(results)} hits passed the filter for job {job_id}")
        
        # Update database record with success
        if job.task:
            job.task.status = 'SUCCESS'
            job.task.result = results
            job.task.date_done = timezone.now()
            job.task.save()
            logger.info(f"Updated database record for task {task_id} to SUCCESS")
            
        return results

    except Exception as e:
        logger.error(f"Error in run_search for job {job_id}: {str(e)}", exc_info=True)
        # Update database record with failure
        if job.task:
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
