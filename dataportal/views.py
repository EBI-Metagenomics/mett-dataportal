import logging

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.views.generic import (
    TemplateView,
)

from .models import SpeciesData
from dataportal.services.search import search_species_data

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "dataportal/pages/index.html"


from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import View
import logging

logger = logging.getLogger(__name__)


class SearchResultsView(View):
    async def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '').strip()
        isolate_name = request.GET.get('isolate-name', '').strip()
        search_term = isolate_name or query

        logger.debug(f"Search term: {search_term}")
        results = []
        paginator = None

        if search_term:
            try:
                sort_field = request.GET.get('sortField', '')
                sort_order = request.GET.get('sortOrder', '')
                page_number = int(request.GET.get('page', 1))

                total_results, page_results = await search_species_data(search_term, sort_field, sort_order,
                                                                        page=page_number)
                paginator = Paginator(range(total_results), 10)  # 10 results per page
                page_obj = paginator.get_page(page_number)
                results = page_results

            except Exception as e:
                logger.error(f"Error executing async query: {e}")
                return JsonResponse({
                    'error': str(e),
                }, status=500)

            return JsonResponse({
                'results': results,
                'page_number': page_obj.number if page_obj else 1,
                'num_pages': paginator.num_pages if paginator else 1,
                'has_previous': page_obj.has_previous() if page_obj else False,
                'has_next': page_obj.has_next() if page_obj else False,
            })

        # Only return an empty JSON response if no search term is provided
        return JsonResponse({
            'results': [],
            'page_number': 1,
            'num_pages': 0,
            'has_previous': False,
            'has_next': False,
        })


class Autocomplete(View):
    async def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        suggestions = []
        if query:
            # Use sync_to_async to run the query in a thread-safe manner
            results = await sync_to_async(list)(SpeciesData.objects.filter(
                Q(species__icontains=query) |
                Q(isolate_name__icontains=query) |
                Q(assembly_name__icontains=query)
            ).values('species', 'isolate_name', 'assembly_name')[:10])

            # Create a list of formatted suggestion strings
            suggestions = [
                f"{result['species']} - {result['isolate_name']} ({result['assembly_name']})"
                for result in results
            ]
        return JsonResponse({'suggestions': suggestions})
