"""
Pytest configuration and fixtures for PyHMMER integration tests using Django Ninja.

This file provides common fixtures and configuration for all PyHMMER tests.
"""

import pytest
import os
import tempfile
from django.test import TestCase
from django.contrib.auth.models import User
from django_celery_results.models import TaskResult
from ninja.testing import TestClient

from pyhmmer_search.search.models import HmmerJob, Database
from pyhmmer_search.search.api import pyhmmer_router_search


@pytest.fixture
def api_client():
    """Provide a test client for Django Ninja."""
    return TestClient(pyhmmer_router_search)


@pytest.fixture
def authenticated_client():
    """Provide a test client with a test user."""
    client = TestClient(pyhmmer_router_search)
    user = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )
    return client, user


@pytest.fixture
def test_database():
    """Provide a test database for PyHMMER searches."""
    # Create a temporary directory for the test database
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_db')
    
    database = Database.objects.create(
        name='test_db',
        description='Test database for integration tests',
        path=db_path,
        is_active=True
    )
    
    yield database
    
    # Cleanup
    database.delete()
    os.rmdir(temp_dir)


@pytest.fixture
def sample_search_request():
    """Provide a sample search request for testing."""
    return {
        "database": "test_db",
        "threshold": "evalue",
        "threshold_value": 0.01,
        "input": "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
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


@pytest.fixture
def sample_bitscore_request():
    """Provide a sample bit score search request for testing."""
    return {
        "database": "test_db",
        "threshold": "bitscore",
        "threshold_value": 25.0,
        "input": "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
        "E": None,
        "domE": None,
        "incE": None,
        "incdomE": None,
        "T": 20.0,
        "domT": 20.0,
        "incT": 25.0,
        "incdomT": 25.0,
        "popen": 0.02,
        "pextend": 0.4
    }


@pytest.fixture
def test_sequence_data():
    """Provide various test sequence data for testing."""
    return {
        "short": "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY",
        "medium": "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY" * 5,
        "long": "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY" * 100,
        "with_special": "MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY*X",
        "empty": "",
        "whitespace": "   MSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY   "
    }


@pytest.fixture
def mock_pyhmmer_results():
    """Provide mock PyHMMER results for testing."""
    return [
        {
            "target": "BU_GENE_1",
            "description": "Test gene 1",
            "evalue": "1e-10",
            "score": "100.0",
            "num_hits": 3,
            "num_significant": 2,
            "is_significant": True,
            "domains": [
                {
                    "env_from": 1,
                    "env_to": 50,
                    "bitscore": 100.0,
                    "ievalue": 1e-10,
                    "is_significant": True
                },
                {
                    "env_from": 51,
                    "env_to": 100,
                    "bitscore": 75.0,
                    "ievalue": 1e-8,
                    "is_significant": True
                },
                {
                    "env_from": 101,
                    "env_to": 150,
                    "bitscore": 25.0,
                    "ievalue": 1e-3,
                    "is_significant": False
                }
            ]
        },
        {
            "target": "BU_GENE_2",
            "description": "Test gene 2",
            "evalue": "1e-5",
            "score": "50.0",
            "num_hits": 1,
            "num_significant": 1,
            "is_significant": True,
            "domains": [
                {
                    "env_from": 1,
                    "env_to": 100,
                    "bitscore": 50.0,
                    "ievalue": 1e-5,
                    "is_significant": True
                }
            ]
        }
    ]


@pytest.fixture
def test_job_creation(authenticated_client, test_database, sample_search_request):
    """Helper fixture to create a test job."""
    client, user = authenticated_client
    
    # Update the request to use the test database
    request_data = {**sample_search_request}
    request_data["database"] = test_database.name
    
    # Create the job
    response = client.post("", json=request_data)
    
    if response.status_code == 200:
        job_id = response.json()['id']
        job = HmmerJob.objects.get(id=job_id)
        return job, job_id
    else:
        pytest.fail(f"Failed to create test job: {response.json()}")


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically clean up test data after each test."""
    yield
    
    # Only clean up if we're in a test that actually uses the database
    # For basic functionality tests, we don't need to clean up
    try:
        # Check if the tables exist before trying to clean them up
        from django.db import connection
        
        # Try to clean up test jobs if the table exists
        try:
            HmmerJob.objects.all().delete()
        except Exception:
            # Table doesn't exist or other error, skip cleanup
            pass
        
        # Try to clean up task results if the table exists
        try:
            TaskResult.objects.all().delete()
        except Exception:
            # Table doesn't exist or other error, skip cleanup
            pass
        
        # Try to clean up test users if the table exists
        try:
            User.objects.filter(username='testuser').delete()
        except Exception:
            # Table doesn't exist or other error, skip cleanup
            pass
        
        # Try to clean up test databases if the table exists
        try:
            Database.objects.filter(name='test_db').delete()
        except Exception:
            # Table doesn't exist or other error, skip cleanup
            pass
            
    except Exception:
        # If any cleanup fails, just continue - this is not critical for basic tests
        pass


# Pytest markers for different test types
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "workflow: marks tests as workflow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark integration tests
        if "integration" in item.name.lower():
            item.add_marker(pytest.mark.integration)
        
        # Mark API tests
        if "api" in item.name.lower():
            item.add_marker(pytest.mark.api)
        
        # Mark workflow tests
        if "workflow" in item.name.lower():
            item.add_marker(pytest.mark.workflow)
        
        # Mark slow tests
        if any(slow_indicator in item.name.lower() for slow_indicator in ["performance", "concurrent", "large"]):
            item.add_marker(pytest.mark.slow)
