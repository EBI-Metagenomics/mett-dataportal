import logging
from typing import Optional, List, Dict, Any

from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict
from elasticsearch_dsl import Search

from dataportal.schema.experimental.proteomics_schemas import (
    ProteomicsWithGeneSchema,
    ProteomicsDataSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import INDEX_FEATURES
from dataportal.utils.exceptions import ServiceError, GeneNotFoundError

logger = logging.getLogger(__name__)


class ProteomicsService(BaseService[ProteomicsWithGeneSchema, str]):
    """Service for retrieving proteomics evidence data."""

    def __init__(self):
        super().__init__(INDEX_FEATURES)

    async def get_by_id(self, locus_tag: str) -> Optional[ProteomicsWithGeneSchema]:
        """
        Retrieve proteomics data for a gene by locus tag.
        
        Args:
            locus_tag: Gene locus tag identifier
            
        Returns:
            ProteomicsWithGeneSchema with gene info and proteomics data
            
        Raises:
            GeneNotFoundError: If gene with locus_tag not found
        """
        try:
            result = await sync_to_async(self._fetch_proteomics_by_identifier)(locus_tag)
            return result
        except GeneNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching proteomics data for {locus_tag}: {e}")
            raise ServiceError(f"Failed to fetch proteomics data: {str(e)}")

    async def get_all(self, **kwargs) -> List[ProteomicsWithGeneSchema]:
        """Not implemented - use search instead."""
        raise NotImplementedError("Use search method with identifiers instead")

    async def search(self, **kwargs) -> List[ProteomicsWithGeneSchema]:
        """Not implemented - use search instead."""
        raise NotImplementedError("Use search method with identifiers instead")

    async def search_with_filters(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        min_coverage: Optional[float] = None,
        min_unique_peptides: Optional[int] = None,
        has_evidence: Optional[bool] = None,
    ) -> List[ProteomicsWithGeneSchema]:
        """
        Search for proteomics data with additional filters.
        
        Args:
            locus_tags: List of locus tags
            uniprot_ids: List of UniProt IDs
            min_coverage: Minimum coverage percentage filter
            min_unique_peptides: Minimum unique peptides filter
            has_evidence: Filter by evidence flag
            
        Returns:
            List of ProteomicsWithGeneSchema objects matching filters
        """
        try:
            results = await sync_to_async(self._fetch_proteomics_by_identifiers)(
                locus_tags=locus_tags or [],
                uniprot_ids=uniprot_ids or [],
                min_coverage=min_coverage,
                min_unique_peptides=min_unique_peptides,
                has_evidence=has_evidence
            )
            return results
        except Exception as e:
            logger.error(f"Error searching proteomics data with filters: {e}")
            raise ServiceError(f"Failed to search proteomics data: {str(e)}")

    def _fetch_proteomics_by_identifier(
        self, identifier: str
    ) -> ProteomicsWithGeneSchema:
        """
        Fetch proteomics data for a single identifier (locus_tag or uniprot_id).
        
        This is a synchronous method to be called via sync_to_async.
        """
        # Try searching by locus_tag first, only return genes with proteomics data
        s = (
            Search(index=self.index_name)
            .filter("term", feature_type="gene")
            .filter("term", has_proteomics=True)  # Only genes with proteomics evidence
            .query("bool", should=[
                {"term": {"locus_tag.keyword": identifier}},
                {"term": {"uniprot_id": identifier}},
            ])
            .extra(size=1)
        )
        
        response = s.execute()
        
        if not response.hits:
            raise GeneNotFoundError(f"Gene with identifier '{identifier}' not found or has no proteomics evidence")
        
        hit = response.hits[0]
        return self._convert_hit_to_proteomics_schema(hit)

    def _fetch_proteomics_by_identifiers(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        min_coverage: Optional[float] = None,
        min_unique_peptides: Optional[int] = None,
        has_evidence: Optional[bool] = None,
    ) -> List[ProteomicsWithGeneSchema]:
        """
        Fetch proteomics data for multiple identifiers.
        
        This is a synchronous method to be called via sync_to_async.
        """
        locus_tags = locus_tags or []
        uniprot_ids = uniprot_ids or []
        
        # Build the search query - only return genes with proteomics data
        s = (
            Search(index=self.index_name)
            .filter("term", feature_type="gene")
            .filter("term", has_proteomics=True)  # Only genes with proteomics evidence
        )
        
        # Build the query conditions based on provided identifiers (if any)
        should_conditions = []
        
        if locus_tags:
            should_conditions.append({"terms": {"locus_tag.keyword": locus_tags}})
        
        if uniprot_ids:
            should_conditions.append({"terms": {"uniprot_id": uniprot_ids}})
        
        # Apply the identifier query (if identifiers were provided)
        if should_conditions:
            s = s.query("bool", should=should_conditions, minimum_should_match=1)
        
        # Apply filters if provided
        if min_coverage is not None or min_unique_peptides is not None or has_evidence is not None:
            # Add nested query for proteomics filters
            nested_conditions = []
            
            if min_coverage is not None:
                nested_conditions.append({
                    "range": {"proteomics.coverage": {"gte": min_coverage}}
                })
            
            if min_unique_peptides is not None:
                nested_conditions.append({
                    "range": {"proteomics.unique_peptides": {"gte": min_unique_peptides}}
                })
            
            if has_evidence is not None:
                nested_conditions.append({
                    "term": {"proteomics.evidence": has_evidence}
                })
            
            if nested_conditions:
                s = s.filter("nested", path="proteomics", query={
                    "bool": {"must": nested_conditions}
                })
        
        # Limit to reasonable number of results
        # If identifiers are provided, use their count; otherwise use a default limit
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 0:
            s = s.extra(size=min(total_identifiers, 1000))
        else:
            # No identifiers provided - searching by filters only
            # Use a reasonable default limit for discovery queries
            s = s.extra(size=100000)
        
        response = s.execute()
        
        results = []
        for hit in response.hits:
            try:
                schema = self._convert_hit_to_proteomics_schema(hit)
                # Extra safeguard: only include genes that actually have proteomics data
                if schema.proteomics and len(schema.proteomics) > 0:
                    results.append(schema)
                else:
                    logger.warning(f"Gene {schema.locus_tag} has has_proteomics=True but empty proteomics array")
            except Exception as e:
                logger.warning(f"Error converting hit to schema: {e}")
                continue
        
        return results

    def _convert_hit_to_proteomics_schema(self, hit) -> ProteomicsWithGeneSchema:
        """Convert Elasticsearch hit to ProteomicsWithGeneSchema."""
        hit_dict = hit.to_dict()
        
        # Extract basic gene information
        gene_data = {
            "locus_tag": hit_dict.get("locus_tag"),
            "gene_name": hit_dict.get("gene_name"),
            "uniprot_id": hit_dict.get("uniprot_id"),
            "product": hit_dict.get("product"),
            "isolate_name": hit_dict.get("isolate_name"),
            "species_scientific_name": hit_dict.get("species_scientific_name"),
            "species_acronym": hit_dict.get("species_acronym"),
        }
        
        # Extract proteomics data
        proteomics_raw = hit_dict.get("proteomics", [])
        proteomics_data = []
        
        if proteomics_raw:
            for entry in proteomics_raw:
                proteomics_data.append(ProteomicsDataSchema(
                    coverage=entry.get("coverage"),
                    unique_peptides=entry.get("unique_peptides"),
                    unique_intensity=entry.get("unique_intensity"),
                    evidence=entry.get("evidence"),
                ))
        
        return ProteomicsWithGeneSchema(
            **gene_data,
            proteomics=proteomics_data
        )

