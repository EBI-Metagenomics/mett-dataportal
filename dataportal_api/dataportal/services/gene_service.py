import json
import logging
from typing import Optional, List, Tuple, Dict, Any

from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict
from elasticsearch_dsl import Search, connections

from dataportal.schema.gene_schemas import (
    GenePaginationSchema,
    GeneResponseSchema,
    GeneProteinSeqSchema,
    GeneSearchQuerySchema,
    GeneFacetedSearchQuerySchema,
    GeneAdvancedSearchQuerySchema,
    GeneAutocompleteQuerySchema,
)
from dataportal.services.base_service import BaseService
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
    ES_FIELD_PFAM,
    ES_FIELD_INTERPRO,
    ES_FIELD_KEGG,
    ES_FIELD_COG_ID,
    ES_FIELD_GENE_NAME,
    ES_FIELD_ALIAS,
    ES_FIELD_PRODUCT,
    ES_FIELD_ISOLATE_NAME,
    GENE_SORT_FIELD_STRAIN,
    FIELD_SEQ_ID,
    ES_FIELD_UNIPROT_ID,
    ES_FIELD_LOCUS_TAG,
    ES_FIELD_SPECIES_ACRONYM,
    ES_INDEX_FEATURE,
    FACET_FIELDS,
    ES_FIELD_COG_FUNCATS,
    SCROLL_BATCH_SIZE,
    SCROLL_MAX_RESULTS,
    SCROLL_TIMEOUT,
    ES_FIELD_GO_TERM,
)
from dataportal.utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
    InvalidGenomeIdError,
)
from dataportal.utils.utils import split_comma_param

logger = logging.getLogger(__name__)


