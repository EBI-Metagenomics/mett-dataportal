#!/usr/bin/env python3
"""
Test script for the automated natural language query service.

This script demonstrates how the enhanced NL query service can automatically:
1. Interpret natural language queries
2. Map them to appropriate API endpoints
3. Execute the queries and return results

Usage:
    python test_nl_query.py
"""

import asyncio
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dataportal.settings")
django.setup()

from dataportal.services.nl_query_service import NaturalLanguageQueryService


async def test_natural_language_queries():
    """Test various natural language queries."""

    service = NaturalLanguageQueryService()

    # Test queries
    test_queries = [
        "Show essential genes in Bacteroides uniformis",
        "Find genes involved in AMR in PV",
        "Get all transport proteins in BU",
        "Show non-essential genes with COG category J",
        "Find genes with Pfam domain PF00001",
        "Get all genes in PV that are not essential",
        "Show genes with KEGG pathway K00001",
        "Find essential genes that have AMR information",
    ]

    print("🧪 Testing Automated Natural Language Query Service")
    print("=" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)

        try:
            # Execute the query
            result = await service.interpret_and_execute_query(query)

            if result.get("success"):
                print("✅ Query executed successfully!")
                print(f"📊 Original query: {result.get('original_query')}")
                print(f"🔍 Interpreted parameters: {result.get('interpreted_query')}")
                print(
                    f"🔧 API method used: {result.get('api_parameters', {}).get('method')}"
                )
                print(
                    f"📈 Total results: {result.get('results', {}).get('total_results', 0)}"
                )

                # Show a sample of results if available
                results_data = result.get("results", {}).get("data", {})
                if isinstance(results_data, dict) and "results" in results_data:
                    sample_results = results_data["results"][:3]  # Show first 3 results
                    print(f"📋 Sample results ({len(sample_results)} shown):")
                    for j, gene in enumerate(sample_results, 1):
                        print(
                            f"   {j}. {gene.get('locus_tag', 'N/A')} - {gene.get('gene_name', 'N/A')}"
                        )
                elif isinstance(results_data, list) and results_data:
                    sample_results = results_data[:3]
                    print(f"📋 Sample results ({len(sample_results)} shown):")
                    for j, gene in enumerate(sample_results, 1):
                        print(
                            f"   {j}. {gene.get('locus_tag', 'N/A')} - {gene.get('gene_name', 'N/A')}"
                        )
                else:
                    print("📋 No results found")

            else:
                print("❌ Query failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")

        print()


async def test_interpretation_only():
    """Test query interpretation without execution."""

    service = NaturalLanguageQueryService()

    print("\n🔍 Testing Query Interpretation Only")
    print("=" * 40)

    test_query = "Show essential genes in PV with AMR information"

    try:
        # Only interpret the query
        interpreted_query = await service._interpret_query(test_query)

        if "error" not in interpreted_query:
            print(f"📝 Query: {test_query}")
            print(f"🔍 Interpreted: {interpreted_query}")

            # Map to API parameters
            api_params = service._map_to_api_parameters(interpreted_query)
            print(f"🔧 Mapped to API: {api_params}")
        else:
            print(f"❌ Interpretation failed: {interpreted_query['error']}")

    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")


async def main():
    """Main test function."""
    print("🚀 Starting Natural Language Query Service Tests")
    print("=" * 60)

    # Test full query execution
    await test_natural_language_queries()

    # Test interpretation only
    await test_interpretation_only()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
