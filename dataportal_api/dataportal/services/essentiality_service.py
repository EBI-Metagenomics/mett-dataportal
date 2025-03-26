import json
import logging
from typing import List, Dict

from asgiref.sync import sync_to_async
from cachetools import LRUCache
from elasticsearch_dsl import Search

from dataportal.schemas import EssentialityTagSchema
from dataportal.utils.constants import (
    GENE_ESSENTIALITY,
    GENE_FIELD_START, GENE_FIELD_END, ES_FIELD_LOCUS_TAG,
)
from dataportal.utils.exceptions import (
    ServiceError,
)
from dataportal.utils.utils import convert_to_camel_case

logger = logging.getLogger(__name__)


class EssentialityService:
    INDEX_NAME = "gene_index"

    def __init__(self, limit: int = 10, cache_size: int = 10000):
        self.limit = limit
        self.essentiality_cache = LRUCache(maxsize=cache_size)

    async def load_essentiality_data_by_strain(self) -> Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]]:
        """Load essentiality data into cache from Elasticsearch."""
        if self.essentiality_cache:
            return self.essentiality_cache

        logger.info("Loading essentiality data into cache from Elasticsearch...")

        try:
            s = Search(index=self.INDEX_NAME).query(
                "exists", field="essentiality"
            ).source(["isolate_name", "seq_id", "locus_tag", "start", "end", "essentiality"])[:10000]

            response = s.execute()
            cache_data = {}

            for hit in response:
                isolate_name = hit.isolate_name
                seq_id = hit.seq_id
                locus_tag = hit.locus_tag
                start = hit.start
                end = hit.end
                essentiality = hit.essentiality if hit.essentiality else "Unknown"

                if isolate_name not in cache_data:
                    cache_data[isolate_name] = {}

                if seq_id not in cache_data[isolate_name]:
                    cache_data[isolate_name][seq_id] = {}

                cache_data[isolate_name][seq_id][locus_tag] = {
                    ES_FIELD_LOCUS_TAG: locus_tag,
                    GENE_FIELD_START: start,
                    GENE_FIELD_END: end,
                    GENE_ESSENTIALITY: essentiality
                }

            self.essentiality_cache.update(cache_data)
            logger.info(f"Loaded {len(response)} essentiality records into cache.")

            return cache_data

        except Exception as e:
            logger.error(f"Error loading essentiality data: {e}")
            return {}

    async def get_essentiality_data_by_strain_and_ref(self, isolate_name: str, ref_name: str) -> Dict[str, Dict]:
        """Retrieve essentiality data for a given isolate and reference name."""

        if not self.essentiality_cache:
            await self.load_essentiality_data_by_strain()

        logger.info(f"Fetching essentiality for isolate: {isolate_name}, reference: {ref_name}")
        isolate_data = self.essentiality_cache.get(isolate_name, {})
        contig_data = isolate_data.get(ref_name, {})

        if not contig_data:
            logger.warning(f"No essentiality data found for isolate '{isolate_name}' and reference '{ref_name}'")
            return {}

        response = {}
        for gene_data in contig_data.values():
            # Ensure all required fields exist
            locus_tag = gene_data.get(ES_FIELD_LOCUS_TAG, "UNKNOWN")
            start = gene_data.get(GENE_FIELD_START, 0)
            end = gene_data.get(GENE_FIELD_END, 0)
            essentiality = gene_data.get(GENE_ESSENTIALITY, "Unknown")

            response[locus_tag] = {
                ES_FIELD_LOCUS_TAG: locus_tag,
                GENE_FIELD_START: start,
                GENE_FIELD_END: end,
                GENE_ESSENTIALITY: essentiality
            }

        return response

    async def get_unique_essentiality_tags(self) -> list[EssentialityTagSchema]:
        """Fetch unique essentiality values from gene_index and process them."""

        try:
            # ✅ Query Elasticsearch for unique `essentiality` values
            search_query = Search(index=self.INDEX_NAME).source([]).extra(
                size=0, aggs={"unique_essentiality": {"terms": {"field": "essentiality", "size": 100}}}
            )

            logger.info(f"Final Elasticsearch Query (Formatted): {json.dumps(search_query.to_dict(), indent=2)}")

            # ✅ Execute the query
            response = await sync_to_async(search_query.execute)()

            # ✅ Extract unique essentiality values
            unique_values = [bucket["key"] for bucket in response.aggregations.unique_essentiality.buckets]

            # ✅ Process values (convert to label format)
            processed_tags = [
                EssentialityTagSchema(name=value, label=convert_to_camel_case(value.replace("_", " ")))
                for value in unique_values
            ]

            return processed_tags

        except Exception as e:
            logger.error(f"Error fetching essentiality tags from Elasticsearch: {e}")
            raise ServiceError(e)
