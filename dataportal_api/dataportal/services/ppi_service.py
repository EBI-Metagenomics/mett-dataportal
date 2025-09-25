import logging
from typing import List, Dict, Any, Optional, Tuple

from elasticsearch_dsl import Search

from dataportal.models.interactions import ProteinProteinDocument
from dataportal.schema.ppi_schemas import (
    PPIInteractionSchema,
    PPISearchQuerySchema,
    PPINetworkSchema,
    PPINetworkPropertiesSchema,
    PPINeighborhoodSchema,
    PPIPaginationSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import ES_INDEX_PPI
from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)


class PPIService(BaseService[PPIInteractionSchema, Dict[str, Any]]):
    """Service for protein-protein interaction data operations."""

    def __init__(self):
        super().__init__(ES_INDEX_PPI)
        self.document_class = ProteinProteinDocument

    async def get_by_id(self, id: str) -> Optional[PPIInteractionSchema]:
        """ Not Implemented."""
        raise NotImplementedError("get_all not implemented for PPI - use search methods instead")

    async def get_all(self, **kwargs) -> List[PPIInteractionSchema]:
        """ Not Implemented."""
        raise NotImplementedError("get_all not implemented for PPI - use search methods instead")

    async def search(self, query: Dict[str, Any]) -> List[PPIInteractionSchema]:
        """ Not Implemented."""
        raise NotImplementedError("search not implemented for PPI - use specific search methods instead")

    async def search_interactions(self, query: PPISearchQuerySchema) -> PPIPaginationSchema:
        """Search for PPI interactions based on query parameters."""
        try:
            s = Search(index=self.index_name)
            
            # Apply filters
            if query.species_acronym:
                s = s.filter("term", species_acronym=query.species_acronym)
            
            if query.isolate_name:
                s = s.filter("term", isolate_name=query.isolate_name)
            
            if query.protein_id:
                s = s.filter("terms", participants=[query.protein_id])
            
            if query.has_xlms is not None:
                s = s.filter("term", has_xlms=query.has_xlms)
            
            if query.has_string is not None:
                s = s.filter("term", has_string=query.has_string)
            
            if query.has_operon is not None:
                s = s.filter("term", has_operon=query.has_operon)
            
            if query.has_ecocyc is not None:
                s = s.filter("term", has_ecocyc=query.has_ecocyc)
            
            if query.has_experimental is not None:
                s = s.filter("term", has_experimental=query.has_experimental)
            
            if query.confidence_bin:
                s = s.filter("term", confidence_bin=query.confidence_bin)
            
            # Score filtering
            if query.score_type and query.score_threshold is not None:
                score_field = f"{query.score_type}_score"
                s = s.filter("range", **{score_field: {"gte": query.score_threshold}})
            
            # Get total count before pagination
            total = s.count()
            
            # Apply pagination
            offset = (query.page - 1) * query.per_page
            s = s[offset:offset + query.per_page]
            
            # Execute search
            response = await self._execute_search(s)
            
            # Convert to schema objects
            interactions = []
            for hit in response.hits:
                interaction_data = self._hit_to_dict(hit)
                interactions.append(PPIInteractionSchema(**interaction_data))
            
            # Calculate pagination metadata
            num_pages = (total + query.per_page - 1) // query.per_page
            has_previous = query.page > 1
            has_next = query.page < num_pages
            
            return PPIPaginationSchema(
                results=interactions,
                page_number=query.page,
                num_pages=num_pages,
                has_previous=has_previous,
                has_next=has_next,
                total_results=total
            )
            
        except Exception as e:
            logger.error(f"Error searching PPI interactions: {e}")
            raise ServiceError(f"Failed to search PPI interactions: {str(e)}")

    async def get_network_data(self, score_type: str, score_threshold: float,
                               species_acronym: Optional[str] = None) -> PPINetworkSchema:
        """Get network data for a specific score type and threshold."""
        try:
            s = Search(index=self.index_name)

            # Apply species filter
            if species_acronym:
                s = s.filter("term", species_acronym=species_acronym)

            # Apply score filter
            score_field = f"{score_type}_score"
            s = s.filter("range", **{score_field: {"gte": score_threshold}})

            # Get all matching interactions
            s = s.source([
                "protein_a", "protein_b", f"{score_field}",
                "protein_a_locus_tag", "protein_a_name", "protein_a_product",
                "protein_b_locus_tag", "protein_b_name", "protein_b_product"
            ])

            response = await self._execute_search(s)

            # Build network data
            nodes = set()
            edges = []

            for hit in response.hits:
                protein_a = hit.protein_a
                protein_b = hit.protein_b
                score = getattr(hit, score_field, 0)

                # Add nodes
                nodes.add(protein_a)
                nodes.add(protein_b)

                # Add edge
                edges.append({
                    "source": protein_a,
                    "target": protein_b,
                    "weight": score
                })

            # Convert nodes to list with metadata
            node_list = []
            for node in nodes:
                node_list.append({
                    "id": node,
                    "label": node
                })

            return PPINetworkSchema(
                nodes=node_list,
                edges=edges,
                properties={}
            )

        except Exception as e:
            logger.error(f"Error getting network data: {e}")
            raise ServiceError(f"Failed to get network data: {str(e)}")

    async def get_network_properties(self, score_type: str, score_threshold: float,
                                     species_acronym: Optional[str] = None) -> PPINetworkPropertiesSchema:
        """Get network properties for a specific score type and threshold."""
        try:
            # Get network data first
            network_data = await self.get_network_data(score_type, score_threshold, species_acronym)

            # Calculate properties
            num_nodes = len(network_data.nodes)
            num_edges = len(network_data.edges)

            # Calculate density (for undirected graph)
            if num_nodes > 1:
                max_possible_edges = num_nodes * (num_nodes - 1) / 2
                density = num_edges / max_possible_edges if max_possible_edges > 0 else 0
            else:
                density = 0

            # Calculate degree distribution
            degree_count = {}
            for edge in network_data.edges:
                source = edge["source"]
                target = edge["target"]
                degree_count[source] = degree_count.get(source, 0) + 1
                degree_count[target] = degree_count.get(target, 0) + 1

            degree_distribution = list(degree_count.values())

            # Calculate average clustering coefficient (simplified)
            # This is a basic implementation - for production, consider using NetworkX
            avg_clustering = 0.0
            if degree_distribution:
                # Simple approximation based on degree distribution
                avg_degree = sum(degree_distribution) / len(degree_distribution)
                avg_clustering = min(avg_degree / (num_nodes - 1), 1.0) if num_nodes > 1 else 0

            return PPINetworkPropertiesSchema(
                num_nodes=num_nodes,
                num_edges=num_edges,
                density=density,
                avg_clustering_coefficient=avg_clustering,
                degree_distribution=degree_distribution
            )

        except Exception as e:
            logger.error(f"Error calculating network properties: {e}")
            raise ServiceError(f"Failed to calculate network properties: {str(e)}")

    async def get_protein_neighborhood(self, protein_id: str, n: int = 5,
                                       species_acronym: Optional[str] = None) -> PPINeighborhoodSchema:
        """Get neighborhood data for a specific protein."""
        try:
            s = Search(index=self.index_name)

            # Filter by protein
            s = s.filter("terms", participants=[protein_id])

            # Apply species filter
            if species_acronym:
                s = s.filter("term", species_acronym=species_acronym)

            # Get all interactions for this protein
            s = s.source([
                "protein_a", "protein_b", "ds_score", "string_score", "melt_score",
                "protein_a_locus_tag", "protein_a_name", "protein_a_product",
                "protein_b_locus_tag", "protein_b_name", "protein_b_product"
            ])

            response = await self._execute_search(s)

            # Build neighborhood data
            neighbors = set()
            edges = []

            for hit in response.hits:
                protein_a = hit.protein_a
                protein_b = hit.protein_b

                # Determine which is the neighbor
                if protein_a == protein_id:
                    neighbor = protein_b
                else:
                    neighbor = protein_a

                neighbors.add(neighbor)

                # Add edge
                edges.append({
                    "source": protein_id,
                    "target": neighbor,
                    "weight": hit.ds_score or 0
                })

            # Convert neighbors to list with metadata
            neighbor_list = []
            for neighbor in list(neighbors)[:n]:  # Limit to n neighbors
                neighbor_list.append({
                    "id": neighbor,
                    "label": neighbor
                })

            # Create network data for the neighborhood
            network_data = PPINetworkSchema(
                nodes=[{"id": protein_id, "label": protein_id}] + neighbor_list,
                edges=edges,
                properties={}
            )

            return PPINeighborhoodSchema(
                protein_id=protein_id,
                neighbors=neighbor_list,
                network_data=network_data
            )

        except Exception as e:
            logger.error(f"Error getting protein neighborhood: {e}")
            raise ServiceError(f"Failed to get protein neighborhood: {str(e)}")

    def _hit_to_dict(self, hit) -> Dict[str, Any]:
        """Convert Elasticsearch hit to dictionary."""
        return {
            "pair_id": hit.pair_id,
            "species_scientific_name": getattr(hit, "species_scientific_name", None),
            "species_acronym": getattr(hit, "species_acronym", None),
            "isolate_name": getattr(hit, "isolate_name", None),
            "protein_a": hit.protein_a,
            "protein_b": hit.protein_b,
            "participants": getattr(hit, "participants", []),
            "is_self_interaction": getattr(hit, "is_self_interaction", False),

            # Protein A info
            "protein_a_locus_tag": getattr(hit, "protein_a_locus_tag", None),
            "protein_a_uniprot_id": getattr(hit, "protein_a_uniprot_id", None),
            "protein_a_name": getattr(hit, "protein_a_name", None),
            "protein_a_product": getattr(hit, "protein_a_product", None),

            # Protein B info
            "protein_b_locus_tag": getattr(hit, "protein_b_locus_tag", None),
            "protein_b_uniprot_id": getattr(hit, "protein_b_uniprot_id", None),
            "protein_b_name": getattr(hit, "protein_b_name", None),
            "protein_b_product": getattr(hit, "protein_b_product", None),

            # Scores
            "dl_score": getattr(hit, "dl_score", None),
            "comelt_score": getattr(hit, "comelt_score", None),
            "perturbation_score": getattr(hit, "perturbation_score", None),
            "abundance_score": getattr(hit, "abundance_score", None),
            "melt_score": getattr(hit, "melt_score", None),
            "secondary_score": getattr(hit, "secondary_score", None),
            "bayesian_score": getattr(hit, "bayesian_score", None),
            "string_score": getattr(hit, "string_score", None),
            "operon_score": getattr(hit, "operon_score", None),
            "ecocyc_score": getattr(hit, "ecocyc_score", None),
            "tt_score": getattr(hit, "tt_score", None),
            "ds_score": getattr(hit, "ds_score", None),

            # Evidence flags
            "has_xlms": getattr(hit, "has_xlms", False),
            "has_string": getattr(hit, "has_string", False),
            "has_operon": getattr(hit, "has_operon", False),
            "has_ecocyc": getattr(hit, "has_ecocyc", False),
            "has_experimental": getattr(hit, "has_experimental", False),

            # Metadata
            "evidence_count": getattr(hit, "evidence_count", 0),
            "confidence_bin": getattr(hit, "confidence_bin", None),
        }
