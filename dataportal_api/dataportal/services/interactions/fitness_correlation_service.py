"""
Service for gene fitness correlation operations.

This service provides methods for querying gene-gene fitness correlations,
finding correlated genes, and building correlation networks.
"""

import logging
from typing import List, Dict, Any, Optional

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search

from dataportal.models.fitness_correlation import GeneFitnessCorrelationDocument
from dataportal.services.base_service import BaseService
from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)

# Constants
INDEX_FITNESS_CORRELATION = "fitness_correlation_index"


class FitnessCorrelationService(BaseService):
    """Service for gene fitness correlation data operations."""

    def __init__(self):
        super().__init__(INDEX_FITNESS_CORRELATION)
        self.document_class = GeneFitnessCorrelationDocument

    def _build_base_search(
            self,
            species_acronym: Optional[str] = None,
            isolate_name: Optional[str] = None,
    ) -> Search:
        """Build a base search query with common filters."""
        s = Search(index=self.index_name)

        if species_acronym:
            s = s.filter("term", species_acronym=species_acronym)

        if isolate_name:
            s = s.filter("term", isolate_name=isolate_name)

        return s

    async def get_by_id(self, id: str) -> Optional[str]:
        """ Not Implemented."""
        raise NotImplementedError("get_all not implemented for Fitness Correlation - use search methods instead")

    async def get_all(self, **kwargs) -> List[str]:
        """ Not Implemented."""
        raise NotImplementedError("get_all not implemented for Fitness Correlation - use search methods instead")

    async def search(self, query: Dict[str, Any]) -> List[str]:
        """ Not Implemented."""
        raise NotImplementedError(
            "search not implemented for Fitness Correlation - use specific search methods instead")

    async def get_correlations_for_gene(
            self,
            locus_tag: str,
            species_acronym: Optional[str] = None,
            min_correlation: Optional[float] = None,
            max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get all correlations for a specific gene.

        Args:
            locus_tag: Locus tag of the gene
            species_acronym: Optional species filter
            min_correlation: Minimum absolute correlation value
            max_results: Maximum number of results to return

        Returns:
            List of correlation dictionaries
        """
        try:
            s = self._build_base_search(species_acronym)
            s = s.filter("terms", genes=[locus_tag])

            if min_correlation is not None:
                s = s.filter("range", abs_correlation={"gte": abs(min_correlation)})

            # Sort by absolute correlation descending
            s = s.sort({"abs_correlation": {"order": "desc"}})
            s = s[:max_results]

            response = await self._execute_search(s)

            correlations = []
            for hit in response.hits:
                # Determine which gene is the partner
                partner_gene = hit.gene_b if hit.gene_a == locus_tag else hit.gene_a
                partner_prefix = "gene_b" if hit.gene_a == locus_tag else "gene_a"

                correlations.append({
                    "locus_tag": locus_tag,
                    "partner_gene": partner_gene,
                    "partner_locus_tag": getattr(hit, f"{partner_prefix}_locus_tag", partner_gene),
                    "partner_name": getattr(hit, f"{partner_prefix}_name", None),
                    "partner_product": getattr(hit, f"{partner_prefix}_product", None),
                    "correlation_value": hit.correlation_value,
                    "abs_correlation": hit.abs_correlation,
                    "correlation_strength": hit.correlation_strength,
                    "species_acronym": hit.species_acronym,
                    "isolate_name": getattr(hit, "isolate_name", None),
                })

            return correlations

        except Exception as e:
            logger.error(f"Error getting correlations for gene {locus_tag}: {e}")
            raise ServiceError(f"Failed to get correlations: {str(e)}")

    async def get_correlation_between_genes(
            self,
            locus_tag_a: str,
            locus_tag_b: str,
            species_acronym: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the correlation value between two specific genes.

        Args:
            locus_tag_a: First gene locus tag
            locus_tag_b: Second gene locus tag
            species_acronym: Optional species filter

        Returns:
            Correlation dictionary or None if not found
        """
        try:
            # Build pair ID for lookup
            from dataportal.models.base import canonical_pair, build_pair_id

            if not species_acronym:
                # Try to extract from locus_tag_a
                if "_" in locus_tag_a:
                    species_acronym = locus_tag_a.split("_")[0]

            if not species_acronym:
                raise ServiceError("Species acronym required or cannot be inferred")

            aa, bb = canonical_pair(locus_tag_a, locus_tag_b)
            pair_id = build_pair_id(species_acronym, aa, bb)

            # Try to fetch by document ID
            try:
                doc = await sync_to_async(
                    GeneFitnessCorrelationDocument.get
                )(id=pair_id, index=self.index_name)

                return {
                    "pair_id": doc.pair_id,
                    "locus_tag_a": doc.gene_a,
                    "locus_tag_b": doc.gene_b,
                    "correlation_value": doc.correlation_value,
                    "abs_correlation": doc.abs_correlation,
                    "correlation_strength": doc.correlation_strength,
                    "species_acronym": doc.species_acronym,
                    "isolate_name": getattr(doc, "isolate_name", None),
                    "gene_a_name": getattr(doc, "gene_a_name", None),
                    "gene_a_product": getattr(doc, "gene_a_product", None),
                    "gene_b_name": getattr(doc, "gene_b_name", None),
                    "gene_b_product": getattr(doc, "gene_b_product", None),
                }
            except Exception:
                return None

        except Exception as e:
            logger.error(f"Error getting correlation between {locus_tag_a} and {locus_tag_b}: {e}")
            raise ServiceError(f"Failed to get correlation: {str(e)}")

    async def get_top_correlations(
            self,
            species_acronym: Optional[str] = None,
            correlation_strength: Optional[str] = None,
            limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get top correlations across the dataset.

        Args:
            species_acronym: Optional species filter
            correlation_strength: Optional filter (e.g., "strong_positive")
            limit: Number of results to return

        Returns:
            List of top correlation dictionaries
        """
        try:
            s = self._build_base_search(species_acronym)

            if correlation_strength:
                s = s.filter("term", correlation_strength=correlation_strength)

            # Exclude self-correlations
            s = s.filter("term", is_self_correlation=False)

            # Sort by absolute correlation descending
            s = s.sort({"abs_correlation": {"order": "desc"}})
            s = s[:limit]

            response = await self._execute_search(s)

            correlations = []
            for hit in response.hits:
                correlations.append({
                    "gene_a": hit.gene_a,
                    "gene_b": hit.gene_b,
                    "gene_a_locus_tag": getattr(hit, "gene_a_locus_tag", hit.gene_a),
                    "gene_a_name": getattr(hit, "gene_a_name", None),
                    "gene_a_product": getattr(hit, "gene_a_product", None),
                    "gene_b_locus_tag": getattr(hit, "gene_b_locus_tag", hit.gene_b),
                    "gene_b_name": getattr(hit, "gene_b_name", None),
                    "gene_b_product": getattr(hit, "gene_b_product", None),
                    "correlation_value": hit.correlation_value,
                    "abs_correlation": hit.abs_correlation,
                    "correlation_strength": hit.correlation_strength,
                    "species_acronym": hit.species_acronym,
                })

            return correlations

        except Exception as e:
            logger.error(f"Error getting top correlations: {e}")
            raise ServiceError(f"Failed to get top correlations: {str(e)}")

    async def get_correlation_statistics(
            self,
            species_acronym: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about correlations in the dataset.

        Args:
            species_acronym: Optional species filter

        Returns:
            Dictionary with statistics
        """
        try:
            s = self._build_base_search(species_acronym)

            # Get total count
            total = await sync_to_async(s.count)()

            # Get counts by strength
            s_copy = self._build_base_search(species_acronym)
            s_copy.aggs.bucket("by_strength", "terms", field="correlation_strength", size=20)

            response = await self._execute_search(s_copy)

            strength_counts = {}
            if hasattr(response, "aggregations"):
                for bucket in response.aggregations.by_strength.buckets:
                    strength_counts[bucket.key] = bucket.doc_count

            return {
                "total_correlations": total,
                "by_strength": strength_counts,
                "species_acronym": species_acronym,
            }

        except Exception as e:
            logger.error(f"Error getting correlation statistics: {e}")
            raise ServiceError(f"Failed to get statistics: {str(e)}")

    async def search_correlations(
            self,
            query: str,
            species_acronym: Optional[str] = None,
            page: int = 1,
            per_page: int = 20,
    ) -> Dict[str, Any]:
        """
        Search correlations by gene name or product.

        Args:
            query: Search query string
            species_acronym: Optional species filter
            page: Page number
            per_page: Results per page

        Returns:
            Paginated search results
        """
        try:
            s = self._build_base_search(species_acronym)

            # Search in gene names and products
            if query:
                s = s.query(
                    "multi_match",
                    query=query,
                    fields=[
                        "gene_a_name",
                        "gene_a_product",
                        "gene_b_name",
                        "gene_b_product",
                        "gene_a_locus_tag",
                        "gene_b_locus_tag",
                    ],
                )

            # Get total count
            total = await sync_to_async(s.count)()

            # Apply pagination
            offset = (page - 1) * per_page
            s = s[offset: offset + per_page]

            # Sort by relevance, then correlation strength
            s = s.sort("_score", {"abs_correlation": {"order": "desc"}})

            response = await self._execute_search(s)

            results = []
            for hit in response.hits:
                results.append({
                    "gene_a": hit.gene_a,
                    "gene_b": hit.gene_b,
                    "gene_a_name": getattr(hit, "gene_a_name", None),
                    "gene_a_product": getattr(hit, "gene_a_product", None),
                    "gene_b_name": getattr(hit, "gene_b_name", None),
                    "gene_b_product": getattr(hit, "gene_b_product", None),
                    "correlation_value": hit.correlation_value,
                    "correlation_strength": hit.correlation_strength,
                })

            num_pages = (total + per_page - 1) // per_page

            return {
                "results": results,
                "page": page,
                "per_page": per_page,
                "total": total,
                "num_pages": num_pages,
                "has_previous": page > 1,
                "has_next": page < num_pages,
            }

        except Exception as e:
            logger.error(f"Error searching correlations: {e}")
            raise ServiceError(f"Failed to search correlations: {str(e)}")
