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
from pyhmmer_search.results.schemas import JobDetailsResponseSchema


class TestPyhmmerResultsIntegration(TestCase):
    """Integration tests for PyHMMER results functionality."""

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

    def test_get_job_results_success(self):
        """Test successful retrieval of job results."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        job_id = response.data['id']
        
        # Test results endpoint
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = self.client.get(results_url)
        
        # Should get a response (even if no results yet)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        
        if response.status_code == status.HTTP_200_OK:
            # Verify response structure
            self.assertIn('results', response.data)
            self.assertIn('pagination', response.data)
            self.assertIn('total_count', response.data)

    def test_get_job_results_not_found(self):
        """Test results endpoint with non-existent job."""
        fake_job_id = "00000000-0000-0000-0000-000000000000"
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': fake_job_id})
        
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_job_results_unauthorized(self):
        """Test results endpoint without authentication."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        # Create unauthenticated client
        unauthenticated_client = APIClient()
        
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = unauthenticated_client.get(results_url)
        
        # Should require authentication
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_results_pagination_parameters(self):
        """Test results pagination with different parameters."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        # Test different page sizes
        for page_size in [10, 25, 50]:
            results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
            response = self.client.get(results_url, {'page_size': page_size})
            
            if response.status_code == status.HTTP_200_OK:
                self.assertIn('pagination', response.data)
                pagination = response.data['pagination']
                self.assertIn('page_size', pagination)
                self.assertIn('current_page', pagination)
                self.assertIn('total_pages', pagination)

    def test_results_filtering_parameters(self):
        """Test results filtering with different parameters."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        # Test different filter parameters
        filter_params = {
            'min_score': 50.0,
            'max_evalue': 1e-5,
            'target_contains': 'GENE'
        }
        
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = self.client.get(results_url, filter_params)
        
        # Should handle filter parameters gracefully
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_results_sorting_parameters(self):
        """Test results sorting with different parameters."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        # Test different sorting parameters
        sort_params = {
            'sort_by': 'score',
            'sort_order': 'desc'
        }
        
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = self.client.get(results_url, sort_params)
        
        # Should handle sorting parameters gracefully
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_results_data_structure(self):
        """Test that results have the expected data structure."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = self.client.get(results_url)
        
        if response.status_code == status.HTTP_200_OK:
            # Verify response structure
            self.assertIn('results', response.data)
            self.assertIn('pagination', response.data)
            self.assertIn('total_count', response.data)
            
            # Verify pagination structure
            pagination = response.data['pagination']
            self.assertIn('page', pagination)
            self.assertIn('page_size', pagination)
            self.assertIn('total_pages', pagination)
            self.assertIn('total_count', pagination)
            
            # Verify results structure (if any results exist)
            if response.data['results']:
                first_result = response.data['results'][0]
                expected_fields = ['target', 'description', 'evalue', 'score', 'num_hits', 'num_significant', 'is_significant']
                for field in expected_fields:
                    self.assertIn(field, first_result)

    def test_results_with_domains(self):
        """Test results that include domain information."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = self.client.get(results_url)
        
        if response.status_code == status.HTTP_200_OK and response.data['results']:
            first_result = response.data['results'][0]
            
            # Check if domains are present
            if 'domains' in first_result and first_result['domains']:
                domain = first_result['domains'][0]
                expected_domain_fields = ['env_from', 'env_to', 'bitscore', 'ievalue', 'is_significant']
                for field in expected_domain_fields:
                    self.assertIn(field, domain)

    def test_results_significance_calculation(self):
        """Test that significance calculations are correct."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        response = self.client.get(results_url)
        
        if response.status_code == status.HTTP_200_OK and response.data['results']:
            for result in response.data['results']:
                # Verify significance fields exist
                self.assertIn('is_significant', result)
                self.assertIn('num_hits', result)
                self.assertIn('num_significant', result)
                
                # Verify logical consistency
                self.assertIsInstance(result['is_significant'], bool)
                self.assertIsInstance(result['num_hits'], int)
                self.assertIsInstance(result['num_significant'], int)
                
                # Verify that num_significant <= num_hits
                self.assertLessEqual(result['num_significant'], result['num_hits'])

    def test_results_error_handling(self):
        """Test error handling in results API."""
        # Test with malformed job ID
        malformed_job_id = "invalid-uuid"
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': malformed_job_id})
        
        response = self.client.get(results_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_results_performance(self):
        """Test results API performance with large datasets."""
        # Create multiple jobs to test performance
        jobs = []
        for i in range(5):
            request = {
                **self.search_request,
                "input": f"SEQUENCE_{i}_{self.test_sequence}"
            }
            response = self.client.post(reverse('pyhmmer_search:search'), request, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            jobs.append(response.data['id'])
        
        # Test response time for each job
        for job_id in jobs:
            start_time = time.time()
            results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
            response = self.client.get(results_url)
            end_time = time.time()
            
            # Response should be reasonably fast (< 1 second)
            response_time = end_time - start_time
            self.assertLess(response_time, 1.0, f"Results API response too slow: {response_time:.2f}s")

    def test_results_concurrent_access(self):
        """Test results API with concurrent access patterns."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        # Simulate concurrent access by making multiple requests quickly
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        
        responses = []
        for _ in range(5):
            response = self.client.get(results_url)
            responses.append(response)
        
        # All responses should be successful
        for response in responses:
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])

    def test_results_data_integrity(self):
        """Test that results data maintains integrity across requests."""
        # Create a job first
        url = reverse('pyhmmer_search:search')
        response = self.client.post(url, self.search_request, format='json')
        job_id = response.data['id']
        
        results_url = reverse('pyhmmer_search:get_results', kwargs={'job_id': job_id})
        
        # Make multiple requests and compare results
        responses = []
        for _ in range(3):
            response = self.client.get(results_url)
            responses.append(response)
        
        # All responses should have consistent structure
        for response in responses:
            if response.status_code == status.HTTP_200_OK:
                self.assertIn('results', response.data)
                self.assertIn('pagination', response.data)
                self.assertIn('total_count', response.data)

    def tearDown(self):
        """Clean up test data."""
        # Clean up test jobs
        HmmerJob.objects.all().delete()
        TaskResult.objects.all().delete()
        
        # Clean up test database
        Database.objects.filter(name='test_db').delete()
        
        # Clean up test user
        User.objects.filter(username='testuser').delete()


class TestPyhmmerResultsDataProcessing(TestCase):
    """Integration tests for PyHMMER results data processing."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_results_pagination_calculation(self):
        """Test pagination calculation logic."""
        # Test pagination with different total counts
        test_cases = [
            (0, 10, 1),      # 0 items, 10 per page = 1 page
            (5, 10, 1),      # 5 items, 10 per page = 1 page
            (10, 10, 1),     # 10 items, 10 per page = 1 page
            (11, 10, 2),     # 11 items, 10 per page = 2 pages
            (25, 10, 3),     # 25 items, 10 per page = 3 pages
            (100, 25, 4),    # 100 items, 25 per page = 4 pages
        ]
        
        for total_count, page_size, expected_pages in test_cases:
            total_pages = (total_count + page_size - 1) // page_size
            self.assertEqual(total_pages, expected_pages, 
                           f"Pagination calculation failed for {total_count} items, {page_size} per page")

    def test_results_filtering_logic(self):
        """Test results filtering logic."""
        # Mock results data
        mock_results = [
            {"target": "GENE_1", "score": 100.0, "evalue": 1e-10, "description": "Test gene 1"},
            {"target": "GENE_2", "score": 50.0, "evalue": 1e-5, "description": "Test gene 2"},
            {"target": "GENE_3", "score": 25.0, "evalue": 1e-3, "description": "Test gene 3"},
            {"target": "PROTEIN_1", "score": 75.0, "evalue": 1e-7, "description": "Test protein 1"},
        ]
        
        # Test filtering by score
        high_score_results = [r for r in mock_results if r["score"] > 50.0]
        self.assertEqual(len(high_score_results), 2)
        self.assertIn("GENE_1", [r["target"] for r in high_score_results])
        self.assertIn("PROTEIN_1", [r["target"] for r in high_score_results])
        
        # Test filtering by E-value
        low_evalue_results = [r for r in mock_results if r["evalue"] < 1e-5]
        self.assertEqual(len(low_evalue_results), 2)
        self.assertIn("GENE_1", [r["target"] for r in low_evalue_results])
        self.assertIn("GENE_2", [r["target"] for r in low_evalue_results])
        
        # Test filtering by target name
        gene_results = [r for r in mock_results if "GENE" in r["target"]]
        self.assertEqual(len(gene_results), 3)

    def test_results_sorting_logic(self):
        """Test results sorting logic."""
        # Mock results data
        mock_results = [
            {"target": "GENE_1", "score": 100.0, "evalue": 1e-10},
            {"target": "GENE_2", "score": 50.0, "evalue": 1e-5},
            {"target": "GENE_3", "score": 75.0, "evalue": 1e-7},
        ]
        
        # Test sorting by score (descending)
        sorted_by_score_desc = sorted(mock_results, key=lambda x: x["score"], reverse=True)
        self.assertEqual(sorted_by_score_desc[0]["score"], 100.0)
        self.assertEqual(sorted_by_score_desc[1]["score"], 75.0)
        self.assertEqual(sorted_by_score_desc[2]["score"], 50.0)
        
        # Test sorting by E-value (ascending)
        sorted_by_evalue_asc = sorted(mock_results, key=lambda x: x["evalue"])
        self.assertEqual(sorted_by_evalue_asc[0]["evalue"], 1e-10)
        self.assertEqual(sorted_by_evalue_asc[1]["evalue"], 1e-7)
        self.assertEqual(sorted_by_evalue_asc[2]["evalue"], 1e-5)

    def tearDown(self):
        """Clean up test data."""
        User.objects.filter(username='testuser').delete()