class GeneService(BaseService[GeneResponseSchema, Dict[str, Any]]):
    """Service for managing gene data operations in the read-only data portal."""

    def __init__(self):
        super().__init__(ES_INDEX_FEATURE)

    async def get_by_id(self, id: str) -> Optional[GeneResponseSchema]:
        """Retrieve a single gene by ID (locus tag)."""
        try:
            return await self.get_gene_by_locus_tag(id)
        except GeneNotFoundError:
            return None
        except Exception as e:
            self._handle_elasticsearch_error(e, f"get_by_id for gene {id}")

    async def get_all(self, **kwargs) -> List[GeneResponseSchema]:
        """Retrieve all genes with optional filtering."""
        try:
            page = kwargs.get("page", 1)
            per_page = kwargs.get("per_page", DEFAULT_PER_PAGE_CNT)
            sort_field = kwargs.get("sort_field")
            sort_order = kwargs.get("sort_order", DEFAULT_SORT)

            pagination_result = await self.get_all_genes(
                page=page,
                per_page=per_page,
                sort_field=sort_field,
                sort_order=sort_order,
            )

            return pagination_result.results
        except Exception as e:
            self._handle_elasticsearch_error(e, "get_all genes")

    async def search(self, query: Dict[str, Any]) -> List[GeneResponseSchema]:
        """Search genes based on query parameters."""
        try:
            # Convert dict to GeneSearchQuerySchema
            search_params = GeneSearchQuerySchema(
                query=query.get("query", ""),
                page=query.get("page", 1),
                per_page=query.get("per_page", DEFAULT_PER_PAGE_CNT),
                sort_field=query.get("sort_field"),
                sort_order=query.get("sort_order", DEFAULT_SORT),
            )

            pagination_result = await self.search_genes(search_params)
            return pagination_result.results
        except Exception as e:
            self._handle_elasticsearch_error(e, "search genes")

    def _convert_hit_to_entity(self, hit) -> GeneResponseSchema:
        """Convert Elasticsearch hit to GeneResponseSchema."""
        gene_obj = gene_from_hit(hit)
        gene_dict = model_to_dict(gene_obj)
        return GeneResponseSchema.model_validate(gene_dict)

    # Original methods with minimal changes - keeping existing query logic
    async def autocomplete_gene_suggestions(
        self,
        params: GeneAutocompleteQuerySchema,
    ) -> List[Dict]:
        try:
            isolate_list = (
                [gid.strip() for gid in params.isolates.split(",") if gid.strip()]
                if params.isolates
                else None
            )

            result = await self._autocomplete_impl(
                query=params.query,
                filter=params.filter,
                limit=params.limit,
                species_acronym=params.species_acronym,
                isolates=isolate_list,
            )

            return result

        except Exception as e:
            logger.error(
                f"Error fetching gene autocomplete suggestions: {e}", exc_info=True
            )
            return []

    async def _autocomplete_impl(
        self,
        query: str,
        filter: Optional[str] = None,
        limit: int = None,
        species_acronym: Optional[str] = None,
        isolates: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Internal implementation of gene autocomplete."""
        try:
            s = Search(index=self.index_name)
            # Always filter for genes only in feature_index
            s = s.filter("term", feature_type="gene")
            s = s.query(
                "multi_match",
                query=query,
                fields=[
                    f"{ES_FIELD_ALIAS}^3",
                    f"{ES_FIELD_ALIAS}.keyword^5",
                    f"{ES_FIELD_GENE_NAME}^2",
                    ES_FIELD_LOCUS_TAG,
                    f"{ES_FIELD_LOCUS_TAG}.keyword^6",
                    ES_FIELD_PRODUCT,
                    ES_FIELD_KEGG,
                    ES_FIELD_UNIPROT_ID,
                    ES_FIELD_PFAM,
                    ES_FIELD_COG_ID,
                    ES_FIELD_INTERPRO,
                ],
                type="best_fields",
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

            logger.info(
                f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}"
            )

            response = await sync_to_async(s.execute)()

            results = []
            for hit in response:
                gene_obj = gene_from_hit(hit)
                gene_dict = model_to_dict(gene_obj)
                results.append(gene_dict)

            # logger.info(f"Autocomplete results: {results}")
            return results

        except Exception as e:
            logger.error(f"Error in autocomplete implementation: {e}")
            raise ServiceError(e)

    async def get_gene_by_locus_tag(self, locus_tag: str) -> GeneResponseSchema:
        try:
            gene = await sync_to_async(
                self.fetch_gene_by_locus_tag, thread_sensitive=False
            )(locus_tag)
            gene_obj = gene_from_hit(gene)
            gene_dict = model_to_dict(gene_obj)
            return GeneResponseSchema.model_validate(gene_dict)
        except ServiceError:
            logger.error(f"Error in get_gene_by_locus_tag: {locus_tag}")
            raise GeneNotFoundError(f"Could not fetch gene by locus_tag: {locus_tag}")
        except Exception as e:
            logger.error(f"Error in get_gene_by_locus_tag: {e}")
            raise GeneNotFoundError(f"Could not fetch gene by locus_tag: {locus_tag}")

    def fetch_gene_by_locus_tag(self, locus_tag: str):
        s = Search(index=self.index_name).filter("term", feature_type="gene").query("match", locus_tag=locus_tag)
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
                sort_order=sort_order,
            )
            return self._create_pagination_schema(genes, page, per_page, total_results)
        except Exception as e:
            logger.error(f"Error in get_all_genes: {e}")
            raise ServiceError(e)

    async def search_genes(
        self,
        params: GeneSearchQuerySchema,
    ) -> GenePaginationSchema:
        try:
            # Build query filters
            es_query = self._build_es_query(None, params.query, None, None)

            # Call the common function
            genes, total_results = await self._fetch_paginated_genes(
                es_query,
                params.page,
                params.per_page,
                params.sort_field,
                params.sort_order,
            )

            return self._create_pagination_schema(
                genes, params.page, params.per_page, total_results
            )

        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            raise ServiceError(e)

    async def get_genes_by_genome(
        self,
        isolate_name: str,
        filter: Optional[str] = None,
        filter_operators: Optional[str] = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = SORT_ASC,
    ) -> GenePaginationSchema:
        try:
            filter_criteria = {"isolate_name": isolate_name}
            parsed_filters = self._parse_filters(filter)
            parsed_filter_operators = self._parse_filter_operators(filter_operators)
            filter_criteria = await self._apply_filters_for_type_strain(
                filter_criteria, parsed_filters, parsed_filter_operators
            )

            es_query = self._build_es_query(
                params=None,
                query=None,
                isolate_name=filter_criteria.get("isolate_name"),
                filter_criteria=filter_criteria,
            )

            genes, total_results = await self._fetch_paginated_genes(
                query=es_query,
                page=page,
                per_page=per_page,
                sort_field=sort_field,
                sort_order=sort_order,
            )

            return self._create_pagination_schema(genes, page, per_page, total_results)

        except Exception as e:
            logger.error(f"Error fetching genes for genome {isolate_name}: {e}")
            raise ServiceError(e)

    async def get_genes_by_multiple_genomes_and_string(
        self,
        params: GeneAdvancedSearchQuerySchema,
        use_scroll: bool = False,
    ) -> GenePaginationSchema:
        try:
            logger.info(
                f"DEBUG - Received params: query='{params.query}', isolates='{params.isolates}', species='{params.species_acronym}'"
            )

            isolate_names_list = (
                [id.strip() for id in params.isolates.split(",")]
                if params.isolates
                else []
            )
            logger.info(f"DEBUG - Parsed isolate names: {isolate_names_list}")

            filter_criteria = {"bool": {"must": []}}

            # Filters for genome IDs and species ID
            if isolate_names_list:
                filter_criteria["bool"]["must"].append(
                    {"terms": {ES_FIELD_ISOLATE_NAME: isolate_names_list}}
                )
                logger.info(
                    f"DEBUG - Added isolate filter: {filter_criteria['bool']['must']}"
                )
            if params.species_acronym:
                filter_criteria["bool"]["must"].append(
                    {"term": {ES_FIELD_SPECIES_ACRONYM: params.species_acronym}}
                )

            # Apply additional filters
            parsed_filters = self._parse_filters(params.filter)
            parsed_filter_operators = self._parse_filter_operators(
                params.filter_operators
            )
            type_strain_filters = await self._apply_filters_for_type_strain(
                {}, parsed_filters, parsed_filter_operators
            )

            if "bool" in type_strain_filters and "must" in type_strain_filters["bool"]:
                filter_criteria["bool"]["must"].extend(
                    type_strain_filters["bool"]["must"]
                )

            logger.info(
                f"DEBUG - Final filter_criteria before building ES query: {json.dumps(filter_criteria, indent=2)}"
            )

            es_query = self._build_es_query(
                params=params,
                query=params.query,
                isolate_name=None,  # Don't pass isolate_name since it's already in filter_criteria
                filter_criteria=filter_criteria,
            )

            if use_scroll:
                # Use scroll API for large downloads
                genes, total_results = await self._fetch_all_genes_with_scroll(
                    query=es_query,
                    sort_field=params.sort_field,
                    sort_order=params.sort_order,
                )
            else:
                # Use regular pagination for normal requests
                genes, total_results = await self._fetch_paginated_genes(
                    query=es_query,
                    page=params.page,
                    per_page=params.per_page,
                    sort_field=params.sort_field,
                    sort_order=params.sort_order,
                )

            return self._create_pagination_schema(
                genes, params.page, params.per_page, total_results
            )

        except ValueError:
            logger.error("Invalid genome ID provided")
            raise InvalidGenomeIdError(params.isolates)
        except Exception as e:
            logger.error(f"Error in get_genes_by_multiple_genomes_and_string: {e}")
            raise ServiceError(e)

    async def _fetch_all_genes_with_scroll(
        self,
        query: dict,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = DEFAULT_SORT,
    ) -> Tuple[List[GeneResponseSchema], int]:
        """Fetch all genes using Elasticsearch scroll API for large downloads."""
        order_prefix = "desc" if sort_order == SORT_DESC else "asc"

        if sort_field == GENE_SORT_FIELD_STRAIN:
            sort_field = ES_FIELD_ISOLATE_NAME

        sort_by = sort_field or GENE_DEFAULT_SORT_FIELD
        sort_by = (
            f"{sort_by}.keyword"
            if sort_by
            in [
                ES_FIELD_GENE_NAME,
                ES_FIELD_ALIAS,
                FIELD_SEQ_ID,
                ES_FIELD_LOCUS_TAG,
                ES_FIELD_PRODUCT,
            ]
            else sort_by
        )

        try:
            es_client = connections.get_connection()
            search_body = {
                "query": query,
                "sort": [{sort_by: {"order": order_prefix}}],
                "size": SCROLL_BATCH_SIZE,
            }

            logger.info(
                f"Starting scroll search with query: {json.dumps(search_body, indent=2)}"
            )

            # Execute initial search
            response = await sync_to_async(
                lambda: es_client.search(
                    index=self.index_name, body=search_body, scroll=SCROLL_TIMEOUT
                )
            )()

            results = []
            total_results = 0
            max_results = SCROLL_MAX_RESULTS
            batch_count = 0
            scroll_id = response["_scroll_id"]

            # Process all batches
            while len(response["hits"]["hits"]) > 0 and total_results < max_results:
                batch_count += 1
                for hit_data in response["hits"]["hits"]:
                    # Create a mock hit object that has to_dict() method
                    class MockHit:
                        def __init__(self, source):
                            self._source = source

                        def to_dict(self):
                            return self._source

                    mock_hit = MockHit(hit_data["_source"])
                    gene_obj = gene_from_hit(mock_hit)
                    gene_dict = model_to_dict(gene_obj)
                    validated = GeneResponseSchema.model_validate(gene_dict)
                    results.append(validated)

                total_results += len(response["hits"]["hits"])
                logger.info(
                    f"Fetched {total_results} genes in {batch_count} batches..."
                )

                # Get next batch using scroll
                try:
                    response = await sync_to_async(
                        lambda: es_client.scroll(
                            scroll_id=scroll_id, scroll=SCROLL_TIMEOUT
                        )
                    )()
                    scroll_id = response["_scroll_id"]
                except Exception as scroll_error:
                    logger.error(f"Error in scroll batch {batch_count}: {scroll_error}")
                    break

            if total_results >= max_results:
                logger.warning(
                    f"Reached maximum result limit of {max_results}. Some results may be truncated."
                )

            logger.info(
                f"Scroll search completed. Total genes fetched: {total_results}"
            )
            return results, total_results

        except Exception as e:
            logger.error(f"Error fetching genes with scroll API: {str(e)}")
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

    def _parse_filter_operators(self, filter_str: Optional[str]) -> Dict[str, str]:
        if not filter_str:
            return {}

        operators = {}
        try:
            groups = filter_str.split(";")
            for group in groups:
                if not group.strip():
                    continue
                key, op = group.split(":", 1)
                operators[key.strip()] = op.strip().upper()
        except ValueError as e:
            logger.error(f"Invalid filter_operators format: {filter_str} — {e}")
            raise ServiceError(
                "Invalid filter_operators format. Use 'key:AND;key2:OR,...'"
            )

        return operators

    async def _apply_essentiality_filter(self, query: dict, values: list) -> dict:

        if not values:
            return query

        if "bool" not in query:
            query["bool"] = {"must": []}

        query["bool"]["must"].append({"terms": {GENE_ESSENTIALITY: values}})

        return query

    async def _apply_filters_for_type_strain(
        self,
        base_filters: Dict,
        filters: Dict[str, List[str]],
        facet_operators: Optional[Dict[str, str]] = None,
    ) -> Dict:
        facet_operators = facet_operators or {}
        bool_query = {"bool": {"must": []}}

        # Add base filters to the "must" clause first (these are required filters)
        for key, val in base_filters.items():
            bool_query["bool"]["must"].append({"term": {key: val}})

        # Process additional filters with operators
        for key, values in filters.items():
            if not values:
                continue

            operator = (facet_operators.get(key) or "OR").upper()

            if operator == "AND":
                for val in values:
                    bool_query["bool"]["must"].append({"term": {key: val}})
            else:
                bool_query["bool"]["must"].append({"terms": {key: values}})

        return bool_query

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
        sort_by = (
            f"{sort_by}.keyword"
            if sort_by
            in [
                ES_FIELD_GENE_NAME,
                ES_FIELD_ALIAS,
                FIELD_SEQ_ID,
                ES_FIELD_LOCUS_TAG,
                ES_FIELD_PRODUCT,
            ]
            else sort_by
        )

        try:
            s = (
                Search(index=self.index_name)
                .filter("term", feature_type="gene")
                .query(query)
                .sort({sort_by: {"order": order_prefix}})[start : start + per_page]
                .extra(track_total_hits=True)
            )

            logger.info(
                f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}"
            )

            response = await sync_to_async(s.execute)()

            results = []
            for hit in response.hits:
                gene_obj = gene_from_hit(hit)
                gene_dict = model_to_dict(gene_obj)
                validated = GeneResponseSchema.model_validate(gene_dict)
                results.append(validated)

            total_results = (
                response.hits.total.value
                if hasattr(response.hits.total, "value")
                else response.hits.total
            )

            return results, total_results

        except Exception as e:
            logger.error(f"Error fetching paginated genes from Elasticsearch: {str(e)}")
            raise ServiceError(e)

    def _build_es_query(
        self,
        params: Optional[GeneAdvancedSearchQuerySchema],
        query: Optional[str],
        isolate_name: Optional[str],
        filter_criteria: Optional[dict],
    ) -> dict:
        """Build a properly structured Elasticsearch query for both full-text search and filters."""
        es_query = {"bool": {"must": []}}
        
        # Always filter for genes only in feature_index
        es_query["bool"]["must"].append({"term": {"feature_type": "gene"}})

        # locus_tag parameter with precedence over query
        if params and params.locus_tag:
            # Exact match
            es_query["bool"]["must"].append(
                {"term": {f"{ES_FIELD_LOCUS_TAG}.keyword": params.locus_tag}}
            )
        elif query:
            # Regular text search
            es_query["bool"]["must"].append(
                {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            ES_FIELD_GENE_NAME,
                            ES_FIELD_ALIAS,
                            ES_FIELD_LOCUS_TAG,
                            ES_FIELD_PRODUCT,
                            ES_FIELD_PFAM,
                            ES_FIELD_INTERPRO,
                        ],
                    }
                }
            )

        if isolate_name:
            es_query["bool"]["must"].append(
                {"term": {ES_FIELD_ISOLATE_NAME: isolate_name}}
            )

        if filter_criteria:
            if "bool" in filter_criteria and "must" in filter_criteria["bool"]:
                es_query["bool"]["must"].extend(filter_criteria["bool"]["must"])
            else:
                for field, value in filter_criteria.items():
                    if isinstance(value, list):
                        es_query["bool"]["must"].append({"terms": {field: value}})
                    else:
                        es_query["bool"]["must"].append({"term": {field: value}})

        logger.info(
            f"DEBUG - Final Elasticsearch Query: {json.dumps(es_query, indent=2)}"
        )
        return es_query

    async def get_faceted_search(
        self,
        params: GeneFacetedSearchQuerySchema,
    ):
        try:
            isolate_list = (
                [id.strip() for id in params.isolates.split(",") if id.strip()]
                if params.isolates
                else []
            )

            operators = {
                ES_FIELD_PFAM: params.pfam_operator,
                ES_FIELD_INTERPRO: params.interpro_operator,
                ES_FIELD_COG_ID: params.cog_id_operator,
                ES_FIELD_COG_FUNCATS: params.cog_funcats_operator,
                ES_FIELD_KEGG: params.kegg_operator,
                ES_FIELD_GO_TERM: params.go_term_operator,
            }

            result = await self._faceted_search_impl(
                query=params.query,
                species_acronym=params.species_acronym,
                isolates=isolate_list,
                essentiality=params.essentiality,
                cog_id=params.cog_id,
                cog_funcats=params.cog_funcats,
                kegg=params.kegg,
                go_term=params.go_term,
                pfam=params.pfam,
                interpro=params.interpro,
                has_amr_info=params.has_amr_info,
                limit=params.limit,
                operators=operators,
            )

            return result

        except Exception as e:
            logger.error(f"Error in faceted search: {e}")
            raise ServiceError(e)

    async def _faceted_search_impl(
        self,
        query: Optional[str] = None,
        species_acronym: Optional[str] = None,
        isolates: Optional[List[str]] = None,
        essentiality: Optional[str] = None,
        cog_id: Optional[str] = None,
        cog_funcats: Optional[str] = None,
        kegg: Optional[str] = None,
        go_term: Optional[str] = None,
        pfam: Optional[str] = None,
        interpro: Optional[str] = None,
        has_amr_info: Optional[bool] = None,
        limit: Optional[int] = DEFAULT_FACET_LIMIT,
        operators: Optional[Dict[str, str]] = None,
    ):
        """Internal implementation of faceted search."""
        try:
            gs = GeneFacetedSearch(
                query=query or "",
                species_acronym=species_acronym,
                essentiality=essentiality,
                isolates=isolates,
                cog_id=split_comma_param(cog_id),
                cog_funcats=split_comma_param(cog_funcats),
                kegg=split_comma_param(kegg),
                go_term=split_comma_param(go_term),
                pfam=split_comma_param(pfam),
                interpro=split_comma_param(interpro),
                has_amr_info=has_amr_info,
                limit=limit,
                operators=operators,
            )

            response = gs.execute()

            facet_results = {}
            for field in FACET_FIELDS:
                try:
                    filtered_agg_result = response.aggregations[f"{field}_filtered"][
                        field
                    ]
                    buckets = filtered_agg_result["buckets"]
                    aggregation_dict = {
                        bucket["key"]: bucket["doc_count"] for bucket in buckets
                    }

                    selected_map = {
                        GENE_ESSENTIALITY: essentiality,
                        ES_FIELD_PFAM: pfam,
                        ES_FIELD_INTERPRO: interpro,
                        ES_FIELD_KEGG: kegg,
                        ES_FIELD_COG_ID: cog_id,
                        ES_FIELD_COG_FUNCATS: cog_funcats,
                    }

                    facet_results[field] = self.process_aggregation_results(
                        aggregation_dict,
                        selected_values=(
                            [selected_map[field]] if selected_map.get(field) else []
                        ),
                        facet_group=field,
                    )
                except KeyError:
                    logger.warning(f"Facet {field} missing in aggregation response.")
                    facet_results[field] = []

            facet_results["total_hits"] = response.hits.total.value
            facet_results["operators"] = {
                ES_FIELD_PFAM: operators.get(ES_FIELD_PFAM, "OR"),
                ES_FIELD_INTERPRO: operators.get(ES_FIELD_INTERPRO, "OR"),
                ES_FIELD_COG_ID: operators.get(ES_FIELD_COG_ID, "OR"),
                ES_FIELD_COG_FUNCATS: operators.get(ES_FIELD_COG_FUNCATS, "OR"),
                ES_FIELD_KEGG: operators.get(ES_FIELD_KEGG, "OR"),
                ES_FIELD_GO_TERM: operators.get(ES_FIELD_GO_TERM, "OR"),
            }

            return facet_results

        except Exception as e:
            logger.exception("Error fetching faceted search")
            raise ServiceError(e)

    def process_aggregation_results(
        self,
        aggregation_dict: Dict[str, int],
        selected_values: Optional[List[str]] = None,
        facet_group: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        """Removes empty keys from aggregation results and marks selected items."""
        selected_values = selected_values or []

        results = []
        for key, count in aggregation_dict.items():
            if not str(key).strip():
                continue

            value = (
                True
                if facet_group == "has_amr_info" and str(key).lower() in ["1", "true"]
                else (
                    False
                    if facet_group == "has_amr_info"
                    and str(key).lower() in ["0", "false"]
                    else str(key)
                )
            )

            is_selected = str(value).lower() in [
                str(val).lower() for val in selected_values
            ]

            if count > 0 or is_selected:
                results.append(
                    {
                        "value": value,
                        "count": count,
                        "selected": is_selected,
                    }
                )

        return results

    async def get_gene_protein_seq(self, locus_tag: str) -> GeneProteinSeqSchema:
        """Fetch protein sequence information for a gene by its locus tag."""
        try:
            s = Search(index=self.index_name)
            s = s.filter("term", feature_type="gene")
            s = s.query("match", locus_tag=locus_tag)
            s = s.source([ES_FIELD_LOCUS_TAG, "protein_sequence"])

            response = await sync_to_async(s.execute)()

            logger.info(f"Response: {response}")

            if not response.hits:
                raise GeneNotFoundError(
                    f"Could not find gene with locus tag: {locus_tag}"
                )

            hit = response.hits[0]
            # logger.info(f"Hit.locus_tag: {hit.locus_tag}")
            # logger.info(f"Hit.protein_sequence: {hit.protein_sequence}")
            return GeneProteinSeqSchema(
                locus_tag=hit.locus_tag, protein_sequence=hit.protein_sequence
            )

        except GeneNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error fetching protein sequence for locus tag {locus_tag}: {e}"
            )
            raise ServiceError(f"Error fetching protein sequence: {str(e)}")

    def convert_to_tsv(self, genes: List[GeneResponseSchema]) -> str:
        """Convert gene data to TSV format for download."""
        if not genes:
            return ""

        columns = [
            "isolate_name",
            "gene_name",
            "alias",
            "seq_id",
            "locus_tag",
            "product",
            "uniprot_id",
            "essentiality",
            "pfam",
            "interpro",
            "kegg",
            "cog_funcats",
            "cog_id",
            "amr",
            "feature_type",
        ]

        # Create header row
        header = "\t".join(columns)

        # Create data rows
        rows = []
        for gene in genes:
            row_data = []
            for col in columns:
                value = getattr(gene, col, "")

                # Handle special cases
                if col == "alias" and value:
                    value = "; ".join(value) if isinstance(value, list) else str(value)
                elif col == "pfam" and value:
                    value = "; ".join(value) if isinstance(value, list) else str(value)
                elif col == "interpro" and value:
                    value = "; ".join(value) if isinstance(value, list) else str(value)
                elif col == "kegg" and value:
                    value = "; ".join(value) if isinstance(value, list) else str(value)
                elif col == "cog_id" and value:
                    value = "; ".join(value) if isinstance(value, list) else str(value)
                elif col == "amr" and value:
                    # Format AMR data
                    amr_parts = []
                    for amr_item in value:
                        if amr_item.get("drug_class"):
                            amr_parts.append(
                                f"{amr_item['drug_class']}({amr_item.get('drug_subclass', '')})"
                            )
                    value = "; ".join(amr_parts) if amr_parts else ""
                else:
                    value = str(value) if value is not None else ""

                # Escape tabs and newlines in the value
                value = value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
                row_data.append(value)

            rows.append("\t".join(row_data))

        return header + "\n" + "\n".join(rows)

    async def stream_genes_with_scroll(
        self,
        isolates: str = None,
        species_acronym: Optional[int] = None,
        query: str = None,
        filter: Optional[str] = None,
        filter_operators: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = SORT_ASC,
    ):
        """Stream genes directly from Elasticsearch scroll API without loading all into memory."""
        isolate_names_list = (
            [id.strip() for id in isolates.split(",")] if isolates else []
        )
        filter_criteria = {"bool": {"must": []}}

        # Filters for genome IDs and species ID
        if isolate_names_list:
            filter_criteria["bool"]["must"].append(
                {"terms": {ES_FIELD_ISOLATE_NAME: isolate_names_list}}
            )
        if species_acronym:
            filter_criteria["bool"]["must"].append(
                {"term": {ES_FIELD_SPECIES_ACRONYM: species_acronym}}
            )

        # Apply additional filters
        parsed_filters = self._parse_filters(filter)
        parsed_filter_operators = self._parse_filter_operators(filter_operators)
        type_strain_filters = await self._apply_filters_for_type_strain(
            {}, parsed_filters, parsed_filter_operators
        )

        if "bool" in type_strain_filters and "must" in type_strain_filters["bool"]:
            filter_criteria["bool"]["must"].extend(type_strain_filters["bool"]["must"])

        es_query = self._build_es_query(
            params=None,
            query=query,
            isolate_name=filter_criteria.get("isolate_name"),
            filter_criteria=filter_criteria,
        )

        # Sort configuration
        order_prefix = "desc" if sort_order == SORT_DESC else "asc"
        if sort_field == GENE_SORT_FIELD_STRAIN:
            sort_field = ES_FIELD_ISOLATE_NAME

        sort_by = sort_field or GENE_DEFAULT_SORT_FIELD
        sort_by = (
            f"{sort_by}.keyword"
            if sort_by
            in [
                ES_FIELD_GENE_NAME,
                ES_FIELD_ALIAS,
                FIELD_SEQ_ID,
                ES_FIELD_LOCUS_TAG,
                ES_FIELD_PRODUCT,
            ]
            else sort_by
        )

        try:
            es_client = connections.get_connection()
            search_body = {
                "query": es_query,
                "sort": [{sort_by: {"order": order_prefix}}],
                "size": SCROLL_BATCH_SIZE,
            }

            logger.info(
                f"Starting streaming scroll search with query: {json.dumps(search_body, indent=2)}"
            )

            # Execute initial search
            response = await sync_to_async(
                lambda: es_client.search(
                    index=self.index_name, body=search_body, scroll=SCROLL_TIMEOUT
                )
            )()

            total_results = 0
            max_results = SCROLL_MAX_RESULTS
            batch_count = 0
            scroll_id = response["_scroll_id"]

            # Process all batches
            while len(response["hits"]["hits"]) > 0 and total_results < max_results:
                batch_count += 1
                for hit_data in response["hits"]["hits"]:
                    # Create a mock hit object that has to_dict() method
                    class MockHit:
                        def __init__(self, source):
                            self._source = source

                        def to_dict(self):
                            return self._source

                    mock_hit = MockHit(hit_data["_source"])
                    gene_obj = gene_from_hit(mock_hit)
                    gene_dict = model_to_dict(gene_obj)
                    validated = GeneResponseSchema.model_validate(gene_dict)

                    total_results += 1
                    yield validated

                logger.info(
                    f"Streamed {total_results} genes in {batch_count} batches..."
                )

                # Get next batch using scroll
                try:
                    response = await sync_to_async(
                        lambda: es_client.scroll(
                            scroll_id=scroll_id, scroll=SCROLL_TIMEOUT
                        )
                    )()
                    scroll_id = response["_scroll_id"]
                except Exception as scroll_error:
                    logger.error(f"Error in scroll batch {batch_count}: {scroll_error}")
                    break

            if total_results >= max_results:
                logger.warning(
                    f"Reached maximum result limit of {max_results}. Some results may be truncated."
                )

            logger.info(f"Streaming completed. Total genes streamed: {total_results}")

        except Exception as e:
            logger.error(f"Error streaming genes with scroll API: {str(e)}")
            raise ServiceError(e)
