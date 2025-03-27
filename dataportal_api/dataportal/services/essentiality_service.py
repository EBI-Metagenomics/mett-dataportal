import logging
from typing import List, Dict

from cachetools import LRUCache
from elasticsearch_dsl import Search

from dataportal.utils.constants import (
    GENE_ESSENTIALITY,
    GENE_FIELD_START, GENE_FIELD_END,
    ES_FIELD_LOCUS_TAG, FIELD_SEQ_ID,
    ES_FIELD_ISOLATE_NAME, ES_INDEX_GENE,
)

logger = logging.getLogger(__name__)


class EssentialityService:
    INDEX_NAME = ES_INDEX_GENE

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
                "exists", field=GENE_ESSENTIALITY
            ).source([ES_FIELD_ISOLATE_NAME, FIELD_SEQ_ID, ES_FIELD_LOCUS_TAG, GENE_FIELD_START, GENE_FIELD_END,
                      GENE_ESSENTIALITY])[:10000]

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
