import json
import logging
from typing import Optional, List, Tuple, Dict

from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict
from elasticsearch_dsl import Search, ElasticsearchDslException

from dataportal.schemas import GenePaginationSchema, GeneResponseSchema
from dataportal.services.gene_faceted_search import GeneFacetedSearch
from dataportal.unmanaged_models.gene_data import gene_from_hit
from dataportal.utils.constants import (
    GENE_DEFAULT_SORT_FIELD,
    DEFAULT_SORT,
    DEFAULT_PER_PAGE_CNT,
    SORT_DESC,
    SORT_ASC,
    GENE_ESSENTIALITY,
    DEFAULT_FACET_LIMIT,
    ES_FIELD_PFAM, ES_FIELD_INTERPRO,
    ES_FIELD_KEGG, ES_FIELD_COG_ID,
    ES_FIELD_GENE_NAME, ES_FIELD_ALIAS,
    ES_FIELD_PRODUCT, ES_FIELD_ISOLATE_NAME,
    GENE_SORT_FIELD_STRAIN, FIELD_SEQ_ID,
    ES_FIELD_UNIPROT_ID, ES_FIELD_LOCUS_TAG,
    ES_FIELD_SPECIES_ACRONYM,
    ES_INDEX_GENE, FACET_FIELDS,
)
from dataportal.utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
    InvalidGenomeIdError, )
from dataportal.utils.utils import split_comma_param

logger = logging.getLogger(__name__)


