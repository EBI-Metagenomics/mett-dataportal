import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
from cachetools import TTLCache

import networkx as nx
from elasticsearch_dsl import Search

from dataportal.models.interactions import ProteinProteinDocument
from dataportal.schema.interactions.ppi_schemas import (
    PPIInteractionSchema,
    PPISearchQuerySchema,
    PPINetworkSchema,
    PPINetworkNodeSchema,
    PPINetworkEdgeSchema,
    PPINetworkPropertiesSchema,
    PPINeighborhoodSchema,
    PPIPaginationSchema,
    PPIAllNeighborsSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import INDEX_PPI, PPI_VALID_FILTER_FIELDS, PPI_SCORE_FIELDS
from dataportal.utils.exceptions import ServiceError, ValidationError

logger = logging.getLogger(__name__)


class PPIService(BaseService[PPIInteractionSchema, Dict[str, Any]]):
    """Service for protein-protein interaction data operations."""

    def __init__(self):
        super().__init__(INDEX_PPI)
        self.document_class = ProteinProteinDocument
        # Cache for expensive network calculations
        self._network_cache = TTLCache(maxsize=100, ttl=300)  # 5 minutes

    def _build_base_search(
        self,
        species_acronym: Optional[str] = None,
        isolate_name: Optional[str] = None,
        score_type: Optional[str] = None,
        score_threshold: Optional[float] = None,
    ) -> Search:
        """Build a base search query with common filters."""
        s = Search(index=self.index_name)

        if species_acronym:
            s = s.filter("term", species_acronym=species_acronym)
            logger.debug(f"Applied species_acronym filter: {species_acronym}")

        if isolate_name:
            s = s.filter("term", isolate_name=isolate_name)
            logger.debug(f"Applied isolate_name filter: {isolate_name}")

        if score_type and score_threshold is not None:
            score_field = self._validate_and_normalize_score_field(score_type)
            s = s.filter("range", **{score_field: {"gte": score_threshold}})
            logger.debug(f"Applied score filter: {score_field} >= {score_threshold}")

        return s

    async def resolve_locus_tag_to_protein_id(
        self,
        locus_tag: str,
        species_acronym: Optional[str] = None,
        isolate_name: Optional[str] = None,
    ) -> str:
        """
        Resolve a locus tag to its corresponding protein_id (UniProt ID).

        Args:
            locus_tag: The locus tag to resolve (e.g., 'BU_ATCC8492_01788')
            species_acronym: Optional species filter for faster resolution
            isolate_name: Optional isolate filter (typically not needed since locus_tag is unique)

        Returns:
            The corresponding protein_id (UniProt ID)

        Raises:
            ServiceError: If locus tag is not found or multiple matches exist
        """
        try:
            s = Search(index=self.index_name)

            # Filter by locus tag in either protein_a or protein_b
            s = s.filter(
                "bool",
                should=[
                    {"term": {"protein_a_locus_tag": locus_tag}},
                    {"term": {"protein_b_locus_tag": locus_tag}},
                ],
            )

            if species_acronym:
                s = s.filter("term", species_acronym=species_acronym)

            # Note: We typically don't filter by isolate_name here because:
            # 1. locus_tag already uniquely identifies the gene
            # 2. isolate_name might not be populated in all PPI documents
            # 3. For type strains, PPI data might be shared across isolates

            # Only fetch the protein_id fields we need
            s = s.source(["protein_a", "protein_b", "protein_a_locus_tag", "protein_b_locus_tag"])
            s = s[:1]  # We only need one hit to get the protein_id

            response = await self._execute_search(s)

            if not response.hits:
                raise ServiceError(
                    f"Locus tag '{locus_tag}' not found"
                    + (f" for species '{species_acronym}'" if species_acronym else "")
                )

            # Get the protein_id from the first hit
            hit = response.hits[0]
            if hit.protein_a_locus_tag == locus_tag:
                return hit.protein_a
            elif hit.protein_b_locus_tag == locus_tag:
                return hit.protein_b
            else:
                raise ServiceError(f"Unexpected error resolving locus tag '{locus_tag}'")

        except ServiceError:
            raise
        except Exception as e:
            logger.error(f"Error resolving locus tag '{locus_tag}': {e}")
            raise ServiceError(f"Failed to resolve locus tag '{locus_tag}': {str(e)}")

    def _get_standard_source_fields(self, include_scores: bool = True) -> List[str]:
        """Get standard source fields for PPI queries."""
        base_fields = [
            "pair_id",
            "protein_a",
            "protein_b",
            "protein_a_locus_tag",
            "protein_a_name",
            "protein_a_product",
            "protein_b_locus_tag",
            "protein_b_name",
            "protein_b_product",
            "participants",
            "is_self_interaction",
            "species_scientific_name",
            "species_acronym",
            "isolate_name",
        ]

        if include_scores:
            base_fields.extend(
                [
                    "ds_score",
                    "string_score",
                    "melt_score",
                    "dl_score",
                    "comelt_score",
                    "perturbation_score",
                    "abundance_score",
                    "secondary_score",
                    "bayesian_score",
                    "operon_score",
                    "ecocyc_score",
                    "tt_score",
                    "has_xlms",
                    "has_string",
                    "has_operon",
                    "has_ecocyc",
                    "evidence_count",
                ]
            )

        return base_fields

    @lru_cache(maxsize=50)
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
        if score_type.endswith("_score"):
            if score_type in PPI_SCORE_FIELDS:
                return score_type
            else:
                raise ValidationError(
                    f"Invalid score field: {score_type}. Valid score fields: {PPI_SCORE_FIELDS}"
                )

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
            G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1.0))

        return G

    async def _build_neighborhood_data(
        self,
        protein_id: str,
        nearest_neighbors: List[str],
        gene_mapping: Dict[str, Dict],
        species_acronym: Optional[str] = None,
    ) -> PPINeighborhoodSchema:
        """Helper method to build neighborhood data from neighbors and gene mapping."""
        # Build neighbor list with gene annotations
        neighbor_list = []
        for neighbor in nearest_neighbors:
            gene_info = gene_mapping.get(neighbor, {})
            locus_tag = gene_info.get("locus_tag", neighbor)
            name = gene_info.get("name", "")

            # Create label like old implementation: "locus_tag\nname"
            label = f"{locus_tag}\n{name}" if name else neighbor

            neighbor_list.append(
                {
                    "id": neighbor,
                    "label": label,
                    "locus_tag": locus_tag,
                    "name": name,
                    "product": gene_info.get("product", ""),
                }
            )

        # Create network data for the neighborhood
        network_data = PPINetworkSchema(
            nodes=[{"id": protein_id, "label": protein_id}] + neighbor_list,
            edges=[],  # Will be populated by caller
            properties={},
        )

        return PPINeighborhoodSchema(
            protein_id=protein_id, neighbors=neighbor_list, network_data=network_data
        )

    async def get_by_id(self, id: str) -> Optional[PPIInteractionSchema]:
        """Not Implemented."""
        raise NotImplementedError("get_all not implemented for PPI - use search methods instead")

    async def get_all(self, **kwargs) -> List[PPIInteractionSchema]:
        """Not Implemented."""
        raise NotImplementedError("get_all not implemented for PPI - use search methods instead")

    async def search(self, query: Dict[str, Any]) -> List[PPIInteractionSchema]:
        """Not Implemented."""
        raise NotImplementedError(
            "search not implemented for PPI - use specific search methods instead"
        )

    async def search_interactions(self, query: PPISearchQuerySchema) -> PPIPaginationSchema:
        """Search for PPI interactions based on query parameters."""
        try:
            # Resolve locus_tag to protein_id if needed
            actual_protein_id = query.protein_id
            if query.locus_tag:
                try:
                    actual_protein_id = await self.resolve_locus_tag_to_protein_id(
                        locus_tag=query.locus_tag, species_acronym=query.species_acronym
                    )
                    logger.info(
                        f"Resolved locus tag '{query.locus_tag}' to protein_id '{actual_protein_id}'"
                    )
                except ServiceError as e:
                    logger.error(f"Locus tag resolution error: {e}")
                    raise ServiceError(f"Failed to resolve locus tag '{query.locus_tag}': {str(e)}")

            def build_search():
                """Build the search query with all filters."""
                s = Search(index=self.index_name)

                # Apply filters
                if query.species_acronym:
                    s = s.filter("term", species_acronym=query.species_acronym)

                if query.isolate_name:
                    s = s.filter("term", isolate_name=query.isolate_name)

                if actual_protein_id:
                    s = s.filter("terms", participants=[actual_protein_id])

                if query.has_xlms is not None:
                    s = s.filter("term", has_xlms=query.has_xlms)

                if query.has_string is not None:
                    s = s.filter("term", has_string=query.has_string)

                if query.has_operon is not None:
                    s = s.filter("term", has_operon=query.has_operon)

                if query.has_ecocyc is not None:
                    s = s.filter("term", has_ecocyc=query.has_ecocyc)

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
            search_query = search_query[offset : offset + query.per_page]

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
                total_results=total,
            )

        except Exception as e:
            logger.error(f"Error searching PPI interactions: {e}")
            raise ServiceError(f"Failed to search PPI interactions: {str(e)}")

    async def get_network_data(
        self,
        score_type: str,
        score_threshold: float,
        species_acronym: Optional[str] = None,
        isolate_name: Optional[str] = None,
        locus_tag: Optional[str] = None,
    ) -> PPINetworkSchema:
        """Get network data for a specific score type and threshold (optimized).

        If locus_tag is provided, only returns PPIs involving that gene (neighborhood view).
        This dramatically reduces data size and improves performance.
        """
        try:
            # When locus_tag is provided, skip isolate_name filter because:
            # 1. locus_tag already uniquely identifies the gene
            # 2. isolate_name might not be populated in PPI documents
            # 3. For type strains, PPI data might be shared across isolates
            # 4. This avoids over-filtering that results in no matches
            search_isolate_name = None if locus_tag else isolate_name
            if locus_tag and isolate_name:
                logger.info(
                    "get_network_data: Skipping isolate_name filter when locus_tag is provided (to avoid over-filtering; isolate_name may not be populated in PPI documents)"
                )

            s = self._build_base_search(
                species_acronym, search_isolate_name, score_type, score_threshold
            )

            # If locus_tag is provided, filter to only PPIs involving this gene
            # This creates a neighborhood view and significantly reduces data size
            # Filter directly by locus_tag fields instead of resolving to protein_id
            # to avoid potential mismatches between resolved protein_id and participants field
            if locus_tag:
                logger.info(
                    f"get_network_data: Filtering to PPIs involving locus_tag '{locus_tag}'"
                )
                # Filter to interactions where this locus_tag appears in either protein_a or protein_b
                s = s.filter(
                    "bool",
                    should=[
                        {"term": {"protein_a_locus_tag": locus_tag}},
                        {"term": {"protein_b_locus_tag": locus_tag}},
                    ],
                )

            # Get all matching interactions
            from asgiref.sync import sync_to_async

            total_matches = await sync_to_async(s.count)()
            logger.info(f"get_network_data: Found {total_matches} total matches before limiting")
            logger.info(
                f"get_network_data: Query params - species_acronym={species_acronym}, isolate_name={isolate_name}, locus_tag={locus_tag}, score_type={score_type}, score_threshold={score_threshold}"
            )
            max_fetch = min(total_matches, 10000000)
            s = s[:max_fetch]

            # Use standard source fields
            score_field = self._validate_and_normalize_score_field(score_type)
            source_fields = self._get_standard_source_fields(include_scores=False)
            source_fields.append(score_field)
            s = s.source(source_fields)

            # Log the final query for debugging
            query_dict = s.to_dict()
            logger.info(f"get_network_data: Final Elasticsearch query: {query_dict}")

            response = await self._execute_search(s)

            # Build network data with node metadata
            nodes_dict = {}  # protein_id -> node metadata dict
            edges = []

            for hit in response.hits:
                protein_a = hit.protein_a
                protein_b = hit.protein_b
                score = getattr(hit, score_field, 0)

                # Collect metadata for protein_a
                if protein_a not in nodes_dict:
                    nodes_dict[protein_a] = {
                        "id": protein_a,
                        "locus_tag": getattr(hit, "protein_a_locus_tag", None),
                        "name": getattr(hit, "protein_a_name", None),
                        "product": getattr(hit, "protein_a_product", None),
                    }
                else:
                    # Update metadata with non-null values if current values are None
                    node_meta = nodes_dict[protein_a]
                    node_meta["locus_tag"] = node_meta.get("locus_tag") or getattr(
                        hit, "protein_a_locus_tag", None
                    )
                    node_meta["name"] = node_meta.get("name") or getattr(
                        hit, "protein_a_name", None
                    )
                    node_meta["product"] = node_meta.get("product") or getattr(
                        hit, "protein_a_product", None
                    )

                # Collect metadata for protein_b
                if protein_b not in nodes_dict:
                    nodes_dict[protein_b] = {
                        "id": protein_b,
                        "locus_tag": getattr(hit, "protein_b_locus_tag", None),
                        "name": getattr(hit, "protein_b_name", None),
                        "product": getattr(hit, "protein_b_product", None),
                    }
                else:
                    # Update metadata with non-null values if current values are None
                    node_meta = nodes_dict[protein_b]
                    node_meta["locus_tag"] = node_meta.get("locus_tag") or getattr(
                        hit, "protein_b_locus_tag", None
                    )
                    node_meta["name"] = node_meta.get("name") or getattr(
                        hit, "protein_b_name", None
                    )
                    node_meta["product"] = node_meta.get("product") or getattr(
                        hit, "protein_b_product", None
                    )

                # Add edge using schema
                edges.append(
                    PPINetworkEdgeSchema(
                        source=protein_a,
                        target=protein_b,
                        weight=score if score else None,
                    )
                )

            # Convert nodes dict to list of schema objects
            node_list = [PPINetworkNodeSchema(**node_data) for node_data in nodes_dict.values()]

            return PPINetworkSchema(nodes=node_list, edges=edges, properties={})

        except Exception as e:
            logger.error(f"Error getting network data: {e}")
            raise ServiceError(f"Failed to get network data: {str(e)}")

    async def get_network_properties(
        self,
        score_type: str,
        score_threshold: float,
        species_acronym: Optional[str] = None,
        isolate_name: Optional[str] = None,
        locus_tag: Optional[str] = None,
    ) -> PPINetworkPropertiesSchema:
        """Get network properties for a specific score type and threshold (optimized).

        If locus_tag is provided, only calculates properties for PPIs involving that gene.
        """
        # Check cache first (include locus_tag in cache key if provided)
        cache_key = f"network_props_{score_type}_{score_threshold}_{species_acronym}_{isolate_name}_{locus_tag}"
        if cache_key in self._network_cache:
            logger.info(f"Returning cached network properties for {cache_key}")
            return self._network_cache[cache_key]

        try:
            # When locus_tag is provided, skip isolate_name filter because:
            # 1. locus_tag already uniquely identifies the gene
            # 2. isolate_name might not be populated in PPI documents
            # 3. For type strains, PPI data might be shared across isolates
            # 4. This avoids over-filtering that results in no matches
            search_isolate_name = None if locus_tag else isolate_name
            if locus_tag and isolate_name:
                logger.info(
                    "get_network_properties: Skipping isolate_name filter when locus_tag is provided (to avoid over-filtering; isolate_name may not be populated in PPI documents)"
                )

            # Build search once
            s = self._build_base_search(
                species_acronym, search_isolate_name, score_type, score_threshold
            )

            # If locus_tag is provided, filter to only PPIs involving this gene
            # Filter directly by locus_tag fields instead of resolving to protein_id
            # to avoid potential mismatches between resolved protein_id and participants field
            if locus_tag:
                logger.info(
                    f"get_network_properties: Filtering to PPIs involving locus_tag '{locus_tag}'"
                )
                # Filter to interactions where this locus_tag appears in either protein_a or protein_b
                s = s.filter(
                    "bool",
                    should=[
                        {"term": {"protein_a_locus_tag": locus_tag}},
                        {"term": {"protein_b_locus_tag": locus_tag}},
                    ],
                )

            # Get count efficiently
            from asgiref.sync import sync_to_async

            total_matches = await sync_to_async(s.count)()
            logger.info(
                f"get_network_properties: Found {total_matches} total matches before limiting"
            )
            logger.info(
                f"get_network_properties: Query params - species_acronym={species_acronym}, isolate_name={isolate_name}, locus_tag={locus_tag}, score_type={score_type}, score_threshold={score_threshold}"
            )
            max_fetch = min(total_matches, 10000000)
            s = s[:max_fetch]

            # Only fetch what we need for network analysis
            score_field = self._validate_and_normalize_score_field(score_type)
            s = s.source(["protein_a", "protein_b", score_field])

            # Log the final query for debugging
            query_dict = s.to_dict()
            logger.info(f"get_network_properties: Final Elasticsearch query: {query_dict}")

            response = await self._execute_search(s)

            # Build graph directly from hits (no intermediate data structure)
            G = nx.Graph()
            for hit in response.hits:
                protein_a = hit.protein_a
                protein_b = hit.protein_b
                score = getattr(hit, score_field, 0)
                G.add_edge(protein_a, protein_b, weight=score)

            # Calculate properties with safe handling for edge cases
            num_nodes = G.number_of_nodes()
            num_edges = G.number_of_edges()

            # Calculate density: 2 * edges / (nodes * (nodes - 1))
            # Handle edge cases: empty graph or single node
            if num_nodes <= 1:
                density = 0.0
            else:
                density = nx.density(G)

            # Calculate average clustering coefficient
            # Handle edge cases: empty graph, single node, or no edges
            if num_nodes == 0 or num_edges == 0:
                avg_clustering = 0.0
            else:
                try:
                    avg_clustering = nx.average_clustering(G)
                except (ZeroDivisionError, nx.NetworkXError):
                    avg_clustering = 0.0

            # Get degree distribution
            degree_distribution = [d for n, d in G.degree()]

            result = PPINetworkPropertiesSchema(
                num_nodes=num_nodes,
                num_edges=num_edges,
                density=density,
                avg_clustering_coefficient=avg_clustering,
                degree_distribution=degree_distribution,
            )

            # Cache the result
            self._network_cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Error calculating network properties: {e}")
            raise ServiceError(f"Failed to calculate network properties: {str(e)}")

    async def get_protein_interactions(
        self, protein_id: str, species_acronym: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all interactions for a specific protein (lightweight)."""
        try:
            s = self._build_base_search(species_acronym)
            s = s.filter("terms", participants=[protein_id])
            s = s.source(self._get_standard_source_fields())
            s = s[:10000]

            logger.info(f"search query: {s.to_dict()}")

            response = await self._execute_search(s)

            interactions = []
            for hit in response.hits:
                interactions.append(
                    {
                        "protein_a": hit.protein_a,
                        "protein_b": hit.protein_b,
                        "ds_score": getattr(hit, "ds_score", None),
                        "string_score": getattr(hit, "string_score", None),
                        "melt_score": getattr(hit, "melt_score", None),
                        "protein_a_locus_tag": getattr(hit, "protein_a_locus_tag", None),
                        "protein_a_name": getattr(hit, "protein_a_name", None),
                        "protein_a_product": getattr(hit, "protein_a_product", None),
                        "protein_b_locus_tag": getattr(hit, "protein_b_locus_tag", None),
                        "protein_b_name": getattr(hit, "protein_b_name", None),
                        "protein_b_product": getattr(hit, "protein_b_product", None),
                    }
                )

            return interactions

        except Exception as e:
            logger.error(f"Error getting protein interactions: {e}")
            raise ServiceError(f"Failed to get protein interactions: {str(e)}")

    async def get_protein_neighborhood(
        self, protein_id: str, n: int = 5, species_acronym: Optional[str] = None
    ) -> PPINeighborhoodSchema:
        """Get neighborhood data for a specific protein using Dijkstra's algorithm (optimized)."""
        try:
            # Build search for protein interactions
            s = self._build_base_search(species_acronym)
            s = s.filter("terms", participants=[protein_id])
            s = s.source(self._get_standard_source_fields())

            response = await self._execute_search(s)

            # Build a NetworkX graph to use Dijkstra's algorithm
            G = nx.Graph()
            gene_mapping = {}

            # Add all interactions to the graph and build gene mapping
            for hit in response.hits:
                protein_a = hit.protein_a
                protein_b = hit.protein_b
                weight = hit.ds_score or 0

                # Add edge with weight (use 1/weight for distance since higher scores = closer)
                distance = 1.0 / (weight + 0.001) if weight > 0 else 1000
                G.add_edge(protein_a, protein_b, weight=distance)

                # Build gene mapping
                if protein_a == protein_id:
                    gene_mapping[protein_b] = {
                        "locus_tag": hit.protein_b_locus_tag,
                        "name": hit.protein_b_name,
                        "product": hit.protein_b_product,
                    }
                elif protein_b == protein_id:
                    gene_mapping[protein_a] = {
                        "locus_tag": hit.protein_a_locus_tag,
                        "name": hit.protein_a_name,
                        "product": hit.protein_a_product,
                    }

            # Use Dijkstra's algorithm to find nearest neighbors
            if protein_id in G:
                distances = nx.single_source_dijkstra_path_length(G, protein_id, weight="weight")
                # Sort by distance and get the n nearest neighbors (excluding the protein itself)
                nearest_neighbors = sorted(distances, key=distances.get)[1 : n + 1]
            else:
                nearest_neighbors = []

            # Build neighborhood data
            neighborhood_data = await self._build_neighborhood_data(
                protein_id, nearest_neighbors, gene_mapping, species_acronym
            )

            # Add edges for the neighborhood subgraph
            neighborhood_nodes = [protein_id] + nearest_neighbors
            edges = []

            # Add edges from the original interactions
            for hit in response.hits:
                protein_a = hit.protein_a
                protein_b = hit.protein_b

                # Include all edges within the neighborhood subgraph
                if protein_a in neighborhood_nodes and protein_b in neighborhood_nodes:
                    edges.append(
                        {"source": protein_a, "target": protein_b, "weight": hit.ds_score or 0}
                    )

            # Query for additional interactions between neighbor proteins
            if len(nearest_neighbors) > 1:
                try:
                    logger.info(
                        f"Searching for neighbor-to-neighbor interactions among: {nearest_neighbors}"
                    )

                    # Use base search builder for neighbor interactions
                    neighbor_search = self._build_base_search(species_acronym)
                    neighbor_search = neighbor_search.filter(
                        "terms", participants=nearest_neighbors
                    )
                    neighbor_search = neighbor_search.source(["protein_a", "protein_b", "ds_score"])

                    neighbor_response = await self._execute_search(neighbor_search)
                    logger.info(
                        f"Found {len(neighbor_response.hits)} potential neighbor-to-neighbor interactions"
                    )

                    # Add any new interactions between neighbors
                    existing_edges = {(edge["source"], edge["target"]) for edge in edges}
                    existing_edges.update({(edge["target"], edge["source"]) for edge in edges})

                    new_edges_count = 0
                    for hit in neighbor_response.hits:
                        protein_a = hit.protein_a
                        protein_b = hit.protein_b

                        # Only add if both proteins are neighbors and we don't already have this edge
                        if (
                            protein_a in nearest_neighbors
                            and protein_b in nearest_neighbors
                            and (protein_a, protein_b) not in existing_edges
                            and (protein_b, protein_a) not in existing_edges
                        ):

                            edges.append(
                                {
                                    "source": protein_a,
                                    "target": protein_b,
                                    "weight": hit.ds_score or 0,
                                }
                            )
                            new_edges_count += 1
                            logger.info(
                                f"Added neighbor-to-neighbor edge: {protein_a} -> {protein_b}"
                            )

                    logger.info(f"Added {new_edges_count} new neighbor-to-neighbor edges")

                except Exception as e:
                    logger.warning(f"Could not fetch neighbor-to-neighbor interactions: {e}")

            # Update network data with edges
            neighborhood_data.network_data.edges = edges

            return neighborhood_data

        except Exception as e:
            logger.error(f"Error getting protein neighborhood: {e}")
            raise ServiceError(f"Failed to get protein neighborhood: {str(e)}")

    async def get_all_protein_neighbors(
        self, protein_id: str, species_acronym: Optional[str] = None
    ) -> PPIAllNeighborsSchema:
        """Get all neighbors for a specific protein without algorithm processing (raw data)."""
        try:
            # Build search for protein interactions
            s = self._build_base_search(species_acronym)
            s = s.filter("terms", participants=[protein_id])
            s = s.source(self._get_standard_source_fields(include_scores=True))
            s = s[:50000]  # Reasonable limit for raw data

            response = await self._execute_search(s)

            # Convert to schema objects
            interactions = []
            unique_neighbors = set()
            neighbor_metadata = {}

            for hit in response.hits:
                try:
                    interaction_data = self._hit_to_dict(hit)
                    interactions.append(PPIInteractionSchema(**interaction_data))

                    # Track unique neighbors and their metadata
                    protein_a = hit.protein_a
                    protein_b = hit.protein_b

                    if protein_a == protein_id and protein_b != protein_id:
                        unique_neighbors.add(protein_b)
                        neighbor_metadata[protein_b] = {
                            "protein_id": protein_b,
                            "locus_tag": getattr(hit, "protein_b_locus_tag", None),
                            "name": getattr(hit, "protein_b_name", None),
                            "product": getattr(hit, "protein_b_product", None),
                            "uniprot_id": getattr(hit, "protein_b_uniprot_id", None),
                        }
                    elif protein_b == protein_id and protein_a != protein_id:
                        unique_neighbors.add(protein_a)
                        neighbor_metadata[protein_a] = {
                            "protein_id": protein_a,
                            "locus_tag": getattr(hit, "protein_a_locus_tag", None),
                            "name": getattr(hit, "protein_a_name", None),
                            "product": getattr(hit, "protein_a_product", None),
                            "uniprot_id": getattr(hit, "protein_a_uniprot_id", None),
                        }

                except Exception as e:
                    logger.error(f"Error converting hit to schema: {e}")
                    logger.error(f"Hit data: {hit.to_dict()}")
                    continue

            # Build unique neighbors list with metadata
            unique_neighbors_list = []
            for neighbor_id in sorted(unique_neighbors):
                metadata = neighbor_metadata.get(neighbor_id, {})
                unique_neighbors_list.append(
                    {
                        "protein_id": neighbor_id,
                        "locus_tag": metadata.get("locus_tag"),
                        "name": metadata.get("name"),
                        "product": metadata.get("product"),
                        "uniprot_id": metadata.get("uniprot_id"),
                    }
                )

            return PPIAllNeighborsSchema(
                protein_id=protein_id,
                total_interactions=len(interactions),
                interactions=interactions,
                unique_neighbors=unique_neighbors_list,
            )

        except Exception as e:
            logger.error(f"Error getting all protein neighbors: {e}")
            raise ServiceError(f"Failed to get all protein neighbors: {str(e)}")

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
            # Metadata
            "evidence_count": getattr(hit, "evidence_count", 0),
        }
