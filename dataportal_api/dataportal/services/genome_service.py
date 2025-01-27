import logging
from typing import Optional, List

from asgiref.sync import sync_to_async
from django.db.models import Q

from dataportal import settings
from dataportal.models import Strain
from dataportal.schemas import (
    GenomePaginationSchema,
    GenomeResponseSchema,
)
from dataportal.utils.constants import (
    FIELD_ID,
    STRAIN_FIELD_STRAIN_ID,
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
    SORT_DESC,
    DEFAULT_PER_PAGE_CNT,
    STRAIN_FIELD_TYPE_STRAIN,
    SPECIES_FIELD_COMMON_NAME,
    SPECIES_FIELD_SCIENTIFIC_NAME,
    SPECIES_FIELD_ACRONYM,
)
from dataportal.utils.exceptions import ServiceError, GenomeNotFoundError

logger = logging.getLogger(__name__)


class GenomeService:
    def __init__(self, limit: int = 10):
        self.limit = limit

    async def get_type_strains(self) -> List[GenomeResponseSchema]:
        return await self._fetch_and_validate_strains(
            filter_criteria=Q(type_strain=True),
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
        return await self._search_paginated_strains(
            filter_criteria=Q(isolate_name__icontains=query),
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error searching genomes by string",
        )

    async def get_genomes_by_species(
            self,
            species_id: int,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sortField: str = STRAIN_FIELD_ISOLATE_NAME,
            sortOrder: str = SORT_ASC,
    ) -> GenomePaginationSchema:
        return await self._search_paginated_strains(
            filter_criteria=Q(species_id=species_id),
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error fetching genomes by species",
        )

    async def search_genomes_by_species_and_string(
            self,
            species_id: int,
            query: str,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sortField: str = STRAIN_FIELD_ISOLATE_NAME,
            sortOrder: str = SORT_ASC,
    ) -> GenomePaginationSchema:
        filter_criteria = Q(species_id=species_id, isolate_name__icontains=query)
        return await self._search_paginated_strains(
            filter_criteria=filter_criteria,
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error searching genomes by species and string",
        )

    async def search_strains(
            self, query: str, limit: int = None, species_id: Optional[int] = None
    ):
        try:
            strain_filter = Q(isolate_name__icontains=query) | Q(
                assembly_name__icontains=query
            )
            if species_id:
                strain_filter &= Q(species_id=species_id)
            strains = await sync_to_async(
                lambda: list(
                    Strain.objects.filter(strain_filter).select_related(
                        STRAIN_FIELD_SPECIES
                    )[: limit or self.limit]
                )
            )()
            return [
                {
                    STRAIN_FIELD_STRAIN_ID: strain.id,
                    STRAIN_FIELD_ISOLATE_NAME: strain.isolate_name,
                    STRAIN_FIELD_ASSEMBLY_NAME: strain.assembly_name,
                }
                for strain in strains
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
            filter_criteria=Q(),
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            error_message="Error fetching genomes",
        )

    async def get_genome_by_id(self, genome_id: int):
        result = await self._fetch_single_genome(
            filter_criteria=Q(id=genome_id),
            error_message=f"Error fetching genome by ID {genome_id}",
        )
        logger.debug(f"Fetched genome successfully: {result}")
        return result

    async def get_genome_by_strain_name(self, strain_name: str):
        return await self._fetch_single_genome(
            filter_criteria=Q(isolate_name__iexact=strain_name),
            error_message=f"Error fetching genome by strain name {strain_name}",
        )

    async def get_genomes_by_ids(
            self, genome_ids: List[int]
    ) -> List[GenomeResponseSchema]:
        if not genome_ids:
            return []
        filter_criteria = Q(id__in=genome_ids)
        try:
            strains = await self._fetch_and_validate_strains(
                filter_criteria=filter_criteria,
                schema=GenomeResponseSchema,
                error_message="Error fetching genomes by IDs",
            )
            return strains
        except Exception as e:
            logger.error(f"Error in get_genomes_by_ids: {e}", exc_info=True)
            raise ServiceError(f"Could not fetch genomes by IDs: {e}")

    async def get_genomes_by_isolate_names(
            self, isolate_names: List[str]
    ) -> List[GenomeResponseSchema]:
        if not isolate_names:
            return []
        filter_criteria = Q(isolate_name__in=isolate_names)
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
        try:
            strains = await sync_to_async(list)(
                Strain.objects.filter(filter_criteria).select_related(
                    STRAIN_FIELD_SPECIES
                )
            )
            return [
                schema.model_validate(await self._serialize_strain(strain))
                for strain in strains
            ]
        except Exception as e:
            logger.error(f"{error_message}: {e}")
            raise ServiceError(e)

    async def _search_paginated_strains(
            self, filter_criteria, page, per_page, sortField, sortOrder, error_message
    ):
        try:
            strains, total_results = await self._fetch_paginated_strains(
                filter_criteria, page, per_page, sortField, sortOrder
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

            strain = await sync_to_async(
                lambda: Strain.objects.select_related(STRAIN_FIELD_SPECIES).get(
                    **filter_kwargs
                )
            )()

            serialized_strain = await self._serialize_strain(strain)
            return GenomeResponseSchema.model_validate(serialized_strain)

        except Strain.DoesNotExist:
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
            self,
            filter_criteria: Q,
            page: int,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sortField: str = STRAIN_FIELD_ISOLATE_NAME,
            sortOrder: str = SORT_ASC,
    ):
        if not sortField:
            sortField = STRAIN_FIELD_ISOLATE_NAME
        if sortOrder not in (SORT_ASC, SORT_DESC):
            sortOrder = SORT_ASC

        ordering = f"{'-' if sortOrder == SORT_DESC else ''}{sortField}"
        start = (page - 1) * per_page

        strains = await sync_to_async(
            lambda: list(
                Strain.objects.select_related(STRAIN_FIELD_SPECIES)
                .filter(filter_criteria)
                .order_by(ordering)[start: start + per_page]
            )
        )()
        total_results = await sync_to_async(
            lambda: Strain.objects.filter(filter_criteria).count()
        )()

        return strains, total_results

    async def _create_pagination_schema(self, strains, total_results, page, per_page):
        serialized_strains = [
            GenomeResponseSchema.model_validate(await self._serialize_strain(strain))
            for strain in strains
        ]

        return GenomePaginationSchema(
            results=serialized_strains,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=(page * per_page) < total_results,
            total_results=total_results,
        )
