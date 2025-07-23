#!/usr/bin/env python
"""
Test script to debug job creation and task execution issues.
Run this script to test the job creation flow without the full API.
"""

import os
import sys
import django
import logging

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dataportal.settings")
django.setup()

from django.utils import timezone
from django_celery_results.models import TaskResult
from .models import HmmerJob
from .tasks import run_search

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_job_creation():
    """Test job creation and task execution flow."""
    logger.info("=== TESTING JOB CREATION FLOW ===")

    # Create a test job
    job_data = {
        "database": "bu_all",
        "threshold": "evalue",
        "threshold_value": 0.01,
        "input": ">Test sequence\nMADEUPSEQ",
        "mx": "BLOSUM62",
        "E": 1.0,
        "domE": 1.0,
        "incE": 0.01,
        "incdomE": 0.03,
        "T": None,
        "domT": None,
        "incT": None,
        "incdomT": None,
        "popen": 0.02,
        "pextend": 0.4,
    }

    logger.info("Creating test job...")
    job = HmmerJob(**job_data, algo=HmmerJob.AlgoChoices.PHMMER)
    logger.info(f"Job object created with ID: {job.id}")
    logger.info(f"Job ID type: {type(job.id)}")

    # Save the job
    job.save()
    logger.info(f"Job saved to database with ID: {job.id}")

    # Verify job exists
    try:
        saved_job = HmmerJob.objects.get(id=job.id)
        logger.info(f"Job verified in database: {saved_job}")
    except HmmerJob.DoesNotExist:
        logger.error("Job not found in database after save!")
        return False

    # Start the task
    logger.info("Starting Celery task...")
    job_id_str = str(job.id)
    logger.info(f"Passing job ID to task: {job_id_str}")

    try:
        result = run_search.delay(job_id_str)
        logger.info(f"Celery task started with ID: {result.id}")

        # Create TaskResult entry
        task_result = TaskResult.objects.create(
            task_id=result.id,
            status="PENDING",
            result=None,
            traceback=None,
            meta=None,
            date_done=None,
            date_created=timezone.now(),
        )
        logger.info(f"TaskResult created: {task_result}")

        # Link the task to the job
        job.task = task_result
        job.save()
        logger.info("Task linked successfully")

        return True

    except Exception as e:
        logger.error(f"Error starting task: {e}")
        return False


def test_job_retrieval(job_id):
    """Test retrieving a specific job."""
    logger.info(f"=== TESTING JOB RETRIEVAL FOR {job_id} ===")

    try:
        job = HmmerJob.objects.get(id=job_id)
        logger.info(f"Found job: {job}")
        return True
    except HmmerJob.DoesNotExist:
        logger.error(f"Job {job_id} not found")

        # List all jobs
        all_jobs = HmmerJob.objects.all()
        logger.info(f"Total jobs in database: {all_jobs.count()}")
        for j in all_jobs[:5]:
            logger.info(f"  - Job ID: {j.id}")

        return False


if __name__ == "__main__":
    # Test job creation
    success = test_job_creation()

    if success:
        logger.info("Job creation test completed successfully")
    else:
        logger.error("Job creation test failed")

    # Test specific job retrieval if provided
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        test_job_retrieval(job_id)
