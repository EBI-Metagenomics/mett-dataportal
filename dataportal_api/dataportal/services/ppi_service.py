import logging
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
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
from dataportal.utils.constants import ES_INDEX_PPI, PPI_VALID_FILTER_FIELDS, PPI_SCORE_FIELDS
from dataportal.utils.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)


class PPIService(BaseService[PPIInteractionSchema, Dict[str, Any]]):
    """Service for protein-protein interaction data operations."""

    def __init__(self):
        super().__init__(ES_INDEX_PPI)
        self.document_class = ProteinProteinDocument

    def _validate_and_normalize_score_field(self, score_type: str) -> str:
        """
        Validate and normalize the score field name.
        
        Args:
            score_type: The score type provided by the user
            
        Returns:
            The normalized field name for Elasticsearch
            
        Raises:
            ValidationError: If the score_type is not valid
        """
        if not score_type:
            raise ValidationError("Score type cannot be empty")
            
        # If it's already a valid field, use it as-is
        if score_type in PPI_VALID_FILTER_FIELDS:
            return score_type
            
        # If it ends with _score, check if it's a valid score field
        if score_type.endswith('_score'):
            if score_type in PPI_SCORE_FIELDS:
                return score_type
            else:
                raise ValidationError(f"Invalid score field: {score_type}. Valid score fields: {PPI_SCORE_FIELDS}")
        
        # Try to construct the score field name
        constructed_field = f"{score_type}_score"
        if constructed_field in PPI_SCORE_FIELDS:
            return constructed_field
            
        # If none of the above work, it's invalid
        raise ValidationError(
            f"Invalid score type: {score_type}. "
            f"Valid fields are: {PPI_VALID_FILTER_FIELDS}. "
            f"For score fields, you can use the base name (e.g., 'ds' for 'ds_score') or the full name."
        )

    def _build_networkx_graph(self, network_data: PPINetworkSchema) -> nx.Graph:
        """
        Build a NetworkX graph from network data.
        
        Args:
            network_data: The network data containing nodes and edges
            
        Returns:
            A NetworkX Graph object
        """
        G = nx.Graph()
        
        # Add nodes
        for node in network_data.nodes:
            G.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
        
        # Add edges
        for edge in network_data.edges:
            G.add_edge(
                edge["source"], 
                edge["target"], 
                weight=edge.get("weight", 1.0)
            )
        
        return G

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
            def build_search():
                """Build the search query with all filters."""
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
                    score_field = self._validate_and_normalize_score_field(query.score_type)
                    s = s.filter("range", **{score_field: {"gte": query.score_threshold}})
                
                logger.info(f"Final search query: {s.to_dict()}")
                return s
            
            # Create separate search objects for count and search
            count_search = build_search()
            search_query = build_search()
            
            # Get total count
            from asgiref.sync import sync_to_async
            total = await sync_to_async(count_search.count)()
            
            # Apply pagination to search query
            offset = (query.page - 1) * query.per_page
            search_query = search_query[offset:offset + query.per_page]
            
            # Execute search
            response = await self._execute_search(search_query)
            
            # Convert to schema objects
            interactions = []
            for hit in response.hits:
                try:
                    interaction_data = self._hit_to_dict(hit)
                    interactions.append(PPIInteractionSchema(**interaction_data))
                except Exception as e:
                    logger.error(f"Error converting hit to schema: {e}")
                    logger.error(f"Hit data: {hit.to_dict()}")
                    raise
            
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
            score_field = self._validate_and_normalize_score_field(score_type)
            s = s.filter("range", **{score_field: {"gte": score_threshold}})

            # Get all matching interactions
            # By default Elasticsearch returns only 10 hits; expand to include all matches
            from asgiref.sync import sync_to_async
            total_matches = await sync_to_async(s.count)()
            # Cap to a safe upper bound within ES max_result_window (typically 10k)
            max_fetch = min(total_matches, 10000000)
            s = s[:max_fetch]
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

            # Build NetworkX graph for accurate calculations
            G = self._build_networkx_graph(network_data)

            # Calculate properties using NetworkX
            num_nodes = G.number_of_nodes()
            num_edges = G.number_of_edges()

            # Calculate density using NetworkX
            density = nx.density(G)

            # Calculate degree distribution
            degree_distribution = [d for n, d in G.degree()]

            # Calculate average clustering coefficient using NetworkX
            avg_clustering = nx.average_clustering(G)

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
