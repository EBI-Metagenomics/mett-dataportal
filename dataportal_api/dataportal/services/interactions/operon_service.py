"""
Service for operon operations.

This service provides methods for querying operon information,
finding operons containing specific genes, and analyzing operon composition.
"""

import logging
from typing import List, Dict, Any, Optional

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search

from dataportal.models.operons import OperonDocument
from dataportal.schema.interactions.operon_schemas import OperonSearchPaginationSchema
from dataportal.services.base_service import BaseService
from dataportal.utils.exceptions import ServiceError
from dataportal.utils.constants import INDEX_OPERONS

logger = logging.getLogger(__name__)


class OperonService(BaseService):
    """Service for operon data operations."""

    def __init__(self):
        super().__init__(INDEX_OPERONS)
        self.document_class = OperonDocument

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

        # logger.info(f'Build base search query: {s.to_dict()}')

        return s

    async def get_by_id(self, operon_id: str) -> Optional[Dict[str, Any]]:
        """
        Get operon by ID.

        Args:
            operon_id: The operon ID

        Returns:
            Operon dictionary or None if not found
        """
        try:
            s = Search(index=self.index_name)
            s = s.filter("term", operon_id=operon_id)

            response = await self._execute_search(s)

            if not response.hits:
                return None

            return self._convert_doc_to_dict(response.hits[0])

        except Exception as e:
            logger.debug(f"Operon {operon_id} not found: {e}")
            return None

    async def get_all(self, **kwargs) -> List[Dict[str, Any]]:
        """Not implemented - use search methods instead."""
        raise NotImplementedError(
            "get_all not implemented for Operons - use search methods instead"
        )

    async def search(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Not implemented - use specific search methods instead."""
        raise NotImplementedError(
            "search not implemented for Operons - use specific search methods instead"
        )

    async def get_operons_by_gene(
        self,
        locus_tag: str,
        species_acronym: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all operons containing a specific gene.

        Args:
            locus_tag: Gene locus tag
            species_acronym: Optional species filter

        Returns:
            List of operons containing the gene
        """
        try:
            s = self._build_base_search(species_acronym)

            # Search for gene in genes list
            s = s.filter("term", genes=locus_tag)

            response = await self._execute_search(s)

            operons = []
            for hit in response.hits:
                operons.append(self._convert_doc_to_dict(hit))

            return operons

        except Exception as e:
            logger.error(f"Error getting operons for gene {locus_tag}: {e}")
            raise ServiceError(f"Failed to get operons: {str(e)}")

    async def search_operons(
        self,
        locus_tag: Optional[str] = None,
        operon_id: Optional[str] = None,
        species_acronym: Optional[str] = None,
        isolate_name: Optional[str] = None,
        has_tss: Optional[bool] = None,
        has_terminator: Optional[bool] = None,
        min_gene_count: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> OperonSearchPaginationSchema:
        """
        Search operons with filters.

        Args:
            locus_tag: Optional gene filter (operons containing this gene)
            operon_id: Optional operon ID filter
            species_acronym: Optional species filter
            isolate_name: Optional isolate filter
            has_tss: Optional TSS filter
            has_terminator: Optional terminator filter
            min_gene_count: Optional minimum gene count filter
            page: Page number
            per_page: Results per page

        Returns:
            Paginated operon results
        """
        try:
            s = self._build_base_search(species_acronym, isolate_name)

            if locus_tag:
                s = s.filter("term", genes=locus_tag)

            if operon_id:
                s = s.filter("term", operon_id=operon_id)

            if has_tss is not None:
                s = s.filter("term", has_tss=has_tss)

            if has_terminator is not None:
                s = s.filter("term", has_terminator=has_terminator)

            if min_gene_count is not None:
                s = s.filter("range", gene_count={"gte": min_gene_count})

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

            return OperonSearchPaginationSchema(
                results=results,
                page_number=page,
                num_pages=num_pages,
                has_previous=page > 1,
                has_next=page < num_pages,
                total_results=total,
            )

        except Exception as e:
            logger.error(f"Error searching operons: {e}")
            raise ServiceError(f"Failed to search operons: {str(e)}")

    async def get_operon_statistics(
        self,
        species_acronym: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about operons.

        Args:
            species_acronym: Optional species filter

        Returns:
            Dictionary with operon statistics
        """
        try:
            s = self._build_base_search(species_acronym)

            # Get total count
            total = await sync_to_async(s.count)()

            # Get counts by gene count
            s_copy = self._build_base_search(species_acronym)
            s_copy.aggs.bucket("by_gene_count", "terms", field="gene_count", size=20)

            # Get counts with TSS/terminator
            s_copy.aggs.bucket("with_tss", "filter", filter={"term": {"has_tss": True}})
            s_copy.aggs.bucket(
                "with_terminator", "filter", filter={"term": {"has_terminator": True}}
            )

            response = await self._execute_search(s_copy)

            gene_count_distribution = {}
            if hasattr(response, "aggregations"):
                for bucket in response.aggregations.by_gene_count.buckets:
                    gene_count_distribution[bucket.key] = bucket.doc_count

            return {
                "total_operons": total,
                "with_tss": (
                    response.aggregations.with_tss.doc_count
                    if hasattr(response, "aggregations")
                    else 0
                ),
                "with_terminator": (
                    response.aggregations.with_terminator.doc_count
                    if hasattr(response, "aggregations")
                    else 0
                ),
                "gene_count_distribution": gene_count_distribution,
                "species_acronym": species_acronym,
            }

        except Exception as e:
            logger.error(f"Error getting operon statistics: {e}")
            raise ServiceError(f"Failed to get statistics: {str(e)}")

    def _convert_doc_to_dict(self, doc) -> Dict[str, Any]:
        """Convert Elasticsearch document to dictionary."""
        # Convert genes from AttrList to regular Python list
        genes = getattr(doc, "genes", [])
        if genes and not isinstance(genes, list):
            genes = list(genes)  # Convert AttrList to list

        result = {
            "operon_id": doc.operon_id,
            "isolate_name": getattr(doc, "isolate_name", None),
            "species_acronym": getattr(doc, "species_acronym", None),
            "species_scientific_name": getattr(doc, "species_scientific_name", None),
            "genes": genes,
            "gene_count": getattr(doc, "gene_count", 0),
            "has_tss": getattr(doc, "has_tss", False),
            "has_terminator": getattr(doc, "has_terminator", False),
        }

        # Add gene A details if available
        if hasattr(doc, "gene_a_locus_tag") and doc.gene_a_locus_tag:
            result["gene_a"] = {
                "locus_tag": doc.gene_a_locus_tag,
                "uniprot_id": getattr(doc, "gene_a_uniprot_id", None),
                "gene_name": getattr(doc, "gene_a_name", None),
                "product": getattr(doc, "gene_a_product", None),
                "isolate_name": getattr(doc, "gene_a_isolate_name", None),
            }

        # Add gene B details if available
        if hasattr(doc, "gene_b_locus_tag") and doc.gene_b_locus_tag:
            result["gene_b"] = {
                "locus_tag": doc.gene_b_locus_tag,
                "uniprot_id": getattr(doc, "gene_b_uniprot_id", None),
                "gene_name": getattr(doc, "gene_b_name", None),
                "product": getattr(doc, "gene_b_product", None),
                "isolate_name": getattr(doc, "gene_b_isolate_name", None),
            }

        return result
