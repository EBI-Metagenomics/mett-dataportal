import logging
from typing import Optional, List

from asgiref.sync import sync_to_async
from dataportal import settings
from dataportal.models import Strain
from dataportal.schemas import (
    TypeStrainSchema,
    GenomePaginationSchema,
    SearchGenomeSchema,
)
from django.db.models import Q
from ninja.errors import HttpError

logger = logging.getLogger(__name__)


class GenomeService:
    def __init__(self, limit: int = 10):
        self.limit = limit

    async def get_type_strains(self) -> List[TypeStrainSchema]:
        try:
            strains = await sync_to_async(list)(Strain.objects.filter(type_strain=True))
            return [
                TypeStrainSchema.model_validate(strain.__dict__) for strain in strains
            ]
        except Exception as e:
            logger.error(f"Error fetching type strains: {e}")
            raise HttpError(500, "Internal Server Error")

    async def search_genomes_by_string(
        self,
        query: str,
        page: int = 1,
        per_page: int = 10,
        sortField: str = "isolate_name",
        sortOrder: str = "asc",
    ) -> GenomePaginationSchema:
        try:
            strains, total_results = await self._fetch_paginated_strains(
                Q(isolate_name__icontains=query), page, per_page, sortField, sortOrder
            )
            return await self._create_pagination_schema(
                strains, total_results, page, per_page
            )
        except Exception as e:
            logger.error(f"Error searching genomes by string: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genomes_by_species(
        self,
        species_id: int,
        page: int = 1,
        per_page: int = 10,
        sortField: str = "isolate_name",
        sortOrder: str = "asc",
    ) -> GenomePaginationSchema:
        try:
            strains, total_results = await self._fetch_paginated_strains(
                Q(species_id=species_id), page, per_page, sortField, sortOrder
            )
            return await self._create_pagination_schema(
                strains, total_results, page, per_page
            )
        except Exception as e:
            logger.error(f"Error fetching genomes by species: {e}")
            raise HttpError(500, "Internal Server Error")

    async def search_genomes_by_species_and_string(
        self,
        species_id: int,
        query: str,
        page: int = 1,
        per_page: int = 10,
        sortField: str = "isolate_name",
        sortOrder: str = "asc",
    ) -> GenomePaginationSchema:
        try:
            filter_criteria = Q(species_id=species_id, isolate_name__icontains=query)
            strains, total_results = await self._fetch_paginated_strains(
                filter_criteria, page, per_page, sortField, sortOrder
            )
            return await self._create_pagination_schema(
                strains, total_results, page, per_page
            )
        except Exception as e:
            logger.error(f"Error searching genomes by species and string: {e}")
            raise HttpError(500, "Internal Server Error")

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
                    Strain.objects.filter(strain_filter).select_related("species")[
                        : limit or self.limit
                    ]
                )
            )()
            return [
                {
                    "strain_id": strain.id,
                    "isolate_name": strain.isolate_name,
                    "assembly_name": strain.assembly_name,
                }
                for strain in strains
            ]
        except Exception as e:
            logger.error(f"Error executing strain search query: {e}")
            return []

    async def get_genomes(
        self,
        page: int = 1,
        per_page: int = 10,
        sortField: str = "isolate_name",
        sortOrder: str = "asc",
    ) -> GenomePaginationSchema:
        try:
            # Fetch paginated strains
            strains, total_results = await self._fetch_paginated_strains(
                Q(), page, per_page, sortField, sortOrder
            )
            return await self._create_pagination_schema(
                strains, total_results, page, per_page
            )
        except Exception as e:
            logger.error(f"Error fetching genomes: {e}")
            raise HttpError(500, "Internal Server Error")

    async def search_genomes(
        self, query: str, page: int = 1, per_page: int = 10
    ) -> GenomePaginationSchema:
        try:
            # Fetch paginated strains matching the search query
            strains, total_results = await self._fetch_paginated_strains(
                Q(isolate_name__icontains=query), page, per_page
            )
            return await self._create_pagination_schema(
                strains, total_results, page, per_page
            )
        except Exception as e:
            logger.error(f"Error searching genomes: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genome_by_id(self, genome_id: int):
        try:
            strain = await sync_to_async(
                lambda: Strain.objects.select_related("species").get(id=genome_id)
            )()
            return SearchGenomeSchema.model_validate(
                {
                    "id": strain.id,
                    "species": strain.species.scientific_name,
                    "common_name": (
                        strain.species.common_name
                        if strain.species.common_name
                        else None
                    ),
                    "isolate_name": strain.isolate_name,
                    "assembly_name": strain.assembly_name,
                    "assembly_accession": strain.assembly_accession,
                    "fasta_file": strain.fasta_file,
                    "gff_file": strain.gff_file,
                    "fasta_url": (
                        f"{settings.ASSEMBLY_FTP_PATH}/{strain.fasta_file}"
                        if strain.fasta_file
                        else None
                    ),
                    "gff_url": (
                        f"{settings.GFF_FTP_PATH.format(strain.isolate_name)}/{strain.gff_file}"
                        if strain.gff_file
                        else None
                    ),
                    "contigs": await sync_to_async(
                        lambda: [
                            {"seq_id": contig.seq_id, "length": contig.length}
                            for contig in strain.contigs.all()
                        ]
                    )(),
                }
            )
        except Strain.DoesNotExist:
            logger.error(f"Genome with ID {genome_id} not found")
            raise HttpError(404, f"Genome with ID {genome_id} not found")
        except Exception as e:
            logger.error(f"Error fetching genome by ID {genome_id}: {e}")
            raise HttpError(500, "Internal Server Error")

    # Helper Methods
    async def _fetch_paginated_strains(
        self,
        filter_criteria: Q,
        page: int,
        per_page: int,
        sortField: str = "isolate_name",
        sortOrder: str = "asc",
    ):
        if not sortField:
            sortField = "isolate_name"
        if sortOrder not in ("asc", "desc"):
            sortOrder = "asc"

        # Apply sorting
        ordering = f"{'-' if sortOrder == 'desc' else ''}{sortField}"
        start = (page - 1) * per_page

        strains = await sync_to_async(
            lambda: list(
                Strain.objects.select_related("species")
                .filter(filter_criteria)
                .order_by(ordering)[start : start + per_page]
            )
        )()
        total_results = await sync_to_async(
            Strain.objects.filter(filter_criteria).count
        )()
        return strains, total_results

    async def _create_pagination_schema(self, strains, total_results, page, per_page):
        serialized_strains = [
            SearchGenomeSchema.model_validate(
                {
                    "id": strain.id,
                    "isolate_name": strain.isolate_name,
                    "assembly_name": strain.assembly_name,
                    "assembly_accession": strain.assembly_accession,
                    "fasta_file": strain.fasta_file,
                    "gff_file": strain.gff_file,
                    "species": strain.species.scientific_name,
                    "common_name": (
                        strain.species.common_name
                        if strain.species.common_name
                        else None
                    ),
                    "fasta_url": (
                        f"{settings.ASSEMBLY_FTP_PATH}/{strain.fasta_file}"
                        if strain.fasta_file
                        else None
                    ),
                    "gff_url": (
                        f"{settings.GFF_FTP_PATH.format(strain.isolate_name)}/{strain.gff_file}"
                        if strain.gff_file
                        else None
                    ),
                    "contigs": await sync_to_async(
                        lambda: [
                            {"seq_id": contig.seq_id, "length": contig.length}
                            for contig in strain.contigs.all()
                        ]
                    )(),
                }
            )
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
