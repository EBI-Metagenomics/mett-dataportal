#!/usr/bin/env python3
"""
Generate CURL commands for testing PPI API endpoints.
This script creates various test scenarios and outputs the corresponding CURL commands.
"""

from typing import List, Dict, Any

API_BASE_URL = "http://localhost:8000/api"


class CURLGenerator:
    """Generate CURL commands for PPI API testing."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def generate_curl(
        self, endpoint: str, params: Dict[str, Any] = None, method: str = "GET"
    ) -> str:
        """Generate a CURL command for the given endpoint and parameters."""
        url = f"{self.base_url}{endpoint}"

        if params:
            param_string = "&".join(
                [f"{k}={v}" for k, v in params.items() if v is not None]
            )
            url = f"{url}?{param_string}"

        curl_cmd = f'curl -X {method} "{url}"'
        return curl_cmd

    def generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate various test scenarios for PPI API."""
        scenarios = [
            # Basic health check
            {
                "name": "Health Check",
                "endpoint": "/health/",
                "params": None,
                "description": "Basic health check endpoint",
            },
            # Available score types
            {
                "name": "Available Score Types",
                "endpoint": "/ppi/scores/available",
                "params": None,
                "description": "Get list of available score types",
            },
            # Basic interactions
            {
                "name": "Basic Interactions (Default)",
                "endpoint": "/ppi/interactions",
                "params": None,
                "description": "Get interactions with default parameters",
            },
            # Species filtering
            {
                "name": "PV Species Interactions",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "PV"},
                "description": "Get interactions for Phocaeicola vulgatus",
            },
            {
                "name": "BU Species Interactions",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "BU"},
                "description": "Get interactions for Bacteroides uniformis",
            },
            # Score filtering
            {
                "name": "DS Score >= 0.8",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "ds_score",
                    "score_threshold": 0.8,
                },
                "description": "Get interactions with DS score >= 0.8",
            },
            {
                "name": "String Score >= 0.7",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "string_score",
                    "score_threshold": 0.7,
                },
                "description": "Get interactions with String score >= 0.7",
            },
            {
                "name": "Melt Score >= 0.9",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "melt_score",
                    "score_threshold": 0.9,
                },
                "description": "Get interactions with Melt score >= 0.9",
            },
            # Evidence filtering
            {
                "name": "XL-MS Evidence",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "PV", "has_xlms": True},
                "description": "Get interactions with XL-MS evidence",
            },
            {
                "name": "STRING Evidence",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "PV", "has_string": True},
                "description": "Get interactions with STRING evidence",
            },
            {
                "name": "Experimental Evidence",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "PV", "has_xlms": True},
                "description": "Get interactions with experimental evidence",
            },
            # Score filtering
            {
                "name": "High Score",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "ds_score",
                    "score_threshold": 0.8,
                },
                "description": "Get high score interactions",
            },
            {
                "name": "Medium Score",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "ds_score",
                    "score_threshold": 0.5,
                },
                "description": "Get medium score interactions",
            },
            # Pagination
            {
                "name": "Pagination - Page 1",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "PV", "page": 1, "per_page": 10},
                "description": "Get first page with 10 results",
            },
            {
                "name": "Pagination - Page 2",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "PV", "page": 2, "per_page": 5},
                "description": "Get second page with 5 results",
            },
            # Network properties
            {
                "name": "Network Properties - DS Score",
                "endpoint": "/ppi/network-properties",
                "params": {
                    "score_type": "ds_score",
                    "score_threshold": 0.8,
                    "species_acronym": "PV",
                },
                "description": "Get network properties for DS score network",
            },
            {
                "name": "Network Properties - String Score",
                "endpoint": "/ppi/network-properties",
                "params": {
                    "score_type": "string_score",
                    "score_threshold": 0.7,
                    "species_acronym": "PV",
                },
                "description": "Get network properties for String score network",
            },
            # Network data
            {
                "name": "Network Data - DS Score",
                "endpoint": "/ppi/network/ds_score",
                "params": {"score_threshold": 0.8, "species_acronym": "PV"},
                "description": "Get network data for DS score network",
            },
            {
                "name": "Network Data - String Score",
                "endpoint": "/ppi/network/string_score",
                "params": {"score_threshold": 0.7, "species_acronym": "PV"},
                "description": "Get network data for String score network",
            },
            # Protein neighborhood
            {
                "name": "Protein Neighborhood - A6KXK8",
                "endpoint": "/ppi/neighborhood/A6KXK8",
                "params": {"n": 5, "species_acronym": "PV"},
                "description": "Get neighborhood for protein A6KXK8",
            },
            # Complex filtering
            {
                "name": "Complex Filter - High Confidence + String",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "ds_score",
                    "score_threshold": 0.8,
                    "has_string": True,
                },
                "description": "Get high confidence interactions with STRING evidence",
            },
            {
                "name": "Complex Filter - Experimental + XL-MS",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "has_xlms": True,
                    "has_string": True,
                },
                "description": "Get interactions with both experimental and XL-MS evidence",
            },
            # Error cases
            {
                "name": "Error - Invalid Species",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "INVALID"},
                "description": "Test error handling with invalid species",
            },
            {
                "name": "Error - Invalid Score Type",
                "endpoint": "/ppi/network-properties",
                "params": {
                    "score_type": "invalid_score",
                    "score_threshold": 0.8,
                    "species_acronym": "PV",
                },
                "description": "Test error handling with invalid score type",
            },
            {
                "name": "Error - Invalid Protein",
                "endpoint": "/ppi/neighborhood/INVALID_PROTEIN",
                "params": {"n": 5, "species_acronym": "PV"},
                "description": "Test error handling with invalid protein ID",
            },
            # Performance tests
            {
                "name": "Performance - Large Page",
                "endpoint": "/ppi/interactions",
                "params": {"species_acronym": "PV", "per_page": 1000},
                "description": "Test performance with large page size",
            },
            {
                "name": "Performance - High Threshold",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "ds_score",
                    "score_threshold": 0.99,
                },
                "description": "Test performance with high score threshold (few results)",
            },
            {
                "name": "Performance - Low Threshold",
                "endpoint": "/ppi/interactions",
                "params": {
                    "species_acronym": "PV",
                    "score_type": "ds_score",
                    "score_threshold": 0.1,
                },
                "description": "Test performance with low score threshold (many results)",
            },
        ]

        return scenarios

    def print_curl_commands(self):
        """Print all CURL commands for testing."""
        scenarios = self.generate_test_scenarios()

        print("PPI API CURL Test Commands")
        print("=" * 50)
        print(f"Base URL: {self.base_url}")
        print("Make sure the Django server is running: python manage.py runserver")
        print("=" * 50)

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            curl_cmd = self.generate_curl(scenario["endpoint"], scenario["params"])
            print(f"   Command: {curl_cmd}")

            # Add pretty print suggestion
            print(f"   Pretty print: {curl_cmd} | jq '.'")
            print("-" * 50)

    def generate_test_script(self, filename: str = "test_ppi_api.sh"):
        """Generate a bash script with all test commands."""
        scenarios = self.generate_test_scenarios()

        with open(filename, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# PPI API Test Script\n")
            f.write("# Generated automatically\n\n")
            f.write('API_BASE_URL="http://localhost:8000/api"\n\n')
            f.write('echo "Testing PPI API endpoints..."\n')
            f.write(
                'echo "Make sure the Django server is running: python manage.py runserver"\n'
            )
            f.write('echo "=" * 50\n\n')

            for i, scenario in enumerate(scenarios, 1):
                f.write(f"# {i}. {scenario['name']}\n")
                f.write(f"# {scenario['description']}\n")
                curl_cmd = self.generate_curl(scenario["endpoint"], scenario["params"])
                f.write(f"echo \"Testing: {scenario['name']}\"\n")
                f.write(f"{curl_cmd}\n")
                f.write('echo ""\n\n')

            f.write('echo "All tests completed!"\n')

        print(f"Test script generated: {filename}")
        print("Make it executable: chmod +x test_ppi_api.sh")
        print("Run it: ./test_ppi_api.sh")


def main():
    """Generate CURL commands and test script."""
    generator = CURLGenerator()

    print("Generating CURL commands...")
    generator.print_curl_commands()

    print("\n" + "=" * 50)
    print("Generating test script...")
    generator.generate_test_script()


if __name__ == "__main__":
    main()
