import logging
from typing import Optional, List

from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Strain, Gene

logger = logging.getLogger(__name__)


class SearchService:

    def __init__(self):
        self.limit = 10

    def paginate_results(self, queryset, page: int, per_page: int):
        paginator = Paginator(queryset, per_page)
        page_obj = paginator.get_page(page)
        return {
            "results": list(page_obj.object_list),
            "page_number": page_obj.number,
            "num_pages": paginator.num_pages,
            "has_previous": page_obj.has_previous(),
            "has_next": page_obj.has_next(),
            "total_results": paginator.count,
        }

    async def search_strains(self, query: str, limit: int = 10, species_id: Optional[int] = None):
        try:
            suggestions = []
            # Search Strains, with optional species_id filter
            strain_filter = Q(isolate_name__icontains=query) | Q(assembly_name__icontains=query)

            # Apply species_id filter only if it is provided and valid
            if species_id is not None and species_id != '':
                strain_filter &= Q(species_id=species_id)

            strain_query = await sync_to_async(lambda: list(
                Strain.objects.filter(strain_filter).select_related('species')[:limit]
            ))()

            for strain in strain_query:
                suggestions.append({
                    "strain_id": strain.id,
                    "isolate_name": strain.isolate_name,
                    "assembly_name": strain.assembly_name
                })

            return suggestions

        except Exception as e:
            logger.error(f"Error executing autocomplete query: {e}")
            return []

    async def get_genomes(self, page: int = 1, per_page: int = 10):
        try:
            strains = await sync_to_async(lambda: list(Strain.objects.all()))()
            return self.paginate_results(strains, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genomes: {e}")
            return self.paginate_results([], page, per_page)

    async def search_genomes(self, query: str = None, species_id: Optional[int] = None, page: int = 1,
                             per_page: int = 10):
        try:
            filters = Q()
            if query:
                filters &= Q(isolate_name__icontains=query) | Q(assembly_name__icontains=query)
            if species_id:
                filters &= Q(species_id=species_id)

            strains = await sync_to_async(lambda: list(Strain.objects.filter(filters).select_related('species')))()
            return self.paginate_results(strains, page, per_page)

        except Exception as e:
            logger.error(f"Error searching genomes: {e}")
            return self.paginate_results([], page, per_page)

    async def get_genomes_by_species(self, species_id: int, page: int = 1, per_page: int = 10):
        try:
            strains = await sync_to_async(
                lambda: list(Strain.objects.filter(species_id=species_id).select_related('species')))()
            return self.paginate_results(strains, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genomes by species ID {species_id}: {e}")
            return self.paginate_results([], page, per_page)

    async def get_genome_by_id(self, genome_id: int):
        try:
            return await sync_to_async(lambda: get_object_or_404(Strain, id=genome_id))()
        except Exception as e:
            logger.error(f"Error fetching genome by ID {genome_id}: {e}")
            return None

    async def get_gene_by_id(self, gene_id: int):
        try:
            return await sync_to_async(lambda: get_object_or_404(Gene, id=gene_id))()
        except Exception as e:
            logger.error(f"Error fetching gene by ID {gene_id}: {e}")
            return None

    async def get_genes(self, page: int = 1, per_page: int = 10):
        try:
            genes = await sync_to_async(lambda: list(Gene.objects.all()))()
            return self.paginate_results(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes: {e}")
            return self.paginate_results([], page, per_page)

    async def search_genes(self, query: str = None, genome_id: Optional[int] = None,
                           genome_ids: Optional[List[int]] = None, page: int = 1, per_page: int = 10):
        try:
            filters = Q()
            if query:
                filters &= Q(gene_name__icontains=query) | Q(description__icontains=query)
            if genome_id:
                filters &= Q(strain_id=genome_id)
            elif genome_ids:
                filters &= Q(strain_id__in=genome_ids)

            genes = await sync_to_async(lambda: list(Gene.objects.filter(filters).select_related('strain')))()
            return self.paginate_results(genes, page, per_page)

        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            return self.paginate_results([], page, per_page)

    async def get_genes_by_genome(self, genome_id: int, page: int = 1, per_page: int = 10):
        try:
            genes = await sync_to_async(
                lambda: list(Gene.objects.filter(strain_id=genome_id).select_related('strain')))()
            return self.paginate_results(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes for genome ID {genome_id}: {e}")
            return self.paginate_results([], page, per_page)

    async def get_genes_by_multiple_genomes(self, genome_ids: List[int], page: int = 1, per_page: int = 10):
        try:
            genes = await sync_to_async(
                lambda: list(Gene.objects.filter(strain_id__in=genome_ids).select_related('strain')))()
            return self.paginate_results(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes for genome IDs {genome_ids}: {e}")
            return self.paginate_results([], page, per_page)
