import logging

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import (
    TemplateView,
)

from .models import Species, Strain

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "dataportal/pages/index.html"


class SearchResultsView(View):
    async def get(self, request, *args, **kwargs):
        logger.debug('SearchResultsView called')
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
                per_page = 10  # Number of results per page

                full_results = await Species.objects.search_species(search_term, sort_field, sort_order)
                # total_results = len(full_results)

                # Paginate the results
                paginator = Paginator(full_results, per_page)
                page_obj = paginator.get_page(page_number)
                results = page_obj.object_list

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

        return JsonResponse({
            'results': [],
            'page_number': 1,
            'num_pages': 0,
            'has_previous': False,
            'has_next': False,
        })


class Autocomplete(View):
    async def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '').strip()
        if query:
            suggestions = await Species.objects.autocomplete_suggestions(query)
            return JsonResponse({'suggestions': suggestions})
        return JsonResponse({'suggestions': []})

class JBrowseView(TemplateView):
    template_name = "dataportal/pages/jbrowse_viewer.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        isolate_id = self.kwargs.get('isolate_id')
        strain = get_object_or_404(Strain, id=isolate_id)

        context.update({
            'species': strain.species.scientific_name,
            'isolate_name': strain.isolate_name,
            'fasta_url': strain.fasta_file,
            'gff_url': strain.gff_file,
        })

        return context