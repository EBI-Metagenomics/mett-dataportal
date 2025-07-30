import logging

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_celery_results.models import TaskResult

from pyhmmer_search.search.models import HmmerJob
from pyhmmer_search.search.tasks import run_search

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test PyHMMER job creation and task execution"

    def handle(self, *args, **options):
        self.stdout.write("=== TESTING PYHMMER JOB CREATION ===")

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

        self.stdout.write("Creating test job...")
        job = HmmerJob(**job_data, algo=HmmerJob.AlgoChoices.PHMMER)
        self.stdout.write(f"Job object created with ID: {job.id}")

        # Save the job
        job.save()
        self.stdout.write(f"Job saved to database with ID: {job.id}")

        # Verify job exists
        try:
            saved_job = HmmerJob.objects.get(id=job.id)
            self.stdout.write(f"Job verified in database: {saved_job}")
        except HmmerJob.DoesNotExist:
            self.stdout.write(self.style.ERROR("Job not found in database after save!"))
            return

        # Start the task
        self.stdout.write("Starting Celery task...")
        job_id_str = str(job.id)
        self.stdout.write(f"Passing job ID to task: {job_id_str}")

        try:
            result = run_search.delay(job_id_str)
            self.stdout.write(f"Celery task started with ID: {result.id}")

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
            self.stdout.write(f"TaskResult created: {task_result}")

            # Link the task to the job
            job.task = task_result
            job.save()
            self.stdout.write("Task linked successfully")

            self.stdout.write(
                self.style.SUCCESS("Job creation test completed successfully")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error starting task: {e}"))
            return
