import logging
from typing import Optional, List

from asgiref.sync import sync_to_async
from django.conf import settings

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Strain, Gene

logger = logging.getLogger(__name__)


class SearchService:

    def __init__(self, limit: int = settings.DEFAULT_LIMIT):
        self.limit = limit

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

    async def fetch_objects(self, model, filters=None, select_related=None, limit=None):
        filters = filters or Q()
        queryset = model.objects.filter(filters)

        if select_related:
            queryset = queryset.select_related(*select_related)

        if limit:
            queryset = queryset[:limit]

        return await sync_to_async(lambda: list(queryset))()

    async def search_strains(self, query: str, limit: int = None, species_id: Optional[int] = None):
        try:
            strain_filter = Q(isolate_name__icontains=query) | Q(assembly_name__icontains=query)

            if species_id:
                strain_filter &= Q(species_id=species_id)

            strains = await self.fetch_objects(
                model=Strain,
                filters=strain_filter,
                select_related=['species'],
                limit=limit or self.limit
            )

            return [
                {"strain_id": strain.id, "isolate_name": strain.isolate_name, "assembly_name": strain.assembly_name}
                for strain in strains
            ]
        except Exception as e:
            logger.error(f"Error executing autocomplete query: {e}")
            return []

    async def get_genomes(self, page: int = 1, per_page: int = 10):
        try:
            strains = await self.fetch_objects(model=Strain, select_related=['species'])
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

            strains = await self.fetch_objects(model=Strain, filters=filters, select_related=['species'])
            return self.paginate_results(strains, page, per_page)
        except Exception as e:
            logger.error(f"Error searching genomes: {e}")
            return self.paginate_results([], page, per_page)

    async def get_genomes_by_species(self, species_id: int, page: int = 1, per_page: int = 10):
        try:
            strains = await self.fetch_objects(
                model=Strain,
                filters=Q(species_id=species_id),
                select_related=['species']
            )
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

    async def autocomplete_gene_suggestions(self, query: str, limit: int = None, species_id: Optional[int] = None,
                                            genome_ids: Optional[List[int]] = None):
        try:
            gene_filter = Q(gene_name__icontains=query)

            if species_id:
                gene_filter &= Q(strain__species_id=species_id)
            if genome_ids:
                gene_filter &= Q(strain_id__in=genome_ids)

            genes = await self.fetch_objects(
                model=Gene,
                filters=gene_filter,
                select_related=['strain'],
                limit=limit or self.limit
            )

            return [
                {"gene_id": gene.id, "gene_name": gene.gene_name, "strain_name": gene.strain.isolate_name}
                for gene in genes
            ]
        except Exception as e:
            logger.error(f"Error fetching gene autocomplete suggestions: {e}")
            return []

    async def get_gene_by_id(self, gene_id: int):
        try:
            return await sync_to_async(lambda: get_object_or_404(Gene, id=gene_id))()
        except Exception as e:
            logger.error(f"Error fetching gene by ID {gene_id}: {e}")
            return None

    async def get_genes(self, page: int = 1, per_page: int = 10):
        try:
            genes = await self.fetch_objects(model=Gene, select_related=['strain'])
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

            genes = await self.fetch_objects(model=Gene, filters=filters, select_related=['strain'])
            return self.paginate_results(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            return self.paginate_results([], page, per_page)

    async def get_genes_by_genome(self, genome_id: int, page: int = 1, per_page: int = 10):
        try:
            genes = await self.fetch_objects(
                model=Gene,
                filters=Q(strain_id=genome_id),
                select_related=['strain']
            )
            return self.paginate_results(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes for genome ID {genome_id}: {e}")
            return self.paginate_results([], page, per_page)

    async def get_genes_by_multiple_genomes(self, genome_ids: List[int], page: int = 1, per_page: int = 10):
        try:
            genes = await self.fetch_objects(
                model=Gene,
                filters=Q(strain_id__in=genome_ids),
                select_related=['strain']
            )
            return self.paginate_results(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes for genome IDs {genome_ids}: {e}")
            return self.paginate_results([], page, per_page)

    async def search_genes_in_strain(self, strain_id: int, query: str, limit: int = 10):
        try:
            gene_filter = Q(strain_id=strain_id, gene_name__icontains=query)
            genes = await self.fetch_objects(
                model=Gene,
                filters=gene_filter,
                limit=limit
            )
            return [{"gene_name": gene.gene_name, "description": gene.description} for gene in genes]
        except Exception as e:
            logger.error(f"Error searching genes in strain: {e}")
            return []

    async def search_genes_globally(self, query: str, limit: int = 10):
        try:
            gene_filter = Q(gene_name__icontains=query) | Q(description__icontains=query)
            genes = await self.fetch_objects(
                model=Gene,
                filters=gene_filter,
                limit=limit
            )
            return [
                {
                    "gene_name": gene.gene_name,
                    "seq_id": gene.seq_id,
                    "strain": gene.strain.isolate_name,
                    "assembly": gene.strain.assembly_name,
                    "description": gene.description
                } for gene in genes
            ]
        except Exception as e:
            logger.error(f"Error searching genes globally: {e}")
            return []

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

            genes = await self.fetch_objects(model=Gene, filters=filters, select_related=['strain'])
            serialized_genes = [
                {
                    "id": gene.id,
                    "seq_id": gene.seq_id,
                    "gene_name": gene.gene_name,
                    "description": gene.description,
                    "strain": gene.strain.isolate_name,
                    "assembly": gene.strain.assembly_name if gene.strain.assembly_name else None,
                    "locus_tag": gene.locus_tag
                }
                for gene in genes
            ]
            return self.paginate_results(serialized_genes, page, per_page)
        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            return self.paginate_results([], page, per_page)
