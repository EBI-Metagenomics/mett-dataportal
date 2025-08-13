"""
Integration tests for PyHMMER search functionality using Django Ninja.

These tests test the actual search API endpoints, search execution, and result processing.
They require a running database and may take longer to execute than unit tests.
"""

import pytest
import json
import time
from decimal import Decimal
from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django_celery_results.models import TaskResult
from django.test import TestCase
from ninja.testing import TestClient
from django.db import transaction

from pyhmmer_search.search.models import HmmerJob, Database
from pyhmmer_search.search.schemas import SearchRequestSchema
from pyhmmer_search.search.tasks import run_search
from pyhmmer_search.search.api import pyhmmer_router_search


class TestPyhmmerSearchIntegration(TransactionTestCase):
    """Integration tests for PyHMMER search functionality using Django Ninja."""

    def setUp(self):
        """Set up test data and client."""
        super().setUp()
        
        try:
            # Create test user within a transaction
            with transaction.atomic():
                self.user = User.objects.create_user(
                    username='testuser',
                    password='testpass123'
                )
        except Exception as e:
            self.fail(f"Failed to create test user: {e}")
        
        try:
            # Create test database within a transaction
            with transaction.atomic():
                self.test_db = Database.objects.create(
                    name='test_db',
                    description='Test database for integration tests',
                    path='/tmp/test_db',
                    is_active=True
                )
        except Exception as e:
            self.fail(f"Failed to create test database: {e}")
        
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

    def test_search_api_endpoint_creation(self):
        """Test that search API endpoint creates a job correctly."""
        # Create a test client for Django Ninja
        client = TestClient(pyhmmer_router_search)
        
        # Make the request
        response = client.post("", json=self.search_request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('id', response.json())
        
        # Verify job was created in database
        job_id = response.json()['id']
        job = HmmerJob.objects.get(id=job_id)
        
        self.assertEqual(job.database.name, 'test_db')
        self.assertEqual(job.threshold, 'evalue')
        self.assertEqual(job.threshold_value, 0.01)
        self.assertEqual(job.input, self.test_sequence)
        self.assertEqual(job.E, 1.0)
        self.assertEqual(job.incE, 0.01)

    def test_search_api_validation(self):
        """Test search API validation with invalid data."""
        client = TestClient(pyhmmer_router_search)
        
        # Test with missing required fields
        invalid_request = {"database": "test_db"}
        response = client.post("", json=invalid_request)
        self.assertEqual(response.status_code, 422)  # Django Ninja returns 422 for validation errors
        
        # Test with invalid threshold value
        invalid_request = {
            **self.search_request,
            "threshold_value": -1.0  # Invalid negative value
        }
        response = client.post("", json=invalid_request)
        self.assertEqual(response.status_code, 422)

    def test_search_api_database_validation(self):
        """Test search API validation for database existence."""
        client = TestClient(pyhmmer_router_search)
        
        # Test with non-existent database
        invalid_request = {
            **self.search_request,
            "database": "non_existent_db"
        }
        response = client.post("", json=invalid_request)
        self.assertEqual(response.status_code, 422)

    def test_search_job_lifecycle(self):
        """Test complete search job lifecycle from creation to completion."""
        client = TestClient(pyhmmer_router_search)
        
        # Create a job
        response = client.post("", json=self.search_request)
        self.assertEqual(response.status_code, 200)
        
        job_id = response.json()['id']
        job = HmmerJob.objects.get(id=job_id)
        
        # Verify initial job state
        self.assertEqual(job.status, 'PENDING')
        self.assertIsNotNone(job.task)
        
        # Simulate job execution (in real scenario, this would be done by Celery)
        # For integration tests, we'll manually execute the task
        try:
            # This would normally be executed by Celery
            # For testing, we'll call it directly
            result = run_search(job_id)
            
            # Refresh job from database
            job.refresh_from_db()
            
            # Verify job completed successfully
            self.assertEqual(job.status, 'SUCCESS')
            self.assertIsNotNone(job.task)
            self.assertEqual(job.task.status, 'SUCCESS')
            
            # Verify results were generated
            self.assertIsNotNone(result)
            self.assertIsInstance(result, list)
            
        except Exception as e:
            # If the search fails (e.g., no actual database), that's expected in test environment
            # We'll just verify the job structure was created correctly
            self.fail(f"Search execution failed: {e}")

    def test_get_databases_endpoint(self):
        """Test get databases endpoint."""
        client = TestClient(pyhmmer_router_search)
        
        # Test databases endpoint
        response = client.get("/databases")
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        data = response.json()
        self.assertIn('data', data)  # Django Ninja wraps responses
        databases = data['data']
        
        # Should have at least our test database
        self.assertGreaterEqual(len(databases), 1)
        
        # Find our test database
        test_db_data = next((db for db in databases if db['name'] == 'test_db'), None)
        self.assertIsNotNone(test_db_data)
        self.assertEqual(test_db_data['name'], 'test_db')

    def test_search_with_different_thresholds(self):
        """Test search with different threshold types."""
        client = TestClient(pyhmmer_router_search)
        
        # Test E-value threshold
        evalue_request = {
            **self.search_request,
            "threshold": "evalue",
            "threshold_value": 0.001
        }
        
        response = client.post("", json=evalue_request)
        self.assertEqual(response.status_code, 200)
        
        # Test Bit Score threshold
        bitscore_request = {
            **self.search_request,
            "threshold": "bitscore",
            "threshold_value": 25.0
        }
        
        response = client.post("", json=bitscore_request)
        self.assertEqual(response.status_code, 200)

    def test_search_parameter_validation(self):
        """Test search parameter validation and relationships."""
        client = TestClient(pyhmmer_router_search)
        
        # Test that incE must be <= E
        invalid_request = {
            **self.search_request,
            "incE": 0.1,  # 0.1 > 1.0 (E)
            "E": 1.0
        }
        response = client.post("", json=invalid_request)
        self.assertEqual(response.status_code, 422)
        
        # Test that incT must be >= T
        invalid_request = {
            **self.search_request,
            "threshold": "bitscore",
            "incT": 20.0,  # 20.0 < 25.0 (T)
            "T": 25.0
        }
        response = client.post("", json=invalid_request)
        self.assertEqual(response.status_code, 422)

    def test_search_history_persistence(self):
        """Test that search jobs are properly persisted."""
        client = TestClient(pyhmmer_router_search)
        
        # Create multiple jobs
        for i in range(3):
            request = {
                **self.search_request,
                "input": f"SEQUENCE_{i}_{self.test_sequence}"
            }
            response = client.post("", json=request)
            self.assertEqual(response.status_code, 200)
        
        # Verify all jobs were created
        self.assertEqual(HmmerJob.objects.count(), 3)
        
        # Verify jobs have different inputs
        inputs = list(HmmerJob.objects.values_list('input', flat=True))
        self.assertEqual(len(set(inputs)), 3)

    def test_error_handling(self):
        """Test error handling in search API."""
        client = TestClient(pyhmmer_router_search)
        
        # Test with malformed JSON
        response = client.post("", data="invalid json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        
        # Test with empty request
        response = client.post("", json={})
        self.assertEqual(response.status_code, 422)

    def test_search_api_response_structure(self):
        """Test that search API returns the expected response structure."""
        client = TestClient(pyhmmer_router_search)
        
        response = client.post("", json=self.search_request)
        self.assertEqual(response.status_code, 200)
        
        # Verify response structure
        data = response.json()
        self.assertIn('id', data)
        self.assertIsInstance(data['id'], str)  # Job ID should be a string
        
        # Verify job was created with correct data
        job_id = data['id']
        job = HmmerJob.objects.get(id=job_id)
        self.assertEqual(job.input, self.test_sequence)
        self.assertEqual(job.database.name, 'test_db')

    def tearDown(self):
        """Clean up test data."""
        try:
            # Clean up test jobs
            HmmerJob.objects.all().delete()
            TaskResult.objects.all().delete()
            
            # Clean up test database
            Database.objects.filter(name='test_db').delete()
            
            # Clean up test user
            User.objects.filter(username='testuser').delete()
        except Exception as e:
            # Log cleanup errors but don't fail the test
            print(f"Warning: Error during test cleanup: {e}")


class TestPyhmmerSearchEdgeCases(TransactionTestCase):
    """Integration tests for PyHMMER search edge cases."""

    def setUp(self):
        """Set up test data and client."""
        super().setUp()
        
        try:
            # Create test user within a transaction
            with transaction.atomic():
                self.user = User.objects.create_user(
                    username='testuser',
                    password='testpass123'
                )
        except Exception as e:
            self.fail(f"Failed to create test user: {e}")
        
        try:
            # Create test database within a transaction
            with transaction.atomic():
                self.test_db = Database.objects.create(
                    name='test_db',
                    description='Test database for integration tests',
                    path='/tmp/test_db',
                    is_active=True
                )
        except Exception as e:
            self.fail(f"Failed to create test database: {e}")

    def test_search_with_empty_sequence(self):
        """Test search behavior with empty sequence."""
        client = TestClient(pyhmmer_router_search)
        
        request = {
            "database": "test_db",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": "",  # Empty sequence
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03
        }
        
        response = client.post("", json=request)
        # This should either succeed or fail with a specific error
        self.assertIn(response.status_code, [200, 422])

    def test_search_with_very_long_sequence(self):
        """Test search behavior with very long sequence."""
        client = TestClient(pyhmmer_router_search)
        
        # Create a very long sequence
        long_sequence = "M" * 10000  # 10k amino acids
        
        request = {
            "database": "test_db",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": long_sequence,
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03
        }
        
        response = client.post("", json=request)
        # This should either succeed or fail with a specific error
        self.assertIn(response.status_code, [200, 422])

    def test_search_with_special_characters(self):
        """Test search behavior with special characters in sequence."""
        client = TestClient(pyhmmer_router_search)
        
        # Test sequence with special characters
        special_sequence = "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY*X"
        
        request = {
            "database": "test_db",
            "threshold": "evalue",
            "threshold_value": 0.01,
            "input": special_sequence,
            "E": 1.0,
            "domE": 1.0,
            "incE": 0.01,
            "incdomE": 0.03
        }
        
        response = client.post("", json=request)
        # This should either succeed or fail with a specific error
        self.assertEqual(response.status_code, 422)

    def tearDown(self):
        """Clean up test data."""
        try:
            Database.objects.filter(name='test_db').delete()
            User.objects.filter(username='testuser').delete()
        except Exception as e:
            # Log cleanup errors but don't fail the test
            print(f"Warning: Error during test cleanup: {e}")
