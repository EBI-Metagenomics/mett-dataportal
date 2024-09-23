import logging
from typing import Optional

from asgiref.sync import sync_to_async
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q

from .models import Species, Strain, Gene

logger = logging.getLogger(__name__)


class SearchService:

    def __init__(self):
        self.limit = 10

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
                suggestions.append(f"{strain.isolate_name} - ({strain.assembly_name})")

            # Uncomment if gene search is needed, along with optional species_id filtering
            # gene_filter = Q(gene_name__icontains=query)
            # if species_id is not None and species_id != '':
            #     gene_filter &= Q(strain__species_id=species_id)
            #
            # gene_query = await sync_to_async(lambda: list(
            #     Gene.objects.filter(gene_filter).select_related('strain__species')[:limit]
            # ))()
            # for gene in gene_query:
            #     suggestions.append(f"{gene.gene_name} ({gene.strain.isolate_name})")

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

    async def search_genomes(self, strain_id=None, query=None):
        try:
            if strain_id:
                logger.debug(f"Searching strain by ID: {strain_id}")
                strains = await sync_to_async(lambda: list(
                    Strain.objects.filter(id=strain_id)
                ))()
                logger.debug(f"Strains found for strain_id {strain_id}: {strains}")
                return strains

            elif query:
                logger.debug(f"Searching strains by query (fuzzy search): {query}")

                # Fuzzy search for Strains using TrigramSimilarity
                strain_query = await sync_to_async(lambda: list(
                    Strain.objects.annotate(
                        similarity=TrigramSimilarity('isolate_name', query) +
                                   TrigramSimilarity('assembly_name', query)
                    ).filter(similarity__gt=0.4)  # Adjust threshold as needed
                    .order_by('-similarity')
                    .select_related('species')
                ))()

                # If strains are found, return
                if strain_query:
                    logger.debug(f"strains found (fuzzy search): {strain_query}")
                    return strain_query

                # If no strains found, proceed to search for species
                logger.debug(f"No strains found. Searching species by query: {query}")
                species_query = await sync_to_async(lambda: list(
                    Species.objects.annotate(
                        similarity=TrigramSimilarity('scientific_name', query) +
                                   TrigramSimilarity('common_name', query)
                    ).filter(similarity__gt=0.1)
                    .order_by('-similarity')
                ))()

                if not species_query:
                    logger.debug(f"No species found for query '{query}'")
                    return []

                # Fetch all strains for all found species
                strains_from_species = []
                for species in species_query:
                    logger.debug(f"Fetching strains for species: {species.scientific_name}")
                    strains_for_species = await sync_to_async(lambda: list(
                        Strain.objects.filter(species=species).select_related('species')
                    ))()
                    strains_from_species.extend(strains_for_species)

                logger.debug(f"Strains found for species: {len(strains_from_species)}")

                return strains_from_species

            else:
                return []
        except Exception as e:
            logger.error(f"Error in search_genomes: {e}")
            return []

    async def search_genome_by_gene(self, gene_id=None):
        try:
            if gene_id:
                logger.debug(f"Searching genome by gene ID: {gene_id}")

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
