import io
import logging

from celery import shared_task
from django_celery_results.models import TaskResult
from pyhmmer.easel import SequenceFile
from pyhmmer.plan7 import Pipeline

from dataportal import settings
from dataportal.celery import app
from .models import HmmerJob

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_search(self, job_id: str):
    logger.info(f"Running HMMER search for job {job_id}")
    job = HmmerJob.objects.select_related("task").get(id=job_id)

    # Link task result to job
    task_result = TaskResult.objects.get(task_id=self.request.id)
    job.task = task_result
    job.save(update_fields=["task"])

    db_path = settings.HMMER_DATABASES[job.database]
    if not db_path:
        raise ValueError(f"Invalid database ID '{job.database}'")

    logger.debug(f"Using database: {db_path}")

    results = []

    # phmmer search
    with SequenceFile(io.BytesIO(job.input.encode())) as query_file:
        with open(db_path, "rb") as db_f:
            with SequenceFile(db_f) as target_file:
                pipeline = Pipeline()
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

    # TODO: Save results to database
    return results


@shared_task
def test_task():
    logger.info(">>> Test task is running")
    print(">>> Hello from test_task")
    return "OK"