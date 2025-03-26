import json
import logging
from typing import List
from typing import Optional

from asgiref.sync import sync_to_async
from django.db.models import Q
from elasticsearch_dsl import Search

from dataportal import settings
from dataportal.models import StrainDocument
from dataportal.schemas import (
    GenomePaginationSchema,
    GenomeResponseSchema,
)
from dataportal.utils.constants import (
    FIELD_ID,
    STRAIN_FIELD_ISOLATE_NAME,
    STRAIN_FIELD_ASSEMBLY_NAME,
    STRAIN_FIELD_ASSEMBLY_ACCESSION,
    STRAIN_FIELD_FASTA_FILE,
    STRAIN_FIELD_GFF_FILE,
    STRAIN_FIELD_SPECIES,
    STRAIN_FIELD_FASTA_URL,
    STRAIN_FIELD_GFF_URL,
    STRAIN_FIELD_CONTIGS,
    STRAIN_FIELD_CONTIG_SEQ_ID,
    STRAIN_FIELD_CONTIG_LEN,
    SORT_ASC,
    DEFAULT_PER_PAGE_CNT,
    STRAIN_FIELD_TYPE_STRAIN,
    SPECIES_FIELD_COMMON_NAME,
    SPECIES_FIELD_SCIENTIFIC_NAME,
    SPECIES_FIELD_ACRONYM,
    STRAIN_FIELD_SPECIES_ACRONYM,
    ES_FIELD_SPECIES_NAME,
    ES_FIELD_SPECIES_ACRONYM,
)
from dataportal.utils.exceptions import ServiceError, GenomeNotFoundError

logger = logging.getLogger(__name__)


