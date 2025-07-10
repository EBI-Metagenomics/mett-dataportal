import json
import logging
from typing import List
from typing import Optional

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.forms.models import model_to_dict
from elasticsearch_dsl import Search, connections

from dataportal.models import StrainDocument
from dataportal.schema.genome_schemas import (
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
    ES_FIELD_SPECIES_ACRONYM,
    ES_INDEX_STRAIN,
    SCROLL_BATCH_SIZE,
    SCROLL_MAX_RESULTS,
    SCROLL_TIMEOUT,
)
from dataportal.utils.exceptions import ServiceError

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
        use_scroll: bool = False,
    ) -> GenomePaginationSchema:
        """Search genomes in Elasticsearch with optional isolate/species filters."""
        filter_criteria = {}

        if query:
            filter_criteria[STRAIN_FIELD_ISOLATE_NAME] = query
        if isolates:
            filter_criteria["isolate_name.keyword"] = isolates
        if species_acronym:
            filter_criteria[ES_FIELD_SPECIES_ACRONYM] = species_acronym

        if use_scroll:
            # Use scroll API for large downloads
            strains, total_results = await self._fetch_all_strains_with_scroll(
                filter_criteria=filter_criteria,
                sortField=sortField,
                sortOrder=sortOrder,
                schema=GenomeResponseSchema,
            )
            return await self._create_pagination_schema(strains, total_results, 1, total_results)
        else:
            # Use regular pagination for normal requests
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
        query: Optional[str],
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sortField: str = STRAIN_FIELD_ISOLATE_NAME,
        sortOrder: str = SORT_ASC,
    ) -> GenomePaginationSchema:
        # If query is None or empty, just filter by species (equivalent to get_genomes_by_species)
        if not query or query.strip() == "":
            return await self.get_genomes_by_species(
                species_acronym=species_acronym,
                page=page,
                per_page=per_page,
                sortField=sortField,
                sortOrder=sortOrder,
            )

        # If query is provided, search by species and query string
        filter_criteria = {
            ES_FIELD_SPECIES_ACRONYM: species_acronym,
            STRAIN_FIELD_ISOLATE_NAME: query,
        }
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
                    {
                        "wildcard": {
                            f"{STRAIN_FIELD_ISOLATE_NAME}.keyword": f"*{query}*"
                        }
                    },
                    {
                        "wildcard": {
                            f"{STRAIN_FIELD_ASSEMBLY_NAME}.keyword": f"*{query}*"
                        }
                    },
                ],
                minimum_should_match=1,
            )

            if species_acronym:
                search = search.filter(
                    "term", **{ES_FIELD_SPECIES_ACRONYM: species_acronym}
                )

            search = search[: (limit or self.limit)]

            search = search.source(
                ["id", STRAIN_FIELD_ISOLATE_NAME, STRAIN_FIELD_ASSEMBLY_NAME]
            )

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
                filter_criteria,
                page,
                per_page,
                sortField,
                sortOrder,
                schema=GenomeResponseSchema,
            )
            return await self._create_pagination_schema(
                strains, total_results, page, per_page
            )
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
                                {
                                    "wildcard": {
                                        f"{field}.keyword": f"*{value.lower()}*"
                                    }
                                },
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
            search = search[(page - 1) * per_page : page * per_page]

            # logger.info(f"Final Elasticsearch Query: {json.dumps(search.to_dict(), indent=2)}")

            response = await sync_to_async(search.execute)()
            total_results = (
                response.hits.total.value
                if hasattr(response.hits.total, "value")
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
        # Map invalid sort fields to valid ones
        field_mapping = {
            'species': ES_FIELD_SPECIES_ACRONYM,
            'isolate_name': f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",
            'genome': f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",  # Map 'genome' to 'isolate_name.keyword'
            'strain': f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",  # Map 'strain' to 'isolate_name.keyword'
            'name': f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",    # Map 'name' to 'isolate_name.keyword'
        }
        
        # Return mapped field if it exists, otherwise return the original field
        return field_mapping.get(field, field)

    def convert_to_tsv(self, genomes: List[GenomeResponseSchema]) -> str:
        """Convert genome data to TSV format for download."""
        if not genomes:
            return ""
        
        # Define the columns to include in the TSV export
        columns = [
            'isolate_name', 'species_scientific_name', 'species_acronym', 
            'assembly_name', 'assembly_accession', 'type_strain'
        ]
        
        # Create header row
        header = '\t'.join(columns)
        
        # Create data rows
        rows = []
        for genome in genomes:
            row_data = []
            for col in columns:
                value = getattr(genome, col, '')
                value = str(value) if value is not None else ''
                
                # Escape tabs and newlines in the value
                value = value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                row_data.append(value)
            
            rows.append('\t'.join(row_data))
        
        return header + '\n' + '\n'.join(rows)

    async def _fetch_all_strains_with_scroll(
        self, filter_criteria, sortField, sortOrder, schema
    ):
        """Fetch all strains using Elasticsearch scroll API for large downloads."""
        try:
            es_client = connections.get_connection()
            search_body = {
                "query": {
                    "bool": {
                        "must": []
                    }
                },
                "size": SCROLL_BATCH_SIZE
            }

            # Dynamically apply filters
            for field, value in filter_criteria.items():
                if isinstance(value, str):
                    if field == STRAIN_FIELD_ISOLATE_NAME:
                        search_body["query"]["bool"]["must"].append({
                            "bool": {
                                "should": [
                                    {
                                        "wildcard": {
                                            f"{field}.keyword": f"*{value.lower()}*"
                                        }
                                    },
                                    {"term": {f"{field}.keyword": value}},
                                ],
                                "minimum_should_match": 1,
                            }
                        })
                    else:
                        search_body["query"]["bool"]["must"].append({
                            "wildcard": {field: f"*{value}*"}
                        })
                elif isinstance(value, list):
                    search_body["query"]["bool"]["must"].append({
                        "terms": {field: value}
                    })
                else:
                    search_body["query"]["bool"]["must"].append({
                        "term": {field: value}
                    })

            # Map "species" to its actual field
            sortField = self._resolve_sort_field(sortField)
            sort_order = "asc" if sortOrder == SORT_ASC else "desc"
            search_body["sort"] = [{sortField: {"order": sort_order}}]

            logger.info(f"Starting scroll search with query: {json.dumps(search_body, indent=2)}")

            # Execute initial search
            response = await sync_to_async(
                lambda: es_client.search(
                    index=ES_INDEX_STRAIN,
                    body=search_body,
                    scroll=SCROLL_TIMEOUT
                )
            )()

            results = []
            total_results = 0
            max_results = SCROLL_MAX_RESULTS
            batch_count = 0
            scroll_id = response['_scroll_id']

            # Process all batches
            while len(response['hits']['hits']) > 0 and total_results < max_results:
                batch_count += 1
                for hit_data in response['hits']['hits']:
                    # Create a mock hit object that has to_dict() method
                    class MockHit:
                        def __init__(self, source):
                            self._source = source
                        
                        def to_dict(self):
                            return self._source
                    
                    mock_hit = MockHit(hit_data['_source'])
                    strain_obj = strain_from_hit(mock_hit)
                    strain_dict = model_to_dict(strain_obj)
                    results.append(schema.model_validate(strain_dict))
                
                total_results += len(response['hits']['hits'])
                logger.info(f"Fetched {total_results} strains in {batch_count} batches...")

                # Get next batch using scroll
                try:
                    response = await sync_to_async(
                        lambda: es_client.scroll(
                            scroll_id=scroll_id,
                            scroll=SCROLL_TIMEOUT
                        )
                    )()
                    scroll_id = response['_scroll_id']
                except Exception as scroll_error:
                    logger.error(f"Error in scroll batch {batch_count}: {scroll_error}")
                    break

            if total_results >= max_results:
                logger.warning(f"Reached maximum result limit of {max_results}. Some results may be truncated.")

            logger.info(f"Scroll search completed. Total strains fetched: {total_results}")
            return results, total_results

        except Exception as e:
            logger.error(f"Error fetching strains with scroll API: {e}", exc_info=True)
            raise ServiceError(f"Error fetching strains with scroll API: {str(e)}")
