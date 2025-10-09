import logging
from typing import Optional, List, Dict

from asgiref.sync import sync_to_async
from cachetools import LRUCache
from elasticsearch_dsl import Search

from dataportal.schema.experimental.essentiality_schemas import (
    EssentialityWithGeneSchema,
    EssentialityDataSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import (
    INDEX_FEATURES,
    GENE_FIELD_ESSENTIALITY,
    GENE_FIELD_START,
    GENE_FIELD_END,
    GENE_FIELD_LOCUS_TAG,
    FIELD_SEQ_ID,
    GENOME_FIELD_ISOLATE_NAME,
)
from dataportal.utils.exceptions import ServiceError, GeneNotFoundError

logger = logging.getLogger(__name__)


class EssentialityService(BaseService[EssentialityWithGeneSchema, str]):
    """
    Comprehensive service for retrieving essentiality data.
    
    Supports both:
    1. Gene-centric API methods (get_by_id, search_with_filters)
    2. Genome browser methods (get_essentiality_data_by_strain_and_ref) with caching
    """

    def __init__(self, limit: int = 10, cache_size: int = 10000):
        super().__init__(INDEX_FEATURES)
        self.limit = limit
        self.essentiality_cache = LRUCache(maxsize=cache_size)

    async def get_by_id(self, locus_tag: str) -> Optional[EssentialityWithGeneSchema]:
        """Retrieve essentiality data for a gene by locus tag."""
        try:
            result = await sync_to_async(self._fetch_essentiality_by_identifier)(locus_tag)
            return result
        except GeneNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching essentiality data for {locus_tag}: {e}")
            raise ServiceError(f"Failed to fetch essentiality data: {str(e)}")

    async def get_all(self, **kwargs) -> List[EssentialityWithGeneSchema]:
        """Not implemented - use search instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search(self, **kwargs) -> List[EssentialityWithGeneSchema]:
        """Not implemented - use search_with_filters instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search_with_filters(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        essentiality_call: Optional[str] = None,
        experimental_condition: Optional[str] = None,
        min_tas_in_locus: Optional[int] = None,
        min_tas_hit: Optional[float] = None,
        element: Optional[str] = None,
    ) -> List[EssentialityWithGeneSchema]:
        """Search for essentiality data with filters."""
        try:
            results = await sync_to_async(self._fetch_essentiality_by_identifiers)(
                locus_tags=locus_tags or [],
                uniprot_ids=uniprot_ids or [],
                essentiality_call=essentiality_call,
                experimental_condition=experimental_condition,
                min_tas_in_locus=min_tas_in_locus,
                min_tas_hit=min_tas_hit,
                element=element,
            )
            return results
        except Exception as e:
            logger.error(f"Error searching essentiality data with filters: {e}")
            raise ServiceError(f"Failed to search essentiality data: {str(e)}")

    def _fetch_essentiality_by_identifier(self, identifier: str) -> EssentialityWithGeneSchema:
        """Fetch essentiality data for a single identifier."""
        s = (
            Search(index=self.index_name)
            .filter("term", feature_type="gene")
            .filter("term", has_essentiality=True)
            .query("bool", should=[
                {"term": {"locus_tag.keyword": identifier}},
                {"term": {"uniprot_id": identifier}},
            ])
            .extra(size=1)
        )
        
        response = s.execute()
        
        if not response.hits:
            raise GeneNotFoundError(f"Gene with identifier '{identifier}' not found or has no essentiality data")
        
        hit = response.hits[0]
        return self._convert_hit_to_essentiality_schema(hit)

    def _fetch_essentiality_by_identifiers(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        essentiality_call: Optional[str] = None,
        experimental_condition: Optional[str] = None,
        min_tas_in_locus: Optional[int] = None,
        min_tas_hit: Optional[float] = None,
        element: Optional[str] = None,
    ) -> List[EssentialityWithGeneSchema]:
        """Fetch essentiality data for multiple identifiers."""
        locus_tags = locus_tags or []
        uniprot_ids = uniprot_ids or []
        
        s = (
            Search(index=self.index_name)
            .filter("term", has_essentiality=True)  # Fast boolean filter
        )
        
        should_conditions = []
        if locus_tags:
            should_conditions.append({"terms": {"locus_tag.keyword": locus_tags}})
        if uniprot_ids:
            should_conditions.append({"terms": {"uniprot_id": uniprot_ids}})
        
        if should_conditions:
            s = s.query("bool", should=should_conditions, minimum_should_match=1)
        
        # Apply nested filters for essentiality_data
        if any([essentiality_call, experimental_condition, min_tas_in_locus is not None, min_tas_hit is not None, element]):
            nested_conditions = []
            
            if essentiality_call:
                nested_conditions.append({"term": {"essentiality_data.essentiality_call": essentiality_call}})
            if experimental_condition:
                nested_conditions.append({"term": {"essentiality_data.experimental_condition": experimental_condition}})
            if min_tas_in_locus is not None:
                # Map API param (lowercase) to ES field (camelCase)
                nested_conditions.append({"range": {"essentiality_data.TAs_in_locus": {"gte": min_tas_in_locus}}})
            if min_tas_hit is not None:
                # Map API param (lowercase) to ES field (camelCase)
                nested_conditions.append({"range": {"essentiality_data.TAs_hit": {"gte": min_tas_hit}}})
            if element:
                nested_conditions.append({"term": {"essentiality_data.element": element}})
            
            if nested_conditions:
                s = s.filter("nested", path="essentiality_data", query={
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
                schema = self._convert_hit_to_essentiality_schema(hit)
                
                # Post-filter the essentiality_data array to only include entries matching the search criteria
                if schema.essentiality_data and len(schema.essentiality_data) > 0:
                    filtered_data = []
                    for entry in schema.essentiality_data:
                        # Apply the same filters used in the nested query
                        if essentiality_call and entry.essentiality_call != essentiality_call:
                            continue
                        if experimental_condition and entry.experimental_condition != experimental_condition:
                            continue
                        if min_tas_in_locus is not None and (entry.tas_in_locus is None or entry.tas_in_locus < min_tas_in_locus):
                            continue
                        if min_tas_hit is not None and (entry.tas_hit is None or entry.tas_hit < min_tas_hit):
                            continue
                        if element and entry.element != element:
                            continue
                        
                        filtered_data.append(entry)
                    
                    # Only include genes that have at least one matching essentiality entry after filtering
                    if filtered_data:
                        schema.essentiality_data = filtered_data
                        results.append(schema)
                else:
                    logger.warning(f"Gene {schema.locus_tag} has has_essentiality=True but empty essentiality_data array")
            except Exception as e:
                logger.warning(f"Error converting hit to schema: {e}")
                continue
        
        return results

    def _convert_hit_to_essentiality_schema(self, hit) -> EssentialityWithGeneSchema:
        """Convert Elasticsearch hit to EssentialityWithGeneSchema."""
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
        
        essentiality_raw = hit_dict.get("essentiality_data", [])
        essentiality_data = []
        
        if essentiality_raw:
            for entry in essentiality_raw:
                essentiality_data.append(EssentialityDataSchema(
                    tas_in_locus=entry.get("TAs_in_locus"),  # ES uses TAs_in_locus
                    tas_hit=entry.get("TAs_hit"),  # ES uses TAs_hit
                    essentiality_call=entry.get("essentiality_call"),
                    experimental_condition=entry.get("experimental_condition"),
                    element=entry.get("element"),
                ))
        
        return EssentialityWithGeneSchema(
            **gene_data,
            essentiality_data=essentiality_data
        )
    
    # ============================================================================
    # Genome Browser Methods (with caching)
    # ============================================================================
    
    async def load_essentiality_data_by_strain(self) -> Dict[str, Dict[str, Dict[str, Dict]]]:
        """Load essentiality data into cache from Elasticsearch for genome browser."""
        if self.essentiality_cache:
            return self.essentiality_cache

        self.logger.info("Loading essentiality data into cache from Elasticsearch...")

        try:
            s = (
                self._create_search()
                .filter("term", feature_type="gene")
                .query("bool", should=[
                    {"term": {"has_essentiality": True}},
                    {"exists": {"field": GENE_FIELD_ESSENTIALITY}}
                ])
                .source([
                    GENOME_FIELD_ISOLATE_NAME,
                    FIELD_SEQ_ID,
                    GENE_FIELD_LOCUS_TAG,
                    GENE_FIELD_START,
                    GENE_FIELD_END,
                    GENE_FIELD_ESSENTIALITY,
                    "essentiality_data",
                    "has_essentiality",
                ])[:10000]
            )

            response = await self._execute_search(s)
            cache_data = {}

            for hit in response:
                isolate_name = hit.isolate_name
                seq_id = hit.seq_id
                locus_tag = hit.locus_tag
                start = hit.start
                end = hit.end
                has_essentiality = getattr(hit, "has_essentiality", False)
                essentiality_data = getattr(hit, "essentiality_data", [])
                
                # Get essentiality from essentiality_data or fallback to legacy field
                essentiality_call = None
                if essentiality_data and len(essentiality_data) > 0:
                    first_essentiality = essentiality_data[0]
                    essentiality_call = getattr(first_essentiality, "essentiality_call", None)

                if isolate_name not in cache_data:
                    cache_data[isolate_name] = {}

                if seq_id not in cache_data[isolate_name]:
                    cache_data[isolate_name][seq_id] = {}

                cache_data[isolate_name][seq_id][locus_tag] = {
                    "locus_tag": locus_tag,
                    "start": start,
                    "end": end,
                    "essentiality": essentiality_call,
                }

            self.essentiality_cache.update(cache_data)
            self.logger.info(f"Loaded {len(response)} essentiality records into cache.")

            return cache_data

        except Exception as e:
            self._handle_elasticsearch_error(e, "load_essentiality_data_by_strain")

    async def get_essentiality_data_by_strain_and_ref(
        self, isolate_name: str, ref_name: str
    ) -> Dict[str, Dict]:
        """
        Retrieve essentiality data for a given isolate and reference name.
        
        Used by genome browser to display essentiality tracks on contigs.
        Returns data in format optimized for visualization.
        """
        if not self.essentiality_cache:
            await self.load_essentiality_data_by_strain()

        self.logger.info(
            f"Fetching essentiality for isolate: {isolate_name}, reference: {ref_name}"
        )
        isolate_data = self.essentiality_cache.get(isolate_name, {})
        contig_data = isolate_data.get(ref_name, {})

        if not contig_data:
            self.logger.warning(
                f"No essentiality data found for isolate '{isolate_name}' and reference '{ref_name}'"
            )
            return {}

        response = {}
        for locus_tag, gene_data in contig_data.items():
            response[locus_tag] = {
                "locus_tag": gene_data["locus_tag"],
                "start": gene_data["start"],
                "end": gene_data["end"],
                "essentiality": gene_data["essentiality"],
            }

        return response

