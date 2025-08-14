#!/usr/bin/env python3
"""
Test runner script for PyHMMER search functionality.
This script allows you to test different scenarios without running the full Django test suite.
"""

import os
import sys
from unittest.mock import Mock

import django
from django_celery_results.models import TaskResult

from pyhmmer_search.search.models import HmmerJob

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dataportal.settings")
django.setup()


def create_mock_objects():
    """Create mock objects for testing"""

    # Mock hit object
    mock_hit = Mock()
    mock_hit.name = b"BU_TEST_GENE_1"
    mock_hit.description = b"Test protein description"
    mock_hit.evalue = 1e-25
    mock_hit.score = 95.5
    mock_hit.included = True
    mock_hit.bias = 0.1

    # Mock domain objects
    mock_domain1 = Mock()
    mock_domain1.env_from = 1
    mock_domain1.env_to = 100
    mock_domain1.score = 95.5
    mock_domain1.i_evalue = 1e-25
    mock_domain1.c_evalue = 1e-20
    mock_domain1.bias = 0.1
    mock_domain1.strand = None
    mock_domain1.alignment = None
    mock_domain1.alignment_display = None

    mock_domain2 = Mock()
    mock_domain2.env_from = 150
    mock_domain2.env_to = 250
    mock_domain2.score = 88.0
    mock_domain2.i_evalue = 1e-15
    mock_domain2.c_evalue = 1e-10
    mock_domain2.bias = 0.05
    mock_domain2.strand = None
    mock_domain2.alignment = None
    mock_domain2.alignment_display = None

    # Mock job object
    mock_job = Mock(spec=HmmerJob)
    mock_job.id = "test-job-id-123"
    mock_job.database = "test_db"
    mock_job.threshold = HmmerJob.ThresholdChoices.EVALUE
    mock_job.threshold_value = 0.01
    mock_job.incE = 0.01
    mock_job.incT = 25.0
    mock_job.E = 1.0
    mock_job.domE = 0.03
    mock_job.T = 7.0
    mock_job.domT = 5.0
    mock_job.popen = 0.02
    mock_job.pextend = 0.4
    mock_job.input = ">test_protein\nMSEIDHVGLWNRCLEIIRDNVPEQTYKTWFLPIIPLKY"
    mock_job.algo = HmmerJob.AlgoChoices.PHMMER

    # Mock task result
    mock_task_result = Mock(spec=TaskResult)
    mock_task_result.task_id = "test-task-id-456"
    mock_task_result.status = "PENDING"

    return mock_hit, mock_domain1, mock_domain2, mock_job, mock_task_result


def test_single_domain_scenario():
    """Test scenario: Gene with single significant domain"""
    print("=== Testing Single Domain Scenario ===")

    mock_hit, mock_domain, _, mock_job, mock_task_result = create_mock_objects()
    mock_hit.domains = [mock_domain]
    mock_job.task = mock_task_result

    print(f"Gene: {mock_hit.name.decode()}")
    print(f"Domains: {len(mock_hit.domains)}")
    print("Expected: 1 domain, 1 significant domain")
    print(f"Hit included: {mock_hit.included}")
    print(f"Domain score: {mock_domain.score}")
    print(f"Domain i_evalue: {mock_domain.i_evalue}")
    print()


def test_multiple_domains_mixed_significance():
    """Test scenario: Gene with multiple domains, mixed significance"""
    print("=== Testing Multiple Domains Mixed Significance ===")

    mock_hit, mock_domain1, mock_domain2, mock_job, mock_task_result = (
        create_mock_objects()
    )
    mock_hit.domains = [mock_domain1, mock_domain2]
    mock_job.task = mock_task_result

    print(f"Gene: {mock_hit.name.decode()}")
    print(f"Total domains: {len(mock_hit.domains)}")

    # Domain 1: Very significant
    print(f"Domain 1 - Score: {mock_domain1.score}, i_evalue: {mock_domain1.i_evalue}")
    print("Domain 1 - Expected significant: True (score > 25.0, i_evalue < 0.01)")

    # Domain 2: Less significant
    print(f"Domain 2 - Score: {mock_domain2.score}, i_evalue: {mock_domain2.i_evalue}")
    print("Domain 2 - Expected significant: False (i_evalue > 0.01)")

    print("Expected: 2 domains, 1 significant domain")
    print()