class GeneService:
    INDEX_NAME = ES_INDEX_GENE

    async def autocomplete_gene_suggestions(
            self,
            query: str,
            filter: Optional[str] = None,
            limit: int = None,
            species_acronym: Optional[str] = None,
            isolates: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Provides autocomplete suggestions for genes based on query & filters."""

        try:
            s = Search(index=self.INDEX_NAME)
            s = s.query(
                "multi_match",
                query=query,
                fields=[
                    f"{ES_FIELD_ALIAS}^3",
                    f"{ES_FIELD_ALIAS}.keyword^5",
                    f"{ES_FIELD_GENE_NAME}^2",
                    ES_FIELD_PRODUCT,
                    ES_FIELD_KEGG,
                    ES_FIELD_UNIPROT_ID,
                    ES_FIELD_PFAM,
                    ES_FIELD_COG_ID,
                    ES_FIELD_INTERPRO,
                ],
                type="best_fields"
            )

            if species_acronym:
                s = s.filter("term", **{ES_FIELD_SPECIES_ACRONYM: species_acronym})

            if isolates:
                s = s.filter("terms", **{ES_FIELD_ISOLATE_NAME: isolates})

            parsed_filters = self._parse_filters(filter)
            for key, values in parsed_filters.items():
                if key == GENE_ESSENTIALITY:
                    normalized_values = [v.lower() for v in values]
                    s = s.filter("terms", **{GENE_ESSENTIALITY: normalized_values})
                else:
                    s = s.filter("terms", **{key: values})

            s = s[:limit]

            # logger.info(f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}")

            response = s.execute()

            results = []
            for hit in response:
                gene_obj = gene_from_hit(hit)
                gene_dict = model_to_dict(gene_obj)
                results.append(gene_dict)

            # logger.info(f"Autocomplete results: {results}")
            return results

        except Exception as e:
            logger.error(f"Error fetching gene autocomplete suggestions: {e}", exc_info=True)
            return []

    async def get_gene_by_locus_tag(self, locus_tag: str) -> GeneResponseSchema:
        try:
            gene = await sync_to_async(self.fetch_gene_by_locus_tag, thread_sensitive=False)(locus_tag)
            gene_obj = gene_from_hit(gene)
            gene_dict = model_to_dict(gene_obj)
            return GeneResponseSchema.model_validate(gene_dict)
        except ServiceError:
            logger.error(f"Error in get_gene_by_locus_tag: {locus_tag}")
            raise GeneNotFoundError(f"Could not fetch gene by locus_tag: {locus_tag}")
        except Exception as e:
            logger.error(f"Error in get_gene_by_locus_tag: {e}")
            raise ServiceError(e)

    def fetch_gene_by_locus_tag(self, locus_tag: str):
        s = Search(index=self.INDEX_NAME).query("match", locus_tag=locus_tag)
        response = s.execute()

        if not response.hits:
            raise ServiceError(f"Error in get_gene_by_locus_tag: {locus_tag}")

        return response.hits[0]

    async def get_all_genes(
            self,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = DEFAULT_SORT,
    ) -> GenePaginationSchema:
        try:
            es_query = {"match_all": {}}
            genes, total_results = await self._fetch_paginated_genes(
                es_query,
                page=page,
                per_page=per_page,
                sort_field=sort_field,
                sort_order=sort_order
            )
            return self._create_pagination_schema(
                genes, page, per_page, total_results
            )
        except Exception as e:
            logger.error(f"Error in get_all_genes: {e}")
            raise ServiceError(e)

    async def search_genes(
            self,
            query: str = None,
            isolate_name: Optional[str] = None,
            filter: Optional[str] = None,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = DEFAULT_SORT,
    ) -> GenePaginationSchema:

        try:
            # Build query filters
            es_query = self._build_es_query(query, isolate_name, filter)

            # logger.info(f"Final Elasticsearch Query (Formatted): {json.dumps(es_query, indent=2)}")

            # Call the common function
            genes, total_results = await self._fetch_paginated_genes(
                es_query, page, per_page, sort_field, sort_order
            )

            return self._create_pagination_schema(genes, page, per_page, total_results)

        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            raise ServiceError(e)

    async def get_genes_by_genome(
            self,
            isolate_name: str,
            filter: Optional[str] = None,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = SORT_ASC,
    ) -> GenePaginationSchema:
        try:
            filter_criteria = {"isolate_name": isolate_name}
            parsed_filters = self._parse_filters(filter)
            filter_criteria = await self._apply_filters_for_type_strain(filter_criteria, parsed_filters)

            es_query = self._build_es_query(query=None, isolate_name=filter_criteria.get("isolate_name"),
                                            filter_criteria=filter_criteria)

            genes, total_results = await self._fetch_paginated_genes(
                query=es_query, page=page, per_page=per_page, sort_field=sort_field, sort_order=sort_order
            )

            return self._create_pagination_schema(genes, page, per_page, total_results)

        except Exception as e:
            logger.error(f"Error fetching genes for genome {isolate_name}: {e}")
            raise ServiceError(e)

    async def get_genes_by_multiple_genomes_and_string(
            self,
            isolates: str = None,
            species_acronym: Optional[int] = None,
            query: str = None,
            filter: Optional[str] = None,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = SORT_ASC,
    ) -> GenePaginationSchema:
        """Fetch genes by multiple genomes, species, and optional search query."""

        try:
            isolate_names_list = [id.strip() for id in isolates.split(",")] if isolates else []
            filter_criteria = {"bool": {"must": []}}

            # Filters for genome IDs and species ID
            if isolate_names_list:
                filter_criteria["bool"]["must"].append({"terms": {ES_FIELD_ISOLATE_NAME: isolate_names_list}})
            if species_acronym:
                filter_criteria["bool"]["must"].append({"term": {ES_FIELD_SPECIES_ACRONYM: species_acronym}})

            # Apply additional filters
            parsed_filters = self._parse_filters(filter)
            type_strain_filters = await self._apply_filters_for_type_strain({}, parsed_filters)

            if "bool" in type_strain_filters and "must" in type_strain_filters["bool"]:
                filter_criteria["bool"]["must"].extend(type_strain_filters["bool"]["must"])

            es_query = self._build_es_query(query=query, isolate_name=filter_criteria.get("isolate_name"),
                                            filter_criteria=filter_criteria)

            genes, total_results = await self._fetch_paginated_genes(
                query=es_query, page=page, per_page=per_page, sort_field=sort_field, sort_order=sort_order
            )

            return self._create_pagination_schema(genes, page, per_page, total_results)

        except ValueError:
            logger.error("Invalid genome ID provided")
            raise InvalidGenomeIdError(isolates)
        except Exception as e:
            logger.error(f"Error in get_genes_by_multiple_genomes_and_string: {e}")
            raise ServiceError(e)

    # helper methods

    def _parse_filters(self, filter_str: Optional[str]) -> Dict[str, List[str]]:
        if not filter_str:
            return {}

        filters = {}
        try:
            filter_groups = filter_str.split(";")
            for group in filter_groups:
                if not group.strip():
                    continue
                key, values_str = group.split(":", 1)
                key = key.strip()
                values = [v.strip() for v in values_str.split(",") if v.strip()]
                if values:
                    filters[key] = values
        except ValueError as e:
            logger.error(f"Invalid filter format: {filter_str} — {e}")
            raise ServiceError(
                "Invalid filter format. Use 'key:val1,val2;key2:val3,...'"
            )

        logger.debug(f"Parsed filters: {filters}")
        return filters

    async def _apply_essentiality_filter(self, query: dict, values: list) -> dict:

        if not values:
            return query

        if "bool" not in query:
            query["bool"] = {"must": []}

        query["bool"]["must"].append({"terms": {GENE_ESSENTIALITY: values}})

        return query

    async def _apply_filters_for_type_strain(
            self, query: dict, filters: Dict[str, list]
    ) -> dict:
        if not filters:
            return query

        if "bool" not in query:
            query["bool"] = {"must": []}

        must_filters = [
            {"terms": {key: values}}
            for key, values in filters.items()
            if values
        ]

        query["bool"]["must"].extend(must_filters)

        logger.debug(f"Applied filters to query: {json.dumps(must_filters, indent=2)}")
        return query

    def _create_pagination_schema(
            self, serialized_genes, page, per_page, total_results
    ) -> GenePaginationSchema:
        return GenePaginationSchema(
            results=serialized_genes,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=(page * per_page) < total_results,
            total_results=total_results,
        )

    async def _fetch_paginated_genes(
            self,
            query: dict,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = DEFAULT_SORT,
    ) -> Tuple[List[GeneResponseSchema], int]:
        start = (page - 1) * per_page
        order_prefix = "desc" if sort_order == SORT_DESC else "asc"

        if sort_field == GENE_SORT_FIELD_STRAIN:
            sort_field = ES_FIELD_ISOLATE_NAME

        sort_by = sort_field or GENE_DEFAULT_SORT_FIELD
        sort_by = f"{sort_by}.keyword" if sort_by in [ES_FIELD_GENE_NAME,
                                                      ES_FIELD_ALIAS,
                                                      FIELD_SEQ_ID,
                                                      ES_FIELD_LOCUS_TAG,
                                                      ES_FIELD_PRODUCT] else sort_by

        try:
            s = (
                Search(index=self.INDEX_NAME)
                .query(query)
                .sort({sort_by: {"order": order_prefix}})
                [start: start + per_page]
                .extra(track_total_hits=True)
            )

            # logger.info(f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}")

            response = await sync_to_async(s.execute)()

            results = []
            for hit in response.hits:
                gene_obj = gene_from_hit(hit)
                gene_dict = model_to_dict(gene_obj)
                validated = GeneResponseSchema.model_validate(gene_dict)
                results.append(validated)

            total_results = response.hits.total.value if hasattr(response.hits.total, 'value') else response.hits.total

            return results, total_results

        except Exception as e:
            logger.error(f"Error fetching paginated genes from Elasticsearch: {str(e)}")
            raise ServiceError(e)

    def _build_es_query(self, query: Optional[str], isolate_name: Optional[str],
                        filter_criteria: Optional[dict]) -> dict:
        """Build a properly structured Elasticsearch query for both full-text search and filters."""
        es_query = {"bool": {"must": []}}

        if query:
            es_query["bool"]["must"].append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            ES_FIELD_GENE_NAME,
                            ES_FIELD_ALIAS,
                            ES_FIELD_PRODUCT,
                            ES_FIELD_PFAM,
                            ES_FIELD_INTERPRO
                        ]
                    }
                }
            )

        if isolate_name:
            es_query["bool"]["must"].append({"term": {ES_FIELD_ISOLATE_NAME: isolate_name}})

        if filter_criteria:
            if "bool" in filter_criteria and "must" in filter_criteria["bool"]:
                es_query["bool"]["must"].extend(filter_criteria["bool"]["must"])
            else:
                for field, value in filter_criteria.items():
                    if isinstance(value, list):
                        es_query["bool"]["must"].append({"terms": {field: value}})
                    else:
                        es_query["bool"]["must"].append({"term": {field: value}})

        # logger.info(f"DEBUG - Final Elasticsearch Query (Fixed): {json.dumps(es_query, indent=2)}")
        return es_query

    async def get_faceted_search(self, species_acronym: Optional[str] = None,
                                 isolates: Optional[List[str]] = None,
                                 essentiality: Optional[str] = None,
                                 cog_id: Optional[str] = None,
                                 kegg: Optional[str] = None,
                                 go_term: Optional[str] = None,
                                 pfam: Optional[str] = None,
                                 interpro: Optional[str] = None,
                                 limit: Optional[int] = DEFAULT_FACET_LIMIT):

        try:
            gs = GeneFacetedSearch(
                query='',
                species_acronym=species_acronym,
                essentiality=essentiality,
                isolates=isolates,
                cog_id=split_comma_param(cog_id),
                kegg=split_comma_param(kegg),
                go_term=split_comma_param(go_term),
                pfam=split_comma_param(pfam),
                interpro=split_comma_param(interpro),
                limit=limit
            )

            try:
                response = gs.execute()
            except ElasticsearchDslException as es_exc:
                logger.error("Elasticsearch error occurred during faceted search")
                logger.error(f"ES error message: {str(es_exc)}")
                raise ServiceError("Elasticsearch query failed.")

            selected_map = {
                GENE_ESSENTIALITY: essentiality,
                ES_FIELD_PFAM: pfam,
                ES_FIELD_INTERPRO: interpro,
                ES_FIELD_KEGG: kegg,
                ES_FIELD_COG_ID: cog_id,
            }

            facet_results = {
                field: self.process_aggregation_results(
                    {b[0]: b[1] for b in (getattr(response.facets, field) or [])},
                    selected_values=[selected_map[field]] if selected_map.get(field) else []
                )
                for field in FACET_FIELDS
            }

            facet_results["total_hits"] = response.hits.total.value
            return facet_results
        except Exception as e:
            logger.exception("Error fetching faceted search")
            raise ServiceError(e)

    def process_aggregation_results(
            self,
            aggregation_dict: Dict[str, int],
            selected_values: Optional[List[str]] = None
    ) -> List[Dict[str, object]]:
        """Removes empty keys from aggregation results and marks selected items."""
        selected_values = selected_values or []

        return [
            {
                "value": key,
                "count": count,
                "selected": key in selected_values
            }
            for key, count in aggregation_dict.items()
            if key.strip()
        ]
