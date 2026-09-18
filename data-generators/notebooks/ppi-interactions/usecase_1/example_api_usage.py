#!/usr/bin/env python3
"""
Example script showing how to use the PPI API directly.
This demonstrates the key API endpoints and their usage.
"""

import requests
from typing import Dict, Any

API_BASE_URL = "http://localhost:8000/api"


class PPIClient:
    """Simple client for PPI API endpoints."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """Make GET request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_interactions(
        self,
        species_acronym: str = "PV",
        score_type: str = None,
        score_threshold: float = None,
        page: int = 1,
        per_page: int = 100,
    ) -> Dict:
        """Get PPI interactions."""
        params = {
            "species_acronym": species_acronym,
            "page": page,
            "per_page": per_page,
        }

        if score_type and score_threshold is not None:
            params["score_type"] = score_type
            params["score_threshold"] = score_threshold

        return self._get("/ppi/interactions", params)

    def get_network_properties(
        self, score_type: str, score_threshold: float, species_acronym: str = "PV"
    ) -> Dict:
        """Get network properties."""
        params = {
            "score_type": score_type,
            "score_threshold": score_threshold,
            "species_acronym": species_acronym,
        }
        return self._get("/ppi/network-properties", params)

    def get_network_data(
        self, score_type: str, score_threshold: float, species_acronym: str = "PV"
    ) -> Dict:
        """Get network data."""
        params = {
            "score_type": score_type,
            "score_threshold": score_threshold,
            "species_acronym": species_acronym,
        }
        return self._get(f"/ppi/network/{score_type}", params)

    def get_protein_neighborhood(
        self, protein_id: str, n: int = 5, species_acronym: str = "PV"
    ) -> Dict:
        """Get protein neighborhood."""
        params = {"n": n, "species_acronym": species_acronym}
        return self._get(f"/ppi/neighborhood/{protein_id}", params)

    def get_available_scores(self) -> Dict:
        """Get available score types."""
        return self._get("/ppi/scores/available")


def main():
    """Demonstrate PPI API usage."""
    print("PPI API Usage Examples")
    print("=" * 40)

    client = PPIClient()

    try:
        # 1. Get available score types
        print("1. Available Score Types:")
        scores = client.get_available_scores()
        print(f"   {scores['data']['score_types']}")
        print()

        # 2. Get some interactions
        print("2. Sample PPI Interactions:")
        interactions = client.get_interactions(species_acronym="PV", per_page=5)
        print(f"   Found {interactions['total']} total interactions")
        print(f"   Showing {len(interactions['data'])} interactions:")

        for i, interaction in enumerate(interactions["data"][:3], 1):
            print(f"   {i}. {interaction['protein_a']} <-> {interaction['protein_b']}")
            print(f"      DS Score: {interaction.get('ds_score', 'N/A')}")
            print(f"      String Score: {interaction.get('string_score', 'N/A')}")
        print()

        # 3. Get network properties
        print("3. Network Properties (DS Score >= 0.8):")
        properties = client.get_network_properties("ds_score", 0.8, "PV")
        data = properties["data"]
        print(f"   Nodes: {data['num_nodes']}")
        print(f"   Edges: {data['num_edges']}")
        print(f"   Density: {data['density']:.4f}")
        print(f"   Avg Clustering: {data['avg_clustering_coefficient']:.4f}")
        print()

        # 4. Get network data
        print("4. Network Data (DS Score >= 0.8):")
        network = client.get_network_data("ds_score", 0.8, "PV")
        data = network["data"]
        print(f"   Nodes: {len(data['nodes'])}")
        print(f"   Edges: {len(data['edges'])}")
        print(f"   Sample nodes: {[n['id'] for n in data['nodes'][:5]]}")
        print()

        # 5. Get protein neighborhood (if we have interactions)
        if interactions["data"]:
            protein_id = interactions["data"][0]["protein_a"]
            print(f"5. Neighborhood of {protein_id}:")
            neighborhood = client.get_protein_neighborhood(
                protein_id, n=3, species_acronym="PV"
            )
            data = neighborhood["data"]
            print(f"   Neighbors: {[n['id'] for n in data['neighbors']]}")
            print(f"   Network edges: {len(data['network_data']['edges'])}")

        print("\n✓ All API calls successful!")

    except requests.exceptions.RequestException as e:
        print(f"✗ API request failed: {e}")
        print("Make sure the Django server is running: python manage.py runserver")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    main()
