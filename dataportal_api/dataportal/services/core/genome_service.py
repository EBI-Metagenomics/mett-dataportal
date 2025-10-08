import json
import logging
from typing import List, Optional, Dict, Any

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.forms.models import model_to_dict
from elasticsearch_dsl import Search, connections

from dataportal.models import StrainDocument
from dataportal.schema.core.genome_schemas import (
    GenomePaginationSchema,
    GenomeResponseSchema,
    GenomeSearchQuerySchema,
    GetAllGenomesQuerySchema,
    GenomesByIsolateNamesQuerySchema,
    GenomeAutocompleteQuerySchema,
    StrainSuggestionSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.decorators import log_execution_time
from django.conf import settings
from dataportal.utils.constants import (
    STRAIN_FIELD_ISOLATE_NAME,
    STRAIN_FIELD_SPECIES,
    SORT_ASC,
    ES_FIELD_SPECIES_ACRONYM,
    ES_INDEX_STRAIN,
    SCROLL_BATCH_SIZE,
    SCROLL_MAX_RESULTS,
    SCROLL_TIMEOUT,
)
from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)


class GenomeService(BaseService[GenomeResponseSchema, Dict[str, Any]]):
    """Service for managing genome data operations in the read-only data portal."""

    def __init__(self, limit: int = 10):
        super().__init__(ES_INDEX_STRAIN)
        self.limit = limit
    
    def _convert_hit_to_genome_schema(self, hit) -> GenomeResponseSchema:
        """Convert Elasticsearch hit directly to GenomeResponseSchema (Pydantic)."""
        hit_dict = hit.to_dict()
        
        # Extract contigs with proper structure
        contigs_raw = hit_dict.get("contigs", [])
        contigs = []
        if contigs_raw:
            from dataportal.schema.core.genome_schemas import ContigSchema
            for contig in contigs_raw:
                if isinstance(contig, dict):
                    contigs.append(ContigSchema(
                        seq_id=contig.get("seq_id"),
                        length=contig.get("length")
                    ))
        
        return GenomeResponseSchema(
            species_scientific_name=hit_dict.get("species_scientific_name"),
            species_acronym=hit_dict.get("species_acronym"),
            isolate_name=hit_dict.get("isolate_name"),
            assembly_name=hit_dict.get("assembly_name"),
            assembly_accession=hit_dict.get("assembly_accession"),
            fasta_file=hit_dict.get("fasta_file"),
            gff_file=hit_dict.get("gff_file"),
            fasta_url=(
                f"{settings.ASSEMBLY_FTP_PATH}/{hit_dict.get('fasta_file')}"
                if hit_dict.get("fasta_file")
                else None
            ),
            gff_url=(
                f"{settings.GFF_FTP_PATH.format(hit_dict.get('isolate_name'))}/{hit_dict.get('gff_file')}"
                if hit_dict.get("gff_file") and hit_dict.get("isolate_name")
                else None
            ),
            type_strain=hit_dict.get("type_strain", False),
            contigs=contigs,
        )

    @log_execution_time
    async def get_by_id(self, id: str) -> Optional[GenomeResponseSchema]:
        """Retrieve a single genome by ID."""
        try:
            search = self._create_search().query("term", _id=id)
            response = await self._execute_search(search)

            if not response:
                return None

            return self._convert_hit_to_entity(response[0])
        except Exception as e:
            self._handle_elasticsearch_error(e, f"get_by_id for genome {id}")

    @log_execution_time
    async def get_all(self, **kwargs) -> List[GenomeResponseSchema]:
        """Retrieve all genomes with optional filtering."""
        try:
            search = self._create_search().query("match_all")

            # Apply filters if provided
            if kwargs.get("species"):
                search = search.filter("term", species_acronym=kwargs["species"])

            if kwargs.get("isolate_name"):
                search = search.filter("term", isolate_name=kwargs["isolate_name"])

            response = await self._execute_search(search)
            return [self._convert_hit_to_entity(hit) for hit in response]
        except Exception as e:
            self._handle_elasticsearch_error(e, "get_all genomes")

    @log_execution_time
    async def search(self, query: Dict[str, Any]) -> List[GenomeResponseSchema]:
        """Search genomes based on query parameters."""
        try:
            search = self._create_search()

            # Build search query based on provided parameters
            if query.get("q"):  # General search
                search = search.query(
                    "multi_match",
                    query=query["q"],
                    fields=["isolate_name", "species_acronym", "description"],
                )
            elif query.get("species"):
                search = search.query("term", species_acronym=query["species"])
            elif query.get("isolate_name"):
                search = search.query("term", isolate_name=query["isolate_name"])
            else:
                search = search.query("match_all")

            # Apply sorting
            if query.get("sort_by"):
                sort_field = query["sort_by"]
                sort_order = query.get("sort_order", "asc")
                search = search.sort({sort_field: sort_order})

            # Apply pagination
            page = query.get("page", 1)
            page_size = query.get("page_size", 10)
            start = (page - 1) * page_size
            search = search[start : start + page_size]

            response = await self._execute_search(search)
            return [self._convert_hit_to_entity(hit) for hit in response]
        except Exception as e:
            self._handle_elasticsearch_error(e, "search genomes")

    def _convert_hit_to_entity(self, hit) -> GenomeResponseSchema:
        """Convert Elasticsearch hit to GenomeResponseSchema."""
        hit_dict = hit.to_dict()
        return GenomeResponseSchema.model_validate(hit_dict)

    # Original methods with minimal changes - keeping existing query logic
    async def get_type_strains(self) -> List[GenomeResponseSchema]:
        return await self._fetch_and_validate_strains(
            filter_criteria={"type_strain": True},
            schema=GenomeResponseSchema,
            error_message="Error fetching type strains",
        )

    async def search_genomes_by_string(
        self,
        params: GenomeSearchQuerySchema,
        use_scroll: bool = False,
    ) -> GenomePaginationSchema:
        filter_criteria = {}

        if params.query:
            filter_criteria[STRAIN_FIELD_ISOLATE_NAME] = params.query
        if params.isolates:
            filter_criteria["isolate_name.keyword"] = params.isolates
        if params.species_acronym:
            filter_criteria[ES_FIELD_SPECIES_ACRONYM] = params.species_acronym

        if use_scroll:
            # Use scroll API for large downloads
            strains, total_results = await self._fetch_all_strains_with_scroll(
                filter_criteria=filter_criteria,
                sortField=params.sortField,
                sortOrder=params.sortOrder,
                schema=GenomeResponseSchema,
            )
            return await self._create_pagination_schema(
                strains, total_results, 1, total_results
            )
        else:
            # Use regular pagination for normal requests
            return await self._search_paginated_strains(
                filter_criteria=filter_criteria,
                page=params.page,
                per_page=params.per_page,
                sortField=params.sortField,
                sortOrder=params.sortOrder,
                error_message="Error searching genomes by string",
            )

    async def search_strains(
        self,
        params: GenomeAutocompleteQuerySchema,
    ) -> List[StrainSuggestionSchema]:
        try:
            search = Search(index=ES_INDEX_STRAIN)
            search = search.query(
                "wildcard", **{STRAIN_FIELD_ISOLATE_NAME: f"*{params.query.lower()}*"}
            )

            if params.species_acronym:
                search = search.filter(
                    "term", **{ES_FIELD_SPECIES_ACRONYM: params.species_acronym}
                )

            search = search[: params.limit]
            response = await sync_to_async(search.execute)()

            results = []
            for hit in response:
                # For StrainSuggestionSchema we only need isolate_name and assembly_name
                hit_dict = hit.to_dict()
                results.append(StrainSuggestionSchema(
                    isolate_name=hit_dict.get("isolate_name"),
                    assembly_name=hit_dict.get("assembly_name")
                ))

            return results

        except Exception as e:
            logger.error(f"Error searching strains: {e}")
            raise ServiceError(f"Error searching strains: {str(e)}")

    async def get_genomes(
        self,
        params: GetAllGenomesQuerySchema,
    ) -> GenomePaginationSchema:
        return await self._search_paginated_strains(
            filter_criteria={},
            page=params.page,
            per_page=params.per_page,
            sortField=params.sortField,
            sortOrder=params.sortOrder,
            error_message="Error fetching all genomes",
        )

    async def get_genome_by_strain_name(self, isolate_name: str):
        return await self._fetch_single_genome(
            filter_criteria={STRAIN_FIELD_ISOLATE_NAME: isolate_name},
            error_message=f"Error fetching genome by strain name {isolate_name}",
        )

    async def get_genomes_by_isolate_names(
        self,
        params: GenomesByIsolateNamesQuerySchema,
    ) -> List[GenomeResponseSchema]:
        isolate_names_list = [id.strip() for id in params.isolates.split(",")]
        return await self._fetch_and_validate_strains(
            filter_criteria={"isolate_name.keyword": isolate_names_list},
            schema=GenomeResponseSchema,
            error_message="Error fetching genomes by isolate names",
        )

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
                results.append(self._convert_hit_to_genome_schema(hit))

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
            return self._convert_hit_to_genome_schema(strain)

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
                results.append(self._convert_hit_to_genome_schema(hit))

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
            "species": ES_FIELD_SPECIES_ACRONYM,
            "isolate_name": f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",
            "genome": f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",  # Map 'genome' to 'isolate_name.keyword'
            "strain": f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",  # Map 'strain' to 'isolate_name.keyword'
            "name": f"{STRAIN_FIELD_ISOLATE_NAME}.keyword",  # Map 'name' to 'isolate_name.keyword'
        }

        # Return mapped field if it exists, otherwise return the original field
        return field_mapping.get(field, field)

    def convert_to_tsv(self, genomes: List[GenomeResponseSchema]) -> str:
        """Convert genome data to TSV format for download."""
        if not genomes:
            return ""

        # Define the columns to include in the TSV export
        columns = [
            "isolate_name",
            "species_scientific_name",
            "species_acronym",
            "assembly_name",
            "assembly_accession",
            "type_strain",
        ]

        # Create header row
        header = "\t".join(columns)

        # Create data rows
        rows = []
        for genome in genomes:
            row_data = []
            for col in columns:
                value = getattr(genome, col, "")
                value = str(value) if value is not None else ""

                # Escape tabs and newlines in the value
                value = value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
                row_data.append(value)

            rows.append("\t".join(row_data))

        return header + "\n" + "\n".join(rows)

    async def _fetch_all_strains_with_scroll(
        self, filter_criteria, sortField, sortOrder, schema
    ):
        """Fetch all strains using Elasticsearch scroll API for large downloads."""
        try:
            es_client = connections.get_connection()
            search_body = {"query": {"bool": {"must": []}}, "size": SCROLL_BATCH_SIZE}

            # Dynamically apply filters
            for field, value in filter_criteria.items():
                if isinstance(value, str):
                    if field == STRAIN_FIELD_ISOLATE_NAME:
                        search_body["query"]["bool"]["must"].append(
                            {
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
                            }
                        )
                    else:
                        search_body["query"]["bool"]["must"].append(
                            {"wildcard": {field: f"*{value}*"}}
                        )
                elif isinstance(value, list):
                    search_body["query"]["bool"]["must"].append(
                        {"terms": {field: value}}
                    )
                else:
                    search_body["query"]["bool"]["must"].append(
                        {"term": {field: value}}
                    )

            # Map "species" to its actual field
            sortField = self._resolve_sort_field(sortField)
            sort_order = "asc" if sortOrder == SORT_ASC else "desc"
            search_body["sort"] = [{sortField: {"order": sort_order}}]

            logger.info(
                f"Starting scroll search with query: {json.dumps(search_body, indent=2)}"
            )

            # Execute initial search
            response = await sync_to_async(
                lambda: es_client.search(
                    index=ES_INDEX_STRAIN, body=search_body, scroll=SCROLL_TIMEOUT
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
                    results.append(self._convert_hit_to_genome_schema(mock_hit))

                total_results += len(response["hits"]["hits"])
                logger.info(
                    f"Fetched {total_results} strains in {batch_count} batches..."
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
                f"Scroll search completed. Total strains fetched: {total_results}"
            )
            return results, total_results

        except Exception as e:
            logger.error(f"Error fetching strains with scroll API: {e}", exc_info=True)
            raise ServiceError(f"Error fetching strains with scroll API: {str(e)}")
