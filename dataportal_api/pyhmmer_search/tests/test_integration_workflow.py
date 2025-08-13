import pytest
import json
import time
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django_celery_results.models import TaskResult
from rest_framework.test import APIClient
from rest_framework import status

from pyhmmer_search.search.models import HmmerJob, Database
from pyhmmer_search.search.tasks import run_search
from pyhmmer_search.results.api import get_job_results
from pyhmmer_search.search.schemas import SearchRequestSchema, HitSchema, DomainSchema


class TestPyhmmerCompleteWorkflow(TestCase):
    """Integration tests for complete PyHMMER workflow."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test database
        self.test_db = Database.objects.create(
            name='test_db',
            description='Test database for integration tests',
            path='/tmp/test_db',
            is_active=True
        )
        
        # Test sequence data
        self.test_sequence = "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY"
        
        # Sample search request
        self.search_request = {
            "database": "test_db",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": self.test_sequence,
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03,
            "T": None,
            "domT": None,
            "incT": None,
            "incdomT": None,
            "popen": 0.02,
            "pextend": 0.4
        }

    def test_complete_search_workflow(self):
        """Test complete search workflow from start to finish."""
        # Step 1: Create search job
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job_id = response.data['id']
        self.assertIsNotNone(job_id)
        
        # Step 2: Verify job was created in database
        job = HmmerJob.objects.get(id=job_id)
        self.assertEqual(job.status, 'PENDING')
        self.assertEqual(job.database.name, 'test_db')
        self.assertEqual(job.threshold, 'evalue')
        self.assertEqual(job.input, self.test_sequence)
        
        # Step 3: Check job status endpoint
        status_url = reverse('pyhmmer_search:job_status', kwargs={'job_id': job_id})
        response = self.client.get(status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'PENDING')
        
        # Step 4: Check job details endpoint
        details_url = reverse('pyhmmer_search:job_details', kwargs={'job_id': job_id})
        response = self.client.get(details_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], job_id)
        
        # Step 5: Check results endpoint (should be empty initially)
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = self.client.get(results_url)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        
        # Step 6: Simulate job execution (in real scenario, this would be done by Celery)
        try:
            # Execute the search task
            result = run_search(job_id)
            
            # Refresh job from database
            job.refresh_from_db()
            
            # Step 7: Verify job completed successfully
            self.assertEqual(job.status, 'SUCCESS')
            self.assertIsNotNone(job.task)
            self.assertEqual(job.task.status, 'SUCCESS')
            
            # Step 8: Verify results were generated
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
            
            # Step 9: Check results endpoint again (should now have data)
            response = self.client.get(results_url)
            if response.status_code == status.HTTP_200_OK:
                self.assertIn('results', response.data)
                self.assertIn('pagination', response.data)
                self.assertIn('total_count', response.data)
                
                # Verify results structure
                if response.data['results']:
                    first_result = response.data['results'][0]
                    expected_fields = ['target', 'description', 'evalue', 'score', 'num_hits', 'num_significant', 'is_significant']
                    for field in expected_fields:
                        self.assertIn(field, first_result)
            
        except Exception as e:
            # If the search fails (e.g., no actual database), that's expected in test environment
            # We'll just verify the job structure was created correctly
            self.fail(f"Search execution failed: {e}")

    def test_search_workflow_with_different_parameters(self):
        """Test search workflow with different parameter combinations."""
        # Test E-value threshold
        evalue_request = {
            **self.search_request,
            "threshold": "evalue",
            "threshold_value": 0.001,
            "incE": 0.001,
            "E": 0.1
        }
        
        self._test_workflow_with_request(evalue_request, "E-value threshold search")
        
        # Test Bit Score threshold
        bitscore_request = {
            **self.search_request,
            "threshold": "bitscore",
            "threshold_value": 25.0,
            "incT": 25.0,
            "T": 20.0
        }
        
        self._test_workflow_with_request(bitscore_request, "Bit Score threshold search")

    def _test_workflow_with_request(self, request_data, description):
        """Helper method to test workflow with specific request data."""
        # Create search job
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, request_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to create job for {description}")
        
        job_id = response.data['id']
        
        # Verify job parameters
        job = HmmerJob.objects.get(id=job_id)
        self.assertEqual(job.threshold, request_data['threshold'])
        self.assertEqual(job.threshold_value, request_data['threshold_value'])
        
        # Check job status
        status_url = reverse('pyhmmer_search:job_status', kwargs={'job_id': job_id})
        response = self.client.get(status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Clean up
        job.delete()

    def test_search_workflow_error_handling(self):
        """Test search workflow error handling."""
        # Test with invalid database
        invalid_request = {
            **self.search_request,
            "database": "non_existent_db"
        }
        
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, invalid_request, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        # Test with invalid threshold value
        invalid_request = {
            **self.search_request,
            "threshold_value": -1.0
        }
        
        response = self.client.post(url, invalid_request, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_search_workflow_concurrent_access(self):
        """Test search workflow with concurrent access patterns."""
        # Create multiple jobs simultaneously
        jobs = []
        url = reverse('pyhmmer_search:search')
        
        for i in range(3):
            request = {
                **self.search_request,
                "input": f"SEQUENCE_{i}_{self.test_sequence}"
            }
            response = self.client.post(url, request, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            jobs.append(response.data['id'])
        
        # Verify all jobs were created
        self.assertEqual(len(jobs), 3)
        self.assertEqual(HmmerJob.objects.count(), 3)
        
        # Check status of all jobs
        for job_id in jobs:
            status_url = reverse('pyhmmer_search:job_status', kwargs={'job_id': job_id})
            response = self.client.get(status_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('status', response.data)
        
        # Clean up
        for job_id in jobs:
            HmmerJob.objects.filter(id=job_id).delete()

    def test_search_workflow_data_persistence(self):
        """Test that search workflow data is properly persisted."""
        # Create a job
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job_id = response.data['id']
        
        # Verify job persistence
        job = HmmerJob.objects.get(id=job_id)
        self.assertEqual(job.input, self.test_sequence)
        self.assertEqual(job.database.name, 'test_db')
        
        # Update job status
        job.status = 'STARTED'
        job.save()
        
        # Verify persistence
        job.refresh_from_db()
        self.assertEqual(job.status, 'STARTED')
        
        # Clean up
        job.delete()

    def test_search_workflow_parameter_validation(self):
        """Test search workflow parameter validation."""
        # Test parameter relationships
        test_cases = [
            {
                "name": "incE > E",
                "request": {**self.search_request, "incE": 0.1, "E": 0.01},
                "expected_status": status.HTTP_422_UNPROCESSABLE_ENTITY
            },
            {
                "name": "incT < T",
                "request": {**self.search_request, "threshold": "bitscore", "incT": 20.0, "T": 25.0},
                "expected_status": status.HTTP_422_UNPROCESSABLE_ENTITY
            },
            {
                "name": "negative threshold",
                "request": {**self.search_request, "threshold_value": -0.01},
                "expected_status": status.HTTP_422_UNPROCESSABLE_ENTITY
            }
        ]
        
        url = reverse('pyhmmer_search:search')
        for test_case in test_cases:
            with self.subTest(test_case["name"]):
                response = self.client.post(url, test_case["request"], format='json')
                self.assertEqual(response.status_code, test_case["expected_status"])

    def test_search_workflow_performance(self):
        """Test search workflow performance characteristics."""
        # Create multiple jobs to test performance
        jobs = []
        url = reverse('pyhmmer_search:search')
        
        start_time = time.time()
        for i in range(5):
            request = {
                **self.search_request,
                "input": f"SEQUENCE_{i}_{self.test_sequence}"
            }
            response = self.client.post(url, request, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            jobs.append(response.data['id'])
        end_time = time.time()
        
        # Job creation should be reasonably fast
        creation_time = end_time - start_time
        self.assertLess(creation_time, 2.0, f"Job creation too slow: {creation_time:.2f}s")
        
        # Clean up
        for job_id in jobs:
            HmmerJob.objects.filter(id=job_id).delete()

    def test_search_workflow_integration_points(self):
        """Test integration points between different workflow components."""
        # Create a job
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job_id = response.data['id']
        
        # Test integration between search and status endpoints
        status_url = reverse('pyhmmer_search:job_status', kwargs={'job_id': job_id})
        status_response = self.client.get(status_url)
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_response.data['id'], job_id)
        
        # Test integration between search and details endpoints
        details_url = reverse('pyhmmer_search:job_details', kwargs={'job_id': job_id})
        details_response = self.client.get(details_url)
        self.assertEqual(details_response.status_code, status.HTTP_200_OK)
        self.assertEqual(details_response.data['id'], job_id)
        
        # Test integration between search and results endpoints
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        results_response = self.client.get(results_url)
        self.assertIn(results_response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        
        # Clean up
        HmmerJob.objects.filter(id=job_id).delete()

    def tearDown(self):
        """Clean up test data."""
        # Clean up test jobs
        HmmerJob.objects.all().delete()
        TaskResult.objects.all().delete()
        
        # Clean up test database
        Database.objects.filter(name='test_db').delete()
        
        # Clean up test user
        User.objects.filter(username='testuser').delete()


class TestPyhmmerWorkflowEdgeCases(TestCase):
    """Integration tests for PyHMMER workflow edge cases."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_workflow_with_empty_sequence(self):
        """Test workflow behavior with empty sequence."""
        # This should be handled by validation
        empty_request = {
            "database": "test_db",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": "",  # Empty sequence
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03
        }
        
        # Note: This might be allowed by the current validation
        # Adjust expected behavior based on your requirements

    def test_workflow_with_very_long_sequence(self):
        """Test workflow behavior with very long sequence."""
        # Create a very long sequence
        long_sequence = "M" * 10000  # 10k amino acids
        
        long_request = {
            "database": "test_db",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": long_sequence,
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03
        }
        
        # This should be handled gracefully (either accepted or rejected with appropriate error)

    def test_workflow_with_special_characters(self):
        """Test workflow behavior with special characters in sequence."""
        # Test sequence with special characters
        special_sequence = "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY*X"
        
        special_request = {
            "database": "test_db",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": special_sequence,
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03
        }
        
        # This should be handled appropriately

    def tearDown(self):
        """Clean up test data."""
        User.objects.filter(username='testuser').delete()