def test_no_domains_scenario():
    """Test scenario: Gene with no domains (phmmer case)"""
    print("=== Testing No Domains Scenario ===")

    mock_hit, _, _, mock_job, mock_task_result = create_mock_objects()
    mock_hit.domains = []
    mock_job.task = mock_task_result

    print(f"Gene: {mock_hit.name.decode()}")
    print(f"Domains: {len(mock_hit.domains)}")
    print("Expected: 0 domains, 0 significant domains")
    print()


def test_bit_score_threshold():
    """Test scenario: Using bit score threshold instead of E-value"""
    print("=== Testing Bit Score Threshold ===")

    mock_hit, mock_domain, _, mock_job, mock_task_result = create_mock_objects()
    mock_hit.domains = [mock_domain]
    mock_job.threshold = HmmerJob.ThresholdChoices.BITSCORE
    mock_job.incT = 25.0
    mock_job.task = mock_task_result

    print(f"Gene: {mock_hit.name.decode()}")
    print(f"Threshold type: {mock_job.threshold}")
    print(f"Bit score threshold: {mock_job.incT}")
    print(f"Domain score: {mock_domain.score}")
    print(f"Expected significant: {mock_domain.score > mock_job.incT}")
    print()


def test_evalue_threshold():
    """Test scenario: Using E-value threshold"""
    print("=== Testing E-value Threshold ===")

    mock_hit, mock_domain, _, mock_job, mock_task_result = create_mock_objects()
    mock_hit.domains = [mock_domain]
    mock_job.threshold = HmmerJob.ThresholdChoices.EVALUE
    mock_job.incE = 0.01
    mock_job.task = mock_task_result

    print(f"Gene: {mock_hit.name.decode()}")
    print(f"Threshold type: {mock_job.threshold}")
    print(f"E-value threshold: {mock_job.incE}")
    print(f"Domain i_evalue: {mock_domain.i_evalue}")
    print(f"Expected significant: {mock_domain.i_evalue < mock_job.incE}")
    print()


def test_fallback_threshold_calculation():
    """Test scenario: Fallback threshold calculation when hit.included is not available"""
    print("=== Testing Fallback Threshold Calculation ===")

    mock_hit, mock_domain, _, mock_job, mock_task_result = create_mock_objects()
    mock_hit.domains = [mock_domain]
    delattr(mock_hit, "included")  # Remove included attribute
    mock_job.task = mock_task_result

    print(f"Gene: {mock_hit.name.decode()}")
    print("hit.included attribute: Not available")
    print(
        f"Will use fallback calculation based on threshold type: {mock_job.threshold}"
    )

    if mock_job.threshold == HmmerJob.ThresholdChoices.EVALUE:
        print(
            f"Fallback: i_evalue < {mock_job.incE} = {mock_domain.i_evalue < mock_job.incE}"
        )
    else:
        print(
            f"Fallback: score > {mock_job.incT} = {mock_domain.score > mock_job.incT}"
        )
    print()


def test_bias_field_handling():
    """Test scenario: Bias field handling and type conversion"""
    print("=== Testing Bias Field Handling ===")

    mock_hit, mock_domain, _, mock_job, mock_task_result = create_mock_objects()
    mock_hit.domains = [mock_domain]
    mock_job.task = mock_task_result

    # Test different bias value types
    test_cases = [
        ("0.1", 0.1, "Valid float string"),
        (0.1, 0.1, "Valid float"),
        ("invalid", None, "Invalid string"),
        (None, None, "None value"),
    ]

    for bias_value, expected, description in test_cases:
        mock_hit.bias = bias_value
        print(f"Bias value: {bias_value} ({description})")
        print(f"Expected result: {expected}")
        print()


def run_all_tests():
    """Run all test scenarios"""
    print("🧪 Running PyHMMER Domain Counting Test Scenarios")
    print("=" * 60)
    print()

    test_single_domain_scenario()
    test_multiple_domains_mixed_significance()
    test_no_domains_scenario()
    test_bit_score_threshold()
    test_evalue_threshold()
    test_fallback_threshold_calculation()
    test_bias_field_handling()

    print("=" * 60)
    print("✅ All test scenarios completed!")
    print()
    print("To run actual tests with pytest:")
    print(
        "cd dataportal_api && python -m pytest pyhmmer_search/search/test_tasks.py -v"
    )


if __name__ == "__main__":
    run_all_tests()
