import logging
from typing import List, Optional

from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Router
from ninja.errors import HttpError
from pydantic import BaseModel

from .models import Strain, Gene
from .services import SearchService
from .utils import construct_file_urls

logger = logging.getLogger(__name__)

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="API for genome browser and contextual information.",
    urls_namespace="api",
    csrf=True,
)

search_router = Router()


class SearchResultSchema(BaseModel):
    species: str
    id: int
    common_name: Optional[str]
    isolate_name: str
    assembly_name: Optional[str]
    assembly_accession: Optional[str]
    fasta_file: str
    gff_file: str


class PaginationSchema(BaseModel):
    results: List[SearchResultSchema]
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int


@search_router.get('/autocomplete/', response=List[str])
async def autocomplete_suggestions(request, query: str, limit: int = 10):
    try:
        suggestions = await SearchService.search_strains(query, limit)
        return suggestions
    except Exception as e:
        raise HttpError(500, f"Error occurred: {str(e)}")


@search_router.get('/strains/{strain_id}/genes/search/', response=List[dict])
async def search_genes_in_strain(request, strain_id: int, q: str):
    try:
        strain = await sync_to_async(lambda: get_object_or_404(Strain, id=strain_id))()

        gene_query = await sync_to_async(lambda: list(
            Gene.objects.filter(
                strain=strain,
                gene_name__icontains=q
            )[:10]
        ))()

        return [{"gene_name": gene.gene_name, "description": gene.description} for gene in gene_query]

    except HttpError as e:
        raise e
    except Exception as e:
        logger.error(f"Error in search_genes_in_strain: {e}")
        raise HttpError(500, f"Error occurred: {str(e)}")


@search_router.get('/genes/search/', response=List[dict])
def search_genes_globally(request, q: str):
    if not q.strip():
        raise HttpError(400, "Query parameter 'q' cannot be empty")

    try:
        genes = SearchService.search_genes_globally(q)
        return [{"gene_name": g.gene_name, "strain": g.strain.isolate_name, "assembly": g.strain.assembly_name,
                 "description": g.description} for g in genes]
    except Exception as e:
        return {'error': str(e)}, 500


@search_router.get('/strains-genes/search/', response=List[dict])
def search_genes_in_strains(request, strain_q: str, gene_q: str):
    try:
        genes = SearchService.search_genes_in_strains(strain_q, gene_q)

        if not genes:
            raise HttpError(404, f"No genes found matching '{gene_q}' in strains matching '{strain_q}'")

        return [{"gene_name": g.gene_name, "strain": g.strain.isolate_name, "assembly": g.strain.assembly_name,
                 "description": g.description} for g in genes]

    except HttpError as e:
        raise e
    except Exception as e:
        return {'error': str(e)}, 500


@search_router.get('/results/', response=PaginationSchema)
async def search_results(request, query: Optional[str] = None, isolate_name: Optional[str] = None,
                         strain_id: Optional[int] = None, gene_id: Optional[int] = None,
                         sortField: Optional[str] = '', sortOrder: Optional[str] = '',
                         page: int = 1, per_page: int = 10):
    try:
        logger.debug(f"query: {query}, isolate_name: {isolate_name}, strain_id: {strain_id}, gene_id: {gene_id}")

        if gene_id:
            # Search by gene_id if provided
            full_results = await SearchService.get_search_results_by_gene(gene_id=gene_id)
        elif strain_id:
            # Search by strain_id if provided
            full_results = await SearchService.get_search_results(strain_id=strain_id)
        else:
            search_term = isolate_name or query
            logger.debug(f"Search term: {search_term}")
            full_results = await SearchService.get_search_results(query=search_term)

        if not full_results:
            logger.debug("No results found")
            return PaginationSchema(
                results=[],
                page_number=1,
                num_pages=0,
                has_previous=False,
                has_next=False,
                total_results=0,
            )

        results = await sync_to_async(lambda: [
            {
                "species": strain.species.scientific_name,
                "id": strain.id,
                "common_name": strain.species.common_name if strain.species.common_name else None,
                "isolate_name": strain.isolate_name,
                "assembly_name": strain.assembly_name,
                "assembly_accession": strain.assembly_accession,
                "fasta_file": strain.fasta_file,
                "gff_file": strain.gff_file,
            }
            for strain in full_results
        ])()

        total_results = len(results)
        logger.debug(f"Total results before pagination: {total_results}")

        start = (page - 1) * per_page
        end = start + per_page
        page_results = results[start:end]

        return PaginationSchema(
            results=page_results,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=end < total_results,
            total_results=total_results,
        )
    except Exception as e:
        logger.error(f"Error in search_results: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


class JBrowseResponseSchema(BaseModel):
    species: str
    isolate_name: str
    fasta_url: str
    gff_url: str
    fasta_file_name: str
    gff_file_name: str


@search_router.get('/jbrowse/{isolate_id}', response=JBrowseResponseSchema)
def get_jbrowse_data(request, isolate_id: int):
    strain = get_object_or_404(Strain, id=isolate_id)
    fasta_url, gff_url, fasta_file_name, gff_file_name = construct_file_urls(strain)

    return JBrowseResponseSchema(
        species=strain.species.scientific_name,
        isolate_name=strain.isolate_name,
        fasta_url=fasta_url,
        gff_url=gff_url,
        fasta_file_name=fasta_file_name,
        gff_file_name=gff_file_name
    )


api.add_router("/search", search_router)
