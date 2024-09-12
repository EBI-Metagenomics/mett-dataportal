import logging

from asgiref.sync import sync_to_async
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db.models import Q

from .models import Species, Strain, Gene

logger = logging.getLogger(__name__)


class SearchService:

    def __init__(self):
        self.limit = 10

    async def search_strains(self, query: str, limit: int = 10):
        try:
            suggestions = []

            # Search Species
            species_query = await sync_to_async(lambda: list(
                Species.objects.filter(
                    Q(scientific_name__icontains=query) | Q(common_name__icontains=query)
                )[:limit]
            ))()
            for species in species_query:
                suggestions.append(f"{species.scientific_name} ({species.common_name})")

            # Search Strains
            strain_query = await sync_to_async(lambda: list(
                Strain.objects.filter(
                    Q(isolate_name__icontains=query) | Q(assembly_name__icontains=query)
                ).select_related('species')[:limit]
            ))()
            for strain in strain_query:
                suggestions.append(f"{strain.isolate_name} - ({strain.assembly_name})")

            # Search Genes
            gene_query = await sync_to_async(lambda: list(
                Gene.objects.filter(
                    Q(gene_name__icontains=query)
                ).select_related('strain__species')[:limit]
            ))()
            for gene in gene_query:
                suggestions.append(f"{gene.gene_name} ({gene.strain.isolate_name})")

            return suggestions

        except Exception as e:
            logger.error(f"Error executing autocomplete query: {e}")
            return []

    def search_genes_in_strain(self, strain_id: int, query: str):
        try:
            search_vector = SearchVector('gene_name', 'description')
            search_query = SearchQuery(query)
            strain = Strain.objects.get(id=strain_id)
            return Gene.objects.filter(strain=strain).annotate(
                search=search_vector
            ).filter(search=search_query)
        except Exception as e:
            logger.error(f"Error searching genes in strain {strain_id}: {e}")
            return []

    def search_genes_globally(self, query: str):
        try:
            search_vector = SearchVector('gene_name', 'description')
            search_query = SearchQuery(query)
            return Gene.objects.annotate(
                search=search_vector
            ).filter(search=search_query)
        except Exception as e:
            logger.error(f"Error searching genes globally: {e}")
            return []

    def search_genes_in_strains(self, strain_query: str, gene_query: str):
        try:
            strain_search_vector = SearchVector('isolate_name', 'assembly_name')
            strain_search_query = SearchQuery(strain_query)

            strains = Strain.objects.annotate(
                search=strain_search_vector
            ).filter(search=strain_search_query)

            gene_search_vector = SearchVector('gene_name', 'description')
            gene_search_query = SearchQuery(gene_query)

            return Gene.objects.filter(strain__in=strains).annotate(
                search=gene_search_vector
            ).filter(search=gene_search_query)
        except Exception as e:
            logger.error(f"Error searching genes across strains: {e}")
            return []

    async def get_search_results(self, strain_id=None, query=None):
        try:
            if strain_id:
                logger.debug(f"Searching strain by ID: {strain_id}")
                strains = await sync_to_async(lambda: list(
                    Strain.objects.filter(id=strain_id)
                ))()
                logger.debug(f"Strains found for strain_id {strain_id}: {strains}")
            elif query:
                logger.debug(f"Searching strains by query: {query}")
                strains = await sync_to_async(lambda: list(
                    Strain.objects.filter(isolate_name__icontains=query)
                ))()
                logger.debug(f"Strains found for query '{query}': {strains}")
            else:
                strains = []
            return strains
        except Exception as e:
            logger.error(f"Error in get_search_results: {e}")
            return []

    async def get_search_results_by_gene(self, gene_id=None):
        try:
            if gene_id:
                logger.debug(f"Searching strains by gene ID: {gene_id}")

                strains = await sync_to_async(lambda: list(
                    Strain.objects.filter(genes__id=gene_id)
                ))()

                logger.debug(f"Strains fetched for gene_id {gene_id}: {strains}")
                return strains

            logger.debug("No gene_id provided, returning empty list.")
            return []
        except Exception as e:
            logger.error(f"Error in get_search_results_by_gene: {e}")
            return []
