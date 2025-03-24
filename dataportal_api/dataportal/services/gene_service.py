import json
import logging
from typing import Optional, List, Tuple, Dict

from asgiref.sync import sync_to_async
from django.db.models import Q
from elasticsearch_dsl import Search, A

from dataportal.models import GeneDocument
from dataportal.schemas import GenePaginationSchema, GeneResponseSchema
from dataportal.services.gene_faceted_search import GeneFacetedSearch
from dataportal.utils.constants import (
    GENE_DEFAULT_SORT_FIELD,
    DEFAULT_SORT,
    DEFAULT_PER_PAGE_CNT,
    SORT_DESC,
    SORT_ASC,
    GENE_ESSENTIALITY,
    GENE_ESSENTIALITY_MEDIA,
)
from dataportal.utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
    InvalidGenomeIdError, )

logger = logging.getLogger(__name__)


class GeneService:
    INDEX_NAME = "gene_index"

    async def autocomplete_gene_suggestions(
            self,
            query: str,
            filter: Optional[str] = None,
            limit: int = None,
            species_acronym: Optional[str] = None,
            isolates: Optional[List[str]] = None,
    ) -> List[Dict]:
        """ Provides autocomplete suggestions for genes based on query & filters. """

        try:

            s = Search(index=self.INDEX_NAME)
            s = s.query(
                "multi_match",
                query=query,
                fields=[
                    "alias^3", "alias.keyword^5", "gene_name^2", "product", "kegg",
                    "uniprot_id", "pfam", "cog_id", "interpro"
                ],
                type="best_fields"
            )

            if species_acronym:
                s = s.filter("term", species_acronym=species_acronym)

            if isolates:
                s = s.filter("terms", isolate_name=isolates)

            parsed_filters = self._parse_filters(filter)
            for key, values in parsed_filters.items():
                if key == "essentiality":
                    normalized_values = [v.lower() for v in values]
                    s = s.filter("terms", essentiality=normalized_values)
                else:
                    s = s.filter("terms", **{key: values})

            s = s[:limit]

            logger.info(f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}")

            response = s.execute()

            results = [
                {
                    "gene_name": getattr(hit, "gene_name", None),
                    "alias": getattr(hit, "alias", []),
                    "product": getattr(hit, "product", None),
                    "locus_tag": getattr(hit, "locus_tag", None),
                    "species_scientific_name": getattr(hit, "species_scientific_name", None),
                    "species_acronym": getattr(hit, "species_acronym", None),
                    "isolate_name": getattr(hit, "isolate_name", None),
                    "kegg": getattr(hit, "kegg", []),
                    "uniprot_id": getattr(hit, "uniprot_id", None),
                    "pfam": getattr(hit, "pfam", []),
                    "cog_id": getattr(hit, "cog_id", None),
                    "interpro": getattr(hit, "interpro", []),
                    "essentiality": getattr(hit, "essentiality", "Unknown")
                }
                for hit in response
            ]

            logger.info(f"Autocomplete results: {results}")
            return results

        except Exception as e:
            logger.error(f"Error fetching gene autocomplete suggestions: {e}")
            return []

    async def get_gene_by_locus_tag(self, locus_tag: str) -> GeneResponseSchema:
        """Fetch a gene document from Elasticsearch using locus_tag."""
        try:
            gene = await sync_to_async(self.fetch_gene_by_locus_tag, thread_sensitive=False)(locus_tag)
            return self._serialize_gene(gene)
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

        return response.hits[0].to_dict()

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
            # serialized_genes = [self._serialize_gene(gene) for gene in genes]
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

            logger.info(f"Final Elasticsearch Query (Formatted): {json.dumps(es_query, indent=2)}")

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
                filter_criteria["bool"]["must"].append({"terms": {"isolate_name": isolate_names_list}})
            if species_acronym:
                filter_criteria["bool"]["must"].append({"term": {"species_acronym": species_acronym}})

            # apply additional filters
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

    def _serialize_gene_essentiality(self, gene_essentiality):
        return {
            GENE_ESSENTIALITY_MEDIA: gene_essentiality.media,
            GENE_ESSENTIALITY: (
                gene_essentiality.essentiality.name
                if gene_essentiality.essentiality
                else None
            ),
        }

    def _serialize_gene(self, gene_data: GeneDocument) -> GeneResponseSchema:
        return GeneResponseSchema(
            locus_tag=gene_data.get("locus_tag"),
            gene_name=gene_data.get("gene_name"),
            alias=gene_data.get("alias") or None,
            seq_id=gene_data.get("seq_id"),
            isolate_name=gene_data.get("isolate_name"),
            uniprot_id=gene_data.get("uniprot_id"),
            cog_funcats=gene_data.get("cog_funcats"),
            cog_id=gene_data.get("cog_id"),
            kegg=gene_data.get("kegg"),
            pfam=gene_data.get("pfam"),
            interpro=gene_data.get("interpro"),
            dbxref=gene_data.get("dbxref"),
            ec_number=gene_data.get("ec_number"),
            product=gene_data.get("product"),
            start_position=gene_data.get("start"),
            end_position=gene_data.get("end"),
            essentiality=gene_data.get("essentiality", "Unknown")
        )

    def _parse_filters(self, filter_str: Optional[str]) -> Dict[str, List[str]]:
        if not filter_str:
            return {}

        filters = {}
        try:
            # Match key:values where values can contain commas
            key, values_str = filter_str.split(":", 1)
            key = key.strip()
            values = [v.strip() for v in values_str.split(",")]
            filters[key] = values
        except ValueError:
            logger.error(f"Invalid filter format: {filter_str}")
            raise ServiceError(
                "Invalid filter format. Use 'key:value' pairs separated by commas."
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
        """Apply additional filters for type strain in Elasticsearch query."""

        if "bool" not in query:
            query["bool"] = {"must": []}

        must_filters = []

        # ✅ Add type strain filter
        # must_filters.append({"term": {"strain.type_strain": True}})

        # ✅ Apply additional filters
        for key, values in filters.items():
            if key == GENE_ESSENTIALITY:
                must_filters.append({"terms": {GENE_ESSENTIALITY: values}})
            else:
                must_filters.append({"terms": {key: values}})

        query["bool"]["must"].extend(must_filters)

        logger.info(f"DEBUG - Filters after _apply_filters_for_type_strain: {json.dumps(query, indent=2)}")

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
        """Fetch paginated genes from Elasticsearch using a unified query format."""

        start = (page - 1) * per_page
        order_prefix = "desc" if sort_order == SORT_DESC else "asc"

        # Ensure "species" is mapped to "species_scientific_name"
        if sort_field == "strain":
            sort_field = "isolate_name"

        sort_by = sort_field or GENE_DEFAULT_SORT_FIELD
        sort_by = f"{sort_by}.keyword" if sort_by in ["gene_name", "alias", "seq_id", "locus_tag",
                                                      "product"] else sort_by

        try:
            logger.debug(f"Sorting by: {sort_by} ({order_prefix})")
            logger.debug(f"Pagination: start={start}, size={per_page}")

            # Execute Elasticsearch query
            s = (
                Search(index=self.INDEX_NAME)
                .query(query)
                .sort({sort_by: {"order": order_prefix}})
                [start: start + per_page]
                .extra(track_total_hits=True)
            )

            logger.info(f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}")

            response = await sync_to_async(s.execute)()

            genes = [self._serialize_gene(hit.to_dict()) for hit in response.hits]
            total_results = response.hits.total.value if hasattr(response.hits.total, 'value') else response.hits.total

            logger.info(f"Fetched {len(genes)} genes")
            logger.info(f"Total matching genes: {total_results}")

            return genes, total_results

        except Exception as e:
            logger.error(f"Error fetching paginated genes from Elasticsearch: {str(e)}")
            raise ServiceError(e)

    def _build_es_query(self, query: Optional[str], isolate_name: Optional[str],
                        filter_criteria: Optional[dict]) -> dict:
        """Build a properly structured Elasticsearch query for both full-text search and filters."""
        es_query = {"bool": {"must": []}}

        if query:
            es_query["bool"]["must"].append(
                {"multi_match": {"query": query, "fields": ["gene_name", "alias", "product", "pfam", "interpro"]}}
            )

        if isolate_name:
            es_query["bool"]["must"].append({"term": {"isolate_name": isolate_name}})

        if filter_criteria:
            if "bool" in filter_criteria and "must" in filter_criteria["bool"]:
                es_query["bool"]["must"].extend(filter_criteria["bool"]["must"])
            else:
                for field, value in filter_criteria.items():
                    if isinstance(value, list):
                        es_query["bool"]["must"].append({"terms": {field: value}})
                    else:
                        es_query["bool"]["must"].append({"term": {field: value}})

        logger.info(f"DEBUG - Final Elasticsearch Query (Fixed): {json.dumps(es_query, indent=2)}")
        return es_query

    async def get_faceted_search(self, species_acronym: Optional[str] = None,
                                 essentiality: Optional[str] = None,
                                 isolates: Optional[List[str]] = None,
                                 cog_funcat: Optional[str] = None,
                                 kegg: Optional[str] = None,
                                 go_term: Optional[str] = None,
                                 pfam: Optional[str] = None,
                                 interpro: Optional[str] = None,
                                 limit: int = 20):
        try:
            gs = GeneFacetedSearch(
                query='',
                species_acronym=species_acronym,
                essentiality=essentiality,
                isolates=isolates,
                cog_funcat=cog_funcat,
                kegg=kegg,
                go_term=go_term,
                pfam=pfam,
                interpro=interpro,
                limit=limit
            )

            response = gs.execute()

            return {
                "pfam": self.process_aggregation_results(
                    {b[0]: b[1] for b in getattr(response.facets, 'pfam', [])},
                    selected_values=[pfam] if pfam else []
                ),
                "interpro": self.process_aggregation_results(
                    {b[0]: b[1] for b in getattr(response.facets, 'interpro', [])},
                    selected_values=[interpro] if interpro else []
                ),
                "essentiality": self.process_aggregation_results(
                    {b[0]: b[1] for b in getattr(response.facets, 'essentiality', [])},
                    selected_values=[essentiality] if essentiality else []
                ),
                "total_hits": response.hits.total.value
            }

        except Exception as e:
            logger.exception("Error fetching faceted search")
            raise ServiceError(e)

    def process_aggregation_results(self, aggregation_dict, selected_values=None):
        """Removes empty keys from aggregation results."""
        return [
            {
                "value": key,
                "count": count,
                "selected": key in selected_values
            }
            for key, count in aggregation_dict.items() if key.strip()
        ]
