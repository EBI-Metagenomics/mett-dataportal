import logging
from typing import List, Dict, Optional

from cachetools import LRUCache

from dataportal.services.base_service import CachedService
from dataportal.utils.constants import (
    GENE_ESSENTIALITY,
    GENE_FIELD_START,
    GENE_FIELD_END,
    ES_FIELD_LOCUS_TAG,
    FIELD_SEQ_ID,
    ES_FIELD_ISOLATE_NAME,
    ES_INDEX_FEATURE,
)

logger = logging.getLogger(__name__)


class EssentialityService(CachedService[Dict, str]):
    """Service for managing essentiality data with caching support."""

    def __init__(self, limit: int = 10, cache_size: int = 10000):
        super().__init__(ES_INDEX_FEATURE, cache_size)
        self.limit = limit
        self.essentiality_cache = LRUCache(maxsize=cache_size)

    async def get_by_id(self, id: str) -> Optional[Dict]:
        """Retrieve essentiality data by strain ID."""
        cache_key = self._get_cache_key("strain", id)
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        # Load data if not in cache
        data = await self.load_essentiality_data_by_strain()
        strain_data = data.get(id, {})
        self._set_cache(cache_key, strain_data)
        return strain_data

    async def get_all(self, **kwargs) -> List[Dict]:
        """Retrieve all essentiality data."""
        data = await self.load_essentiality_data_by_strain()
        return list(data.values())

    async def search(self, query: str) -> List[Dict]:
        """Search essentiality data by strain name."""
        data = await self.load_essentiality_data_by_strain()
        if query in data:
            return [data[query]]
        return []

    async def load_essentiality_data_by_strain(
        self,
    ) -> Dict[str, Dict[str, Dict[str, Dict]]]:
        """Load essentiality data into cache from Elasticsearch."""
        if self.essentiality_cache:
            return self.essentiality_cache

        self.logger.info("Loading essentiality data into cache from Elasticsearch...")

        try:
            s = (
                self._create_search()
                .filter("term", feature_type="gene")
                .query("bool", should=[
                    {"term": {"has_essentiality": True}},
                    {"exists": {"field": GENE_ESSENTIALITY}}
                ])
                .source(
                    [
                        ES_FIELD_ISOLATE_NAME,
                        FIELD_SEQ_ID,
                        ES_FIELD_LOCUS_TAG,
                        GENE_FIELD_START,
                        GENE_FIELD_END,
                        GENE_ESSENTIALITY,
                        "essentiality_data",
                        "has_essentiality",
                    ]
                )[:10000]
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
                if essentiality_data and len(essentiality_data) > 0:
                    # Use the first essentiality_call from the structured data
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
        """Retrieve essentiality data for a given isolate and reference name."""

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
