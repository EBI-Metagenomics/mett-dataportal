from typing import List, Optional

from ninja import NinjaAPI, Router
from pydantic import BaseModel

from .models import Species

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="The API is developed to support a genome browser for genomic information, "
                "complemented by contextual information. This page will also allow users to "
                "browse non-genomic information, such as experimental results.",
    urls_namespace="api",
    csrf=True,
)

search_router = Router()


class SearchResultSchema(BaseModel):
    species: str
    common_name: Optional[str]
    isolate_name: str
    strain_name: Optional[str]
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


@search_router.get('/results/', response=PaginationSchema)
async def search_results(request, query: Optional[str] = None, isolate_name: Optional[str] = None,
                         sortField: Optional[str] = '', sortOrder: Optional[str] = '', page: int = 1,
                         per_page: int = 10):
    search_term = isolate_name or query
    print(f'sort_field: {sortField}, sort_order: {sortOrder}')
    if search_term:
        try:
            full_results = await Species.objects.search_species(search_term, sortField, sortOrder)

            total_results = len(full_results)
            print(f'Total results found in search_results: {total_results}')

            start = (page - 1) * per_page
            end = start + per_page
            print(f'Paginating results: start={start}, end={end}')

            page_results = full_results[start:end]

            has_previous = page > 1
            has_next = end < total_results

            return PaginationSchema(
                results=page_results,
                page_number=page,
                num_pages=(total_results + per_page - 1) // per_page,  # Calculate total pages
                has_previous=has_previous,
                has_next=has_next,
                total_results=total_results,
            )

        except Exception as e:
            from ninja.errors import HttpError
            print(f'Error occurred: {e}')
            raise HttpError(500, str(e))

    return PaginationSchema(
        results=[],
        page_number=1,
        num_pages=1,
        has_previous=False,
        has_next=False,
        total_results=0,
    )


@search_router.get('/autocomplete/', response=List[str])
async def autocomplete_suggestions(request, query: str, limit: int = 10):
    try:
        suggestions = await Species.objects.autocomplete_suggestions(query, limit)
        return suggestions
    except Exception as e:
        return {'error': str(e)}, 500


api.add_router("/search", search_router)

__all__ = ["api"]
