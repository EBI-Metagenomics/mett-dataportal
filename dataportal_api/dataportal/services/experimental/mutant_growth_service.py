import logging
from typing import Optional, List

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search

from dataportal.schema.experimental.mutant_growth_schemas import (
    MutantGrowthWithGeneSchema,
    MutantGrowthDataSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import INDEX_FEATURES
from dataportal.utils.exceptions import ServiceError, GeneNotFoundError

logger = logging.getLogger(__name__)


class MutantGrowthService(BaseService[MutantGrowthWithGeneSchema, str]):
    """Service for retrieving mutant growth data."""

    def __init__(self):
        super().__init__(INDEX_FEATURES)

    async def get_by_id(self, locus_tag: str) -> Optional[MutantGrowthWithGeneSchema]:
        """Retrieve mutant growth data for a gene by locus tag."""
        try:
            result = await sync_to_async(self._fetch_mutant_growth_by_identifier)(locus_tag)
            return result
        except GeneNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching mutant growth data for {locus_tag}: {e}")
            raise ServiceError(f"Failed to fetch mutant growth data: {str(e)}")

    async def get_all(self, **kwargs) -> List[MutantGrowthWithGeneSchema]:
        """Not implemented - use search instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search(self, **kwargs) -> List[MutantGrowthWithGeneSchema]:
        """Not implemented - use search_with_filters instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search_with_filters(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        media: Optional[str] = None,
        experimental_condition: Optional[str] = None,
        min_doubling_time: Optional[float] = None,
        max_doubling_time: Optional[float] = None,
        exclude_double_picked: Optional[bool] = None,
    ) -> List[MutantGrowthWithGeneSchema]:
        """Search for mutant growth data with filters."""
        try:
            results = await sync_to_async(self._fetch_mutant_growth_by_identifiers)(
                locus_tags=locus_tags or [],
                uniprot_ids=uniprot_ids or [],
                media=media,
                experimental_condition=experimental_condition,
                min_doubling_time=min_doubling_time,
                max_doubling_time=max_doubling_time,
                exclude_double_picked=exclude_double_picked,
            )
            return results
        except Exception as e:
            logger.error(f"Error searching mutant growth data with filters: {e}")
            raise ServiceError(f"Failed to search mutant growth data: {str(e)}")

    def _fetch_mutant_growth_by_identifier(self, identifier: str) -> MutantGrowthWithGeneSchema:
        """Fetch mutant growth data for a single identifier."""
        s = (
            Search(index=self.index_name)
            .filter("term", feature_type="gene")
            .filter("term", has_mutant_growth=True)
            .query("bool", should=[
                {"term": {"locus_tag.keyword": identifier}},
                {"term": {"uniprot_id": identifier}},
            ])
            .extra(size=1)
        )
        
        response = s.execute()
        
        if not response.hits:
            raise GeneNotFoundError(f"Gene with identifier '{identifier}' not found or has no mutant growth data")
        
        hit = response.hits[0]
        return self._convert_hit_to_mutant_growth_schema(hit)

    def _fetch_mutant_growth_by_identifiers(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        media: Optional[str] = None,
        experimental_condition: Optional[str] = None,
        min_doubling_time: Optional[float] = None,
        max_doubling_time: Optional[float] = None,
        exclude_double_picked: Optional[bool] = None,
    ) -> List[MutantGrowthWithGeneSchema]:
        """Fetch mutant growth data for multiple identifiers."""
        locus_tags = locus_tags or []
        uniprot_ids = uniprot_ids or []
        
        s = (
            Search(index=self.index_name)
            .filter("term", has_mutant_growth=True)  # Fast boolean filter
        )
        
        should_conditions = []
        if locus_tags:
            should_conditions.append({"terms": {"locus_tag.keyword": locus_tags}})
        if uniprot_ids:
            should_conditions.append({"terms": {"uniprot_id": uniprot_ids}})
        
        if should_conditions:
            s = s.query("bool", should=should_conditions, minimum_should_match=1)
        
        # Apply nested filters for mutant_growth
        if any([media, experimental_condition, min_doubling_time is not None, max_doubling_time is not None, exclude_double_picked is not None]):
            nested_conditions = []
            
            if media:
                nested_conditions.append({"term": {"mutant_growth.media": media}})
            if experimental_condition:
                nested_conditions.append({"term": {"mutant_growth.experimental_condition": experimental_condition}})
            if min_doubling_time is not None:
                nested_conditions.append({"range": {"mutant_growth.doubling_time": {"gte": min_doubling_time}}})
            if max_doubling_time is not None:
                nested_conditions.append({"range": {"mutant_growth.doubling_time": {"lte": max_doubling_time}}})
            if exclude_double_picked:
                nested_conditions.append({"term": {"mutant_growth.isdoublepicked": False}})
            
            if nested_conditions:
                s = s.filter("nested", path="mutant_growth", query={
                    "bool": {"must": nested_conditions}
                })
        
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 0:
            s = s.extra(size=min(total_identifiers, 1000))
        else:
            s = s.extra(size=100000)
        
        response = s.execute()
        
        results = []
        for hit in response.hits:
            try:
                schema = self._convert_hit_to_mutant_growth_schema(hit)
                
                # Post-filter the mutant_growth array to only include entries matching the search criteria
                if schema.mutant_growth and len(schema.mutant_growth) > 0:
                    filtered_data = []
                    for entry in schema.mutant_growth:
                        # Apply the same filters used in the nested query
                        if experimental_condition and entry.experimental_condition != experimental_condition:
                            continue
                        if media and entry.media != media:
                            continue
                        if min_doubling_time is not None and (entry.doubling_time is None or entry.doubling_time < min_doubling_time):
                            continue
                        if max_doubling_time is not None and (entry.doubling_time is None or entry.doubling_time > max_doubling_time):
                            continue
                        if exclude_double_picked and entry.isdoublepicked:
                            continue
                        
                        filtered_data.append(entry)
                    
                    # Only include genes that have at least one matching mutant_growth entry after filtering
                    if filtered_data:
                        schema.mutant_growth = filtered_data
                        results.append(schema)
                else:
                    logger.warning(f"Gene {schema.locus_tag} has has_mutant_growth=True but empty mutant_growth array")
            except Exception as e:
                logger.warning(f"Error converting hit to schema: {e}")
                continue
        
        return results

    def _convert_hit_to_mutant_growth_schema(self, hit) -> MutantGrowthWithGeneSchema:
        """Convert Elasticsearch hit to MutantGrowthWithGeneSchema."""
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
        
        mutant_growth_raw = hit_dict.get("mutant_growth", [])
        mutant_growth_data = []
        
        if mutant_growth_raw:
            for entry in mutant_growth_raw:
                mutant_growth_data.append(MutantGrowthDataSchema(
                    doubling_time=entry.get("doubling_time"),
                    isdoublepicked=entry.get("isdoublepicked"),
                    brep=entry.get("brep"),
                    plate384=entry.get("plate384"),
                    well384=entry.get("well384"),
                    percent_from_start=entry.get("percent_from_start"),
                    media=entry.get("media"),
                    experimental_condition=entry.get("experimental_condition"),
                ))
        
        return MutantGrowthWithGeneSchema(
            **gene_data,
            mutant_growth=mutant_growth_data
        )

