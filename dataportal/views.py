import logging

from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Strain
from .services import SearchService
from .utils import construct_file_urls

logger = logging.getLogger(__name__)


class SearchResultsView(View):
    async def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '').strip()
        isolate_name = request.GET.get('isolate-name', '').strip()
        search_term = isolate_name or query
        results = []
        paginator = None

        logger.debug(f"Search term: {search_term}")

        try:
            if search_term:
                logger.debug("Search term exists, proceeding with search")
                sort_field = request.GET.get('sortField', '')
                sort_order = request.GET.get('sortOrder', '')
                page_number = int(request.GET.get('page', 1))
                per_page = 10

                logger.debug(f"Calling SearchService.get_search_results with query: {search_term}")
                full_results = await SearchService.get_search_results(query=search_term)
                logger.debug(f"Search results: {full_results}")

                logger.debug("Instantiating Paginator")
                paginator = await sync_to_async(Paginator)(full_results, per_page)
                logger.debug(f"Paginator instantiated with {paginator.num_pages} pages")

                logger.debug(f"Getting page {page_number}")
                page_obj = await sync_to_async(paginator.page)(page_number)
                logger.debug(f"Page object: {page_obj}")

                results = await sync_to_async(lambda: list(page_obj.object_list))()
                logger.debug(f"Results: {results}")

            return JsonResponse({
                'results': results,
                'page_number': page_obj.number if page_obj else 1,
                'num_pages': paginator.num_pages if paginator else 1,
                'has_previous': page_obj.has_previous() if page_obj else False,
                'has_next': page_obj.has_next() if page_obj else False,
            })

        except Exception as e:
            logger.error(f"Error in search: {e}")
            return JsonResponse({'error': str(e)}, status=500)


class Autocomplete(View):
    async def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '').strip()
        if query:
            suggestions = await SearchService.search_strains(query)
            return JsonResponse({'suggestions': suggestions})
        return JsonResponse({'suggestions': []})


class JBrowseView(View):
    def get_context_data(self, **kwargs):
        isolate_id = self.kwargs.get('isolate_id')
        strain = get_object_or_404(Strain, id=isolate_id)
        fasta_url, gff_url, fasta_file_name, gff_file_name = construct_file_urls(strain)
        return {
            'species_name': strain.species.scientific_name,
            'isolate_name': strain.isolate_name,
            'assembly_name': strain.assembly_name,
            'assembly_accession': strain.assembly_accession,
            'fasta_file_name': fasta_file_name,
            'gff_file_name': gff_file_name,
            'fasta_url': fasta_url,
            'gff_url': gff_url,
        }
