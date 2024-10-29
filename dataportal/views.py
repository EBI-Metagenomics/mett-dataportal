import logging

from asgiref.sync import sync_to_async
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from .models import Strain
from .services.genome_service import GenomeService
from .utils import construct_file_urls

logger = logging.getLogger(__name__)
genome_service = GenomeService()


class SearchGenomesView(View):
    async def get(self, request, *args, **kwargs):
        query = request.GET.get("query", "").strip()
        isolate_name = request.GET.get("isolate-name", "").strip()
        gene_id = request.GET.get("gene_id", None)
        search_term = isolate_name or query
        results = []
        paginator = None

        logger.debug(f"Search term: {search_term}, gene_id: {gene_id}")

        try:
            if gene_id:
                logger.debug(f"Searching by gene_id: {gene_id}")
                full_results = await genome_service.search_genome_by_gene(
                    gene_id=gene_id
                )
            elif search_term:
                logger.debug("Search term exists, proceeding with search")
                full_results = await genome_service.search_genomes(query=search_term)

            if not full_results:
                logger.debug(f"No results found for search term: {search_term}")
                return JsonResponse(
                    {
                        "results": [],
                        "page_number": 1,
                        "num_pages": 0,
                        "has_previous": False,
                        "has_next": False,
                    }
                )

            paginator = await sync_to_async(Paginator)(full_results, 10)
            page_obj = await sync_to_async(paginator.page)(
                int(request.GET.get("page", 1))
            )
            results = await sync_to_async(lambda: list(page_obj.object_list))()

            return JsonResponse(
                {
                    "results": results,
                    "page_number": page_obj.number if page_obj else 1,
                    "num_pages": paginator.num_pages if paginator else 1,
                    "has_previous": page_obj.has_previous() if page_obj else False,
                    "has_next": page_obj.has_next() if page_obj else False,
                }
            )

        except Exception as e:
            logger.error(f"Error in search: {e}")
            return JsonResponse({"error": str(e)}, status=500)


class Autocomplete(View):
    async def get(self, request, *args, **kwargs):
        query = request.GET.get("query", "").strip()
        species_id = request.GET.get("species_id")  # Get species_id if provided
        if query:
            suggestions = await genome_service.search_strains(
                query, species_id=species_id
            )
            return JsonResponse({"suggestions": suggestions})
        return JsonResponse({"suggestions": []})


class JBrowseView(View):
    def get_context_data(self, **kwargs):
        isolate_id = self.kwargs.get("isolate_id")
        strain = get_object_or_404(Strain, id=isolate_id)
        fasta_url, gff_url, fasta_file_name, gff_file_name = construct_file_urls(strain)
        return {
            "species_name": strain.species.scientific_name,
            "isolate_name": strain.isolate_name,
            "assembly_name": strain.assembly_name,
            "assembly_accession": strain.assembly_accession,
            "fasta_file_name": fasta_file_name,
            "gff_file_name": gff_file_name,
            "fasta_url": fasta_url,
            "gff_url": gff_url,
        }
