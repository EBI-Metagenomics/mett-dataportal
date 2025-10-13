import logging
from typing import Optional, List

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search

from dataportal.schema.experimental.fitness_schemas import (
    FitnessWithGeneSchema,
    FitnessDataSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import INDEX_FEATURES
from dataportal.utils.exceptions import ServiceError, GeneNotFoundError

logger = logging.getLogger(__name__)


class FitnessDataService(BaseService[FitnessWithGeneSchema, str]):
    """Service for retrieving fitness data."""

    def __init__(self):
        super().__init__(INDEX_FEATURES)

    async def get_by_id(self, locus_tag: str) -> Optional[FitnessWithGeneSchema]:
        """Retrieve fitness data for a gene by locus tag."""
        try:
            result = await sync_to_async(self._fetch_fitness_by_identifier)(locus_tag)
            return result
        except GeneNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching fitness data for {locus_tag}: {e}")
            raise ServiceError(f"Failed to fetch fitness data: {str(e)}")

    async def get_all(self, **kwargs) -> List[FitnessWithGeneSchema]:
        """Not implemented - use search instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search(self, **kwargs) -> List[FitnessWithGeneSchema]:
        """Not implemented - use search_with_filters instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search_with_filters(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        contrast: Optional[str] = None,
        min_lfc: Optional[float] = None,
        max_fdr: Optional[float] = None,
        min_barcodes: Optional[int] = None,
    ) -> List[FitnessWithGeneSchema]:
        """Search for fitness data with filters."""
        try:
            results = await sync_to_async(self._fetch_fitness_by_identifiers)(
                locus_tags=locus_tags or [],
                uniprot_ids=uniprot_ids or [],
                contrast=contrast,
                min_lfc=min_lfc,
                max_fdr=max_fdr,
                min_barcodes=min_barcodes,
            )
            return results
        except Exception as e:
            logger.error(f"Error searching fitness data with filters: {e}")
            raise ServiceError(f"Failed to search fitness data: {str(e)}")

    def _fetch_fitness_by_identifier(self, identifier: str) -> FitnessWithGeneSchema:
        """Fetch fitness data for a single identifier."""
        s = (
            Search(index=self.index_name)
            .filter("term", feature_type="gene")
            .filter("term", has_fitness=True)
            .query("bool", should=[
                {"term": {"locus_tag.keyword": identifier}},
                {"term": {"uniprot_id": identifier}},
            ])
            .extra(size=1)
        )
        
        response = s.execute()
        
        if not response.hits:
            raise GeneNotFoundError(f"Gene with identifier '{identifier}' not found or has no fitness data")
        
        hit = response.hits[0]
        return self._convert_hit_to_fitness_schema(hit)

    def _fetch_fitness_by_identifiers(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        contrast: Optional[str] = None,
        min_lfc: Optional[float] = None,
        max_fdr: Optional[float] = None,
        min_barcodes: Optional[int] = None,
    ) -> List[FitnessWithGeneSchema]:
        """Fetch fitness data for multiple identifiers."""
        locus_tags = locus_tags or []
        uniprot_ids = uniprot_ids or []
        
        s = (
            Search(index=self.index_name)
            .filter("term", has_fitness=True)  # Fast boolean filter
        )
        
        should_conditions = []
        if locus_tags:
            should_conditions.append({"terms": {"locus_tag.keyword": locus_tags}})
        if uniprot_ids:
            should_conditions.append({"terms": {"uniprot_id": uniprot_ids}})
        
        if should_conditions:
            s = s.query("bool", should=should_conditions, minimum_should_match=1)
        
        # Apply nested filters for fitness
        if any([contrast, min_lfc is not None, max_fdr is not None, min_barcodes is not None]):
            nested_conditions = []

            if contrast:
                nested_conditions.append({"term": {"fitness.contrast": contrast}})
            if min_lfc is not None:
                # Use absolute value for LFC
                nested_conditions.append({"range": {"fitness.lfc": {"gte": min_lfc}}})
            if max_fdr is not None:
                nested_conditions.append({"range": {"fitness.fdr": {"lte": max_fdr}}})
            if min_barcodes is not None:
                nested_conditions.append({"range": {"fitness.number_of_barcodes": {"gte": min_barcodes}}})
            
            if nested_conditions:
                s = s.filter("nested", path="fitness", query={
                    "bool": {"must": nested_conditions}
                })
        
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 0:
            s = s.extra(size=min(total_identifiers, 1000))
        else:
            s = s.extra(size=100000)

        logger.info(f'Final Query: {s.to_dict()}')

        response = s.execute()
        
        results = []
        for hit in response.hits:
            try:
                schema = self._convert_hit_to_fitness_schema(hit)
                
                # Post-filter the fitness array to only include entries matching the search criteria
                if schema.fitness and len(schema.fitness) > 0:
                    filtered_fitness = []
                    for entry in schema.fitness:
                        # Apply the same filters used in the nested query
                        if contrast and entry.contrast != contrast:
                            continue
                        if min_lfc is not None and (entry.lfc is None or entry.lfc < min_lfc):
                            continue
                        if max_fdr is not None and (entry.fdr is None or entry.fdr > max_fdr):
                            continue
                        if min_barcodes is not None and (entry.number_of_barcodes is None or entry.number_of_barcodes < min_barcodes):
                            continue
                        
                        filtered_fitness.append(entry)
                    
                    # Only include genes that have at least one matching fitness entry after filtering
                    if filtered_fitness:
                        schema.fitness = filtered_fitness
                        results.append(schema)
                else:
                    logger.warning(f"Gene {schema.locus_tag} has has_fitness=True but empty fitness array")
            except Exception as e:
                logger.warning(f"Error converting hit to schema: {e}")
                continue
        
        return results

    def _convert_hit_to_fitness_schema(self, hit) -> FitnessWithGeneSchema:
        """Convert Elasticsearch hit to FitnessWithGeneSchema."""
        hit_dict = hit.to_dict()
        
        gene_data = {
            "feature_id": hit.meta.id if hasattr(hit, 'meta') else None,
            "feature_type": hit_dict.get("feature_type"),
            "locus_tag": hit_dict.get("locus_tag"),
            "gene_name": hit_dict.get("gene_name"),
            "uniprot_id": hit_dict.get("uniprot_id"),
            "product": hit_dict.get("product"),
            "isolate_name": hit_dict.get("isolate_name"),
            "species_scientific_name": hit_dict.get("species_scientific_name"),
            "species_acronym": hit_dict.get("species_acronym"),
        }
        
        fitness_raw = hit_dict.get("fitness", [])
        fitness_data = []
        
        if fitness_raw:
            for entry in fitness_raw:
                fitness_data.append(FitnessDataSchema(
                    experimental_condition=entry.get("experimental_condition"),
                    contrast=entry.get("contrast"),
                    lfc=entry.get("lfc"),
                    fdr=entry.get("fdr"),
                    number_of_barcodes=entry.get("number_of_barcodes"),
                ))
        
        return FitnessWithGeneSchema(
            **gene_data,
            fitness=fitness_data
        )

