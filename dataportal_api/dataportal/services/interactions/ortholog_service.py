"""
Service for ortholog operations.

This service provides methods for querying ortholog relationships between genes,
finding orthologs for specific genes, and analyzing orthology patterns.
"""

import logging
from typing import List, Dict, Any, Optional

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search

from dataportal.models.orthologs import OrthologDocument
from dataportal.schema.interactions.ortholog_schemas import OrthologSearchPaginationSchema
from dataportal.services.base_service import BaseService
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.constants import INDEX_ORTHOLOGS

logger = logging.getLogger(__name__)


class OrthologService(BaseService):
    """Service for ortholog data operations."""

    def __init__(self):
        super().__init__(INDEX_ORTHOLOGS)
        self.document_class = OrthologDocument

    def _build_base_search(
        self,
        species_acronym: Optional[str] = None,
    ) -> Search:
        """Build a base search query with common filters."""
        s = Search(index=self.index_name)

        if species_acronym:
            # Search for either gene_a or gene_b matching the species
            s = s.query(
                "bool",
                should=[
                    {"term": {"species_a_acronym": species_acronym}},
                    {"term": {"species_b_acronym": species_acronym}},
                ],
                minimum_should_match=1,
            )

        return s

    async def get_by_id(self, pair_id: str) -> Optional[Dict[str, Any]]:
        """
        Get ortholog pair by ID.

        Args:
            pair_id: The ortholog pair ID

        Returns:
            Ortholog pair dictionary or None if not found
        """
        try:
            doc = await sync_to_async(OrthologDocument.get)(id=pair_id, index=self.index_name)

            return self._convert_doc_to_dict(doc)
        except Exception as e:
            logger.debug(f"Ortholog pair {pair_id} not found: {e}")
            return None

    async def get_all(self, **kwargs) -> List[Dict[str, Any]]:
        """Not implemented - use search methods instead."""
        raise NotImplementedError(
            "get_all not implemented for Orthologs - use search methods instead"
        )

    async def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Not implemented - use specific search methods instead."""
        raise NotImplementedError(
            "search not implemented for Orthologs - use specific search methods instead"
        )

    async def get_orthologs_for_gene(
        self,
        locus_tag: str,
        species_acronym: Optional[str] = None,
        orthology_type: Optional[str] = None,
        one_to_one_only: bool = False,
        cross_species_only: bool = False,
        max_results: int = 10000,
    ) -> Dict[str, Any]:
        """
        Get all orthologs for a specific gene.

        Args:
            locus_tag: Gene locus tag
            species_acronym: Optional species filter
            orthology_type: Optional orthology type filter (1:1, many:1, etc.)
            one_to_one_only: Return only one-to-one orthologs
            cross_species_only: Return only cross-species orthologs
            max_results: Maximum number of results to return

        Returns:
            Dictionary with orthologs list and statistics
        """
        try:
            s = Search(index=self.index_name)

            # Search for gene in members field
            s = s.filter("term", members=locus_tag)

            if species_acronym:
                # Filter by target species (not the query gene's species)
                s = s.query(
                    "bool",
                    should=[
                        {"term": {"species_a_acronym": species_acronym}},
                        {"term": {"species_b_acronym": species_acronym}},
                    ],
                    minimum_should_match=1,
                )

            if orthology_type:
                s = s.filter("term", orthology_type=orthology_type)

            if one_to_one_only:
                s = s.filter("term", is_one_to_one=True)

            if cross_species_only:
                s = s.filter("term", same_species=False)

            s = s[:max_results]

            response = await self._execute_search(s)

            orthologs = []
            one_to_one_count = 0
            cross_species_count = 0

            for hit in response.hits:
                # Determine which gene is the ortholog (not the query gene)
                if hit.gene_a == locus_tag:
                    ortholog_gene = {
                        "locus_tag": hit.gene_b,
                        "uniprot_id": getattr(hit, "gene_b_uniprot_id", None),
                        "gene_name": getattr(hit, "gene_b_name", None),
                        "product": getattr(hit, "gene_b_product", None),
                        "start": getattr(hit, "gene_b_start", None),
                        "end": getattr(hit, "gene_b_end", None),
                        "strand": getattr(hit, "gene_b_strand", None),
                        "species_acronym": getattr(hit, "species_b_acronym", None),
                        "isolate": getattr(hit, "isolate_b", None),
                        # Relationship metadata (varies per pair)
                        "orthology_type": getattr(hit, "orthology_type", None),
                        "oma_group_id": getattr(hit, "oma_group_id", None),
                        "is_one_to_one": getattr(hit, "is_one_to_one", False),
                    }
                else:
                    ortholog_gene = {
                        "locus_tag": hit.gene_a,
                        "uniprot_id": getattr(hit, "gene_a_uniprot_id", None),
                        "gene_name": getattr(hit, "gene_a_name", None),
                        "product": getattr(hit, "gene_a_product", None),
                        "start": getattr(hit, "gene_a_start", None),
                        "end": getattr(hit, "gene_a_end", None),
                        "strand": getattr(hit, "gene_a_strand", None),
                        "species_acronym": getattr(hit, "species_a_acronym", None),
                        "isolate": getattr(hit, "isolate_a", None),
                        # Relationship metadata (varies per pair)
                        "orthology_type": getattr(hit, "orthology_type", None),
                        "oma_group_id": getattr(hit, "oma_group_id", None),
                        "is_one_to_one": getattr(hit, "is_one_to_one", False),
                    }

                orthologs.append(ortholog_gene)

                if getattr(hit, "is_one_to_one", False):
                    one_to_one_count += 1
                if not getattr(hit, "same_species", True):
                    cross_species_count += 1

            return {
                "query_gene": locus_tag,
                "orthologs": orthologs,
                "total_count": len(orthologs),
                "one_to_one_count": one_to_one_count,
                "cross_species_count": cross_species_count,
            }

        except Exception as e:
            logger.error(f"Error getting orthologs for gene {locus_tag}: {e}")
            raise ServiceError(f"Failed to get orthologs: {str(e)}")

    async def get_ortholog_pair(
        self,
        locus_tag_a: str,
        locus_tag_b: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get ortholog relationship between two genes.

        Args:
            locus_tag_a: First gene locus tag
            locus_tag_b: Second gene locus tag

        Returns:
            Ortholog pair dictionary or None if not found
        """
        try:
            s = Search(index=self.index_name)

            # Search for both genes in members field
            s = s.filter("terms", members=[locus_tag_a, locus_tag_b])

            # Ensure we have the exact pair
            s = s.query(
                "bool",
                must=[
                    {"term": {"members": locus_tag_a}},
                    {"term": {"members": locus_tag_b}},
                ],
            )

            response = await self._execute_search(s)

            if not response.hits:
                return None

            hit = response.hits[0]
            return self._convert_doc_to_dict(hit)

        except Exception as e:
            logger.error(f"Error getting ortholog pair for {locus_tag_a} and {locus_tag_b}: {e}")
            raise ServiceError(f"Failed to get ortholog pair: {str(e)}")

    async def search_orthologs(
        self,
        species_acronym: Optional[str] = None,
        orthology_type: Optional[str] = None,
        one_to_one_only: bool = False,
        cross_species_only: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> OrthologSearchPaginationSchema:
        """
        Search orthologs with filters.

        Args:
            species_acronym: Optional species filter
            orthology_type: Optional orthology type filter
            one_to_one_only: Return only one-to-one orthologs
            cross_species_only: Return only cross-species orthologs
            page: Page number
            per_page: Results per page

        Returns:
            Paginated ortholog results
        """
        try:
            s = self._build_base_search(species_acronym)

            if orthology_type:
                s = s.filter("term", orthology_type=orthology_type)

            if one_to_one_only:
                s = s.filter("term", is_one_to_one=True)

            if cross_species_only:
                s = s.filter("term", same_species=False)

            # Get total count
            total = await sync_to_async(s.count)()

            # Apply pagination
            offset = (page - 1) * per_page
            s = s[offset : offset + per_page]

            response = await self._execute_search(s)

            results = []
            for hit in response.hits:
                results.append(self._convert_doc_to_dict(hit))

            num_pages = (total + per_page - 1) // per_page

            return OrthologSearchPaginationSchema(
                results=results,
                page_number=page,
                num_pages=num_pages,
                has_previous=page > 1,
                has_next=page < num_pages,
                total_results=total,
            )

        except Exception as e:
            logger.error(f"Error searching orthologs: {e}")
            raise ServiceError(f"Failed to search orthologs: {str(e)}")

    def _convert_doc_to_dict(self, doc) -> Dict[str, Any]:
        """Convert Elasticsearch document to dictionary."""
        return {
            "pair_id": doc.pair_id,
            "orthology_type": getattr(doc, "orthology_type", None),
            "oma_group_id": getattr(doc, "oma_group_id", None),
            "is_one_to_one": getattr(doc, "is_one_to_one", False),
            "same_species": getattr(doc, "same_species", False),
            "same_isolate": getattr(doc, "same_isolate", False),
            "gene_a": {
                "locus_tag": doc.gene_a,
                "uniprot_id": getattr(doc, "gene_a_uniprot_id", None),
                "gene_name": getattr(doc, "gene_a_name", None),
                "product": getattr(doc, "gene_a_product", None),
                "start": getattr(doc, "gene_a_start", None),
                "end": getattr(doc, "gene_a_end", None),
                "strand": getattr(doc, "gene_a_strand", None),
                "species_acronym": getattr(doc, "species_a_acronym", None),
                "isolate": getattr(doc, "isolate_a", None),
            },
            "gene_b": {
                "locus_tag": doc.gene_b,
                "uniprot_id": getattr(doc, "gene_b_uniprot_id", None),
                "gene_name": getattr(doc, "gene_b_name", None),
                "product": getattr(doc, "gene_b_product", None),
                "start": getattr(doc, "gene_b_start", None),
                "end": getattr(doc, "gene_b_end", None),
                "strand": getattr(doc, "gene_b_strand", None),
                "species_acronym": getattr(doc, "species_b_acronym", None),
                "isolate": getattr(doc, "isolate_b", None),
            },
        }
