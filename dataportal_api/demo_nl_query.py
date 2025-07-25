#!/usr/bin/env python3
"""
Simple demonstration of the automated natural language query service.

This script shows how the service automatically converts natural language queries
into API requests and executes them.
"""

import asyncio
import os
import sys

import django
from dataportal.services.nl_query_service import NaturalLanguageQueryService

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dataportal.settings")
django.setup()


async def demo():
    """Demonstrate the natural language query service."""

    service = NaturalLanguageQueryService()

    # Example queries
    queries = [
        "Show essential genes in Bacteroides uniformis",
        "Find genes involved in AMR in PV",
        "Get transport proteins in BU",
    ]

    print("🚀 Natural Language Query Service Demo")
    print("=" * 50)

    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 30)

        try:
            result = await service.interpret_and_execute_query(query)

            if result.get("success"):
                print("✅ Success!")
                print(f"🔍 Interpreted as: {result['interpreted_query']}")
                print(f"🔧 API method: {result['api_parameters']['method']}")
                print(f"📊 Results: {result['results']['total_results']} found")
            else:
                print(f"❌ Error: {result.get('error')}")

        except Exception as e:
            print(f"❌ Exception: {e}")


if __name__ == "__main__":
    asyncio.run(demo())