class GenomeService:
    INDEX_NAME = "strain_index"

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
    ) -> GenomePaginationSchema:
        """Search genomes in Elasticsearch by isolate name (partial match)."""
        return await self._search_paginated_strains(
            filter_criteria={STRAIN_FIELD_ISOLATE_NAME: query},
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
            filter_criteria={STRAIN_FIELD_SPECIES_ACRONYM: species_acronym},
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
        filter_criteria = {STRAIN_FIELD_SPECIES_ACRONYM: species_acronym, STRAIN_FIELD_ISOLATE_NAME: query}
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
            search = Search(index=self.INDEX_NAME)

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

            logger.info(f"Final Elasticsearch Query: {json.dumps(search.to_dict(), indent=2)}")
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
        logger.info(f"Getting genomes for isolate names: {isolate_names}")
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
            search = Search(index=self.INDEX_NAME)

            for field, value in filter_criteria.items():
                if isinstance(value, list):
                    search = search.filter("terms", **{field: value})
                else:
                    search = search.filter("term", **{field: value})

            response = await sync_to_async(search.execute)()

            results = []
            for hit in response:
                strain_data = hit.to_dict()

                # Compute fasta_url and gff_url
                strain_data["fasta_url"] = (
                    f"{settings.ASSEMBLY_FTP_PATH}/{strain_data['fasta_file']}"
                    if strain_data.get("fasta_file")
                    else None
                )
                strain_data["gff_url"] = (
                    f"{settings.GFF_FTP_PATH.format(strain_data[STRAIN_FIELD_ISOLATE_NAME])}/{strain_data['gff_file']}"
                    if strain_data.get("gff_file") and strain_data.get(STRAIN_FIELD_ISOLATE_NAME)
                    else None
                )

                # Validate and append
                results.append(schema.model_validate(strain_data))

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
                filter_criteria, page, per_page, sortField, sortOrder
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

            strain = await sync_to_async(
                lambda: StrainDocument.objects.select_related(STRAIN_FIELD_SPECIES).get(
                    **filter_kwargs
                )
            )()

            serialized_strain = await self._serialize_strain(strain)
            return GenomeResponseSchema.model_validate(serialized_strain)

        except StrainDocument.DoesNotExist:
            logger.error(error_message)
            raise GenomeNotFoundError(error_message)
        except Exception as e:
            logger.error(f"{error_message}: {e}", exc_info=True)
            raise ServiceError(e)

    async def _serialize_strain(self, strain):
        contigs = await sync_to_async(
            lambda: list(
                strain.contigs.values(
                    STRAIN_FIELD_CONTIG_SEQ_ID, STRAIN_FIELD_CONTIG_LEN
                )
            )
        )()

        species = strain.species

        return {
            FIELD_ID: strain.id,
            STRAIN_FIELD_SPECIES: {
                FIELD_ID: species.id,
                SPECIES_FIELD_SCIENTIFIC_NAME: species.scientific_name,
                SPECIES_FIELD_COMMON_NAME: species.common_name or None,
                SPECIES_FIELD_ACRONYM: species.acronym or None,
            },
            STRAIN_FIELD_ISOLATE_NAME: strain.isolate_name,
            STRAIN_FIELD_ASSEMBLY_NAME: strain.assembly_name,
            STRAIN_FIELD_ASSEMBLY_ACCESSION: strain.assembly_accession,
            STRAIN_FIELD_FASTA_FILE: strain.fasta_file,
            STRAIN_FIELD_GFF_FILE: strain.gff_file,
            STRAIN_FIELD_FASTA_URL: (
                f"{settings.ASSEMBLY_FTP_PATH}/{strain.fasta_file}"
                if strain.fasta_file
                else None
            ),
            STRAIN_FIELD_GFF_URL: (
                f"{settings.GFF_FTP_PATH.format(strain.isolate_name)}/{strain.gff_file}"
                if strain.gff_file
                else None
            ),
            STRAIN_FIELD_TYPE_STRAIN: strain.type_strain,
            STRAIN_FIELD_CONTIGS: contigs,
        }

    async def _fetch_paginated_strains(
            self, filter_criteria, page, per_page, sortField, sortOrder
    ):
        """Fetch paginated strains from Elasticsearch with optimized searching."""
        try:
            search = Search(index=self.INDEX_NAME)

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
                else:
                    search = search.query("term", **{field: value})

            # Map "species" to its actual field
            if sortField == STRAIN_FIELD_SPECIES:
                sortField = STRAIN_FIELD_SPECIES_ACRONYM

            # Use .keyword for text fields
            if sortField in [STRAIN_FIELD_ISOLATE_NAME, ES_FIELD_SPECIES_NAME]:
                sortField = f"{sortField}.keyword"

            sort_order = "asc" if sortOrder == SORT_ASC else "desc"
            search = search.sort({sortField: {"order": sort_order}})

            # Apply pagination
            search = search[(page - 1) * per_page: page * per_page]

            logger.info(f"Final Elasticsearch Query: {json.dumps(search.to_dict(), indent=2)}")

            response = await sync_to_async(search.execute)()
            total_results = response.hits.total.value if hasattr(response.hits.total, 'value') else len(response)

            results = []
            for hit in response:
                strain_data = hit.to_dict()

                # Compute fasta_url and gff_url
                strain_data["fasta_url"] = (
                    f"{settings.ASSEMBLY_FTP_PATH}/{strain_data['fasta_file']}"
                    if strain_data.get("fasta_file")
                    else None
                )
                strain_data["gff_url"] = (
                    f"{settings.GFF_FTP_PATH.format(strain_data[STRAIN_FIELD_ISOLATE_NAME])}/{strain_data['gff_file']}"
                    if strain_data.get("gff_file") and strain_data.get(STRAIN_FIELD_ISOLATE_NAME)
                    else None
                )

                results.append(strain_data)

            return results, total_results

        except Exception as e:
            logger.error(f"Error fetching paginated strains: {e}")
            raise ServiceError(f"Error fetching paginated strains: {str(e)}")

    async def _create_pagination_schema(self, strains, total_results, page, per_page):
        """Create pagination schema for search results."""
        serialized_strains = [
            GenomeResponseSchema.model_validate(strain) for strain in strains
        ]

        return GenomePaginationSchema(
            results=serialized_strains,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=(page * per_page) < total_results,
            total_results=total_results,
        )
