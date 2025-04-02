import json
import logging
from typing import List
from typing import Optional

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.forms.models import model_to_dict
from elasticsearch_dsl import Search

from dataportal.models import StrainDocument
from dataportal.schemas import (
    GenomePaginationSchema,
    GenomeResponseSchema,
)
from dataportal.unmanaged_models.strain_data import strain_from_hit
from dataportal.utils.constants import (
    STRAIN_FIELD_ISOLATE_NAME,
    STRAIN_FIELD_ASSEMBLY_NAME,
    STRAIN_FIELD_SPECIES,
    SORT_ASC,
    DEFAULT_PER_PAGE_CNT,
    ES_FIELD_SPECIES_SCIENTIFIC_NAME,
    ES_FIELD_SPECIES_ACRONYM, ES_INDEX_STRAIN,
)
from dataportal.utils.exceptions import ServiceError, GenomeNotFoundError

logger = logging.getLogger(__name__)


class GenomeService:

    def __init__(self, limit: int = 10):
        self.limit = limit

    async def get_type_strains(self) -> List[GenomeResponseSchema]:
        return await self._fetch_and_validate_strains(
            filter_criteria={"type_strain": True},
            schema=GenomeResponseSchema,
            error_message="Error fetching type strains",
        )

    async def search_genomes_by_string(
            self,
            query: str,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sortField: str = STRAIN_FIELD_ISOLATE_NAME,
            sortOrder: str = SORT_ASC,
            isolates: Optional[List[str]] = None,
            species_acronym: Optional[str] = None,
    ) -> GenomePaginationSchema:
        """Search genomes in Elasticsearch with optional isolate/species filters."""
        filter_criteria = {}

        if query:
            filter_criteria[STRAIN_FIELD_ISOLATE_NAME] = query
        if isolates:
            filter_criteria["isolate_name.keyword"] = isolates
        if species_acronym:
            filter_criteria[ES_FIELD_SPECIES_ACRONYM] = species_acronym

        return await self._search_paginated_strains(
            filter_criteria=filter_criteria,
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error searching genomes by string",
        )

    async def get_genomes_by_species(
            self,
            species_acronym: str,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sortField: str = STRAIN_FIELD_ISOLATE_NAME,
            sortOrder: str = SORT_ASC,
    ) -> GenomePaginationSchema:
        return await self._search_paginated_strains(
            filter_criteria={ES_FIELD_SPECIES_ACRONYM: species_acronym},
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error fetching genomes by species",
        )

    async def search_genomes_by_species_and_string(
            self,
            species_acronym: str,
            query: str,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sortField: str = STRAIN_FIELD_ISOLATE_NAME,
            sortOrder: str = SORT_ASC,
    ) -> GenomePaginationSchema:
        filter_criteria = {ES_FIELD_SPECIES_ACRONYM: species_acronym, STRAIN_FIELD_ISOLATE_NAME: query}
        return await self._search_paginated_strains(
            filter_criteria=filter_criteria,
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error searching genomes by species and string",
        )

    async def search_strains(
            self, query: str, limit: int = None, species_acronym: Optional[str] = None
    ):
        try:
            search = Search(index=ES_INDEX_STRAIN)

            search = search.query(
                "bool",
                should=[
                    {"wildcard": {f"{STRAIN_FIELD_ISOLATE_NAME}.keyword": f"*{query}*"}},
                    {"wildcard": {f"{STRAIN_FIELD_ASSEMBLY_NAME}.keyword": f"*{query}*"}}
                ],
                minimum_should_match=1
            )

            if species_acronym:
                search = search.filter("term", **{ES_FIELD_SPECIES_ACRONYM: species_acronym})

            search = search[: (limit or self.limit)]

            search = search.source(["id", STRAIN_FIELD_ISOLATE_NAME, STRAIN_FIELD_ASSEMBLY_NAME])

            # logger.info(f"Final Elasticsearch Query: {json.dumps(search.to_dict(), indent=2)}")
            response = await sync_to_async(search.execute)()

            return [
                {
                    STRAIN_FIELD_ISOLATE_NAME: hit.isolate_name,
                    STRAIN_FIELD_ASSEMBLY_NAME: hit.assembly_name,
                }
                for hit in response
            ]

        except Exception as e:
            logger.error(f"Error executing strain search query: {e}")
            return []

    async def get_genomes(
            self,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sortField: str = STRAIN_FIELD_ISOLATE_NAME,
            sortOrder: str = SORT_ASC,
    ) -> GenomePaginationSchema:
        return await self._search_paginated_strains(
            filter_criteria={},
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error fetching genomes",
        )

    async def get_genome_by_strain_name(self, isolate_name: str):
        return await self._fetch_single_genome(
            filter_criteria={STRAIN_FIELD_ISOLATE_NAME: isolate_name},
            error_message=f"Error fetching genome by strain name {isolate_name}",
        )

    async def get_genomes_by_isolate_names(
            self, isolate_names: List[str]
    ) -> List[GenomeResponseSchema]:
        if not isolate_names:
            return []
        # logger.info(f"Getting genomes for isolate names: {isolate_names}")
        filter_criteria = {"isolate_name.keyword": isolate_names}
        try:
            strains = await self._fetch_and_validate_strains(
                filter_criteria=filter_criteria,
                schema=GenomeResponseSchema,
                error_message="Error fetching genomes by isolate names",
            )
            return strains
        except Exception as e:
            logger.error(f"Error in get_genomes_by_isolate_names: {e}", exc_info=True)
            raise ServiceError(f"Could not fetch genomes by isolate names: {e}")

    async def _fetch_and_validate_strains(self, filter_criteria, schema, error_message):
        """Fetch and validate strains from Elasticsearch and compute additional fields."""
        try:
            search = Search(index=ES_INDEX_STRAIN)

            for field, value in filter_criteria.items():
                if isinstance(value, list):
                    search = search.filter("terms", **{field: value})
                else:
                    search = search.filter("term", **{field: value})

            response = await sync_to_async(search.execute)()

            results = []
            for hit in response:
                strain_obj = strain_from_hit(hit)
                strain_dict = model_to_dict(strain_obj)
                results.append(schema.model_validate(strain_dict))

            return results

        except Exception as e:
            logger.error(f"{error_message}: {e}")
            raise ServiceError(f"{error_message}: {str(e)}")

    async def _search_paginated_strains(
            self, filter_criteria, page, per_page, sortField, sortOrder, error_message
    ):
        """Search and paginate strains in Elasticsearch."""
        try:
            strains, total_results = await self._fetch_paginated_strains(
                filter_criteria, page, per_page, sortField, sortOrder, schema=GenomeResponseSchema
            )
            return await self._create_pagination_schema(strains, total_results, page, per_page)
        except Exception as e:
            logger.error(f"{error_message}: {e}")
            raise ServiceError(e)

    async def _fetch_single_genome(self, filter_criteria, error_message):
        try:
            if isinstance(filter_criteria, Q):
                filter_kwargs = {
                    child[0]: child[1] for child in filter_criteria.children
                }
            else:
                filter_kwargs = filter_criteria

            # Fetch ORM strain with related species
            strain = await sync_to_async(
                lambda: StrainDocument.objects.select_related(STRAIN_FIELD_SPECIES).get(
                    **filter_kwargs
                )
            )()
            strain_obj = strain_from_hit(strain)
            strain_dict = model_to_dict(strain_obj)
            # Validate using Pydantic schema
            return GenomeResponseSchema.model_validate(strain_dict)

        except StrainDocument.DoesNotExist:
            logger.error(error_message)
            raise GenomeNotFoundError(error_message)
        except Exception as e:
            logger.error(f"{error_message}: {e}", exc_info=True)
            raise ServiceError(e)

    async def _fetch_paginated_strains(
            self, filter_criteria, page, per_page, sortField, sortOrder, schema
    ):
        """Fetch paginated strains from Elasticsearch with optimized searching."""
        try:
            search = Search(index=ES_INDEX_STRAIN)

            # Dynamically apply filters
            for field, value in filter_criteria.items():
                if isinstance(value, str):
                    if field == STRAIN_FIELD_ISOLATE_NAME:
                        search = search.query(
                            "bool",
                            should=[
                                {"wildcard": {f"{field}.keyword": f"*{value.lower()}*"}},
                                {"term": {f"{field}.keyword": value}},
                            ],
                            minimum_should_match=1,
                        )
                    else:
                        search = search.query("wildcard", **{field: f"*{value}*"})
                elif isinstance(value, list):
                    search = search.filter("terms", **{field: value})
                else:
                    search = search.filter("term", **{field: value})

            # Map "species" to its actual field
            sortField = self._resolve_sort_field(sortField)
            sort_order = "asc" if sortOrder == SORT_ASC else "desc"
            search = search.sort({sortField: {"order": sort_order}})

            # Apply pagination
            search = search[(page - 1) * per_page: page * per_page]

            # logger.info(f"Final Elasticsearch Query: {json.dumps(search.to_dict(), indent=2)}")

            response = await sync_to_async(search.execute)()
            total_results = (
                response.hits.total.value
                if hasattr(response.hits.total, 'value')
                else len(response)
            )

            results = []
            for hit in response:
                strain_obj = strain_from_hit(hit)
                strain_dict = model_to_dict(strain_obj)
                results.append(schema.model_validate(strain_dict))

            return results, total_results

        except Exception as e:
            logger.error(f"Error fetching paginated strains: {e}", exc_info=True)
            raise ServiceError(f"Error fetching paginated strains: {str(e)}")

    async def _create_pagination_schema(self, strains, total_results, page, per_page):
        """Create pagination schema for search results."""
        return GenomePaginationSchema(
            results=strains,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=(page * per_page) < total_results,
            total_results=total_results,
        )

    def _resolve_sort_field(self, field: str) -> str:
        if field == STRAIN_FIELD_SPECIES:
            return ES_FIELD_SPECIES_ACRONYM
        if field in [STRAIN_FIELD_ISOLATE_NAME, ES_FIELD_SPECIES_SCIENTIFIC_NAME]:
            return f"{field}.keyword"
        return field
