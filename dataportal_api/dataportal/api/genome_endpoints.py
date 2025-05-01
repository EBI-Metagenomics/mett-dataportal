import logging
from typing import List, Optional, Dict

from ninja import Router, Query, Path
from ninja.errors import HttpError

from ..schemas import (
    StrainSuggestionSchema,
    GenomePaginationSchema,
    GenomeResponseSchema,
    GenePaginationSchema,
    EssentialityByContigSchema,
)
from ..services.essentiality_service import EssentialityService
from ..services.gene_service import GeneService
from ..services.genome_service import GenomeService
from ..utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    STRAIN_FIELD_ISOLATE_NAME, )
from ..utils.decorators import log_endpoint_access
from ..utils.errors import raise_http_error
from ..utils.exceptions import (
    ServiceError,
)

logger = logging.getLogger(__name__)

genome_service = GenomeService()
gene_service = GeneService()
essentiality_service = EssentialityService()

ROUTER_GENOME = "Genomes"
genome_router = Router(tags=[ROUTER_GENOME])


@genome_router.get(
    "/autocomplete",
    response=List[StrainSuggestionSchema],
    summary="Suggest isolates / genomes",
    description="Returns isolate suggestions based on the input query. You can optionally filter by species acronym. ",
    include_in_schema=False
)
@log_endpoint_access("genome_autocomplete_suggestions")
async def autocomplete_suggestions(
        request,
        query: str = Query(..., description="Search term for isolate/genome name autocomplete."),
        limit: int = Query(DEFAULT_PER_PAGE_CNT, description="Maximum number of suggestions to return."),
        species_acronym: Optional[str] = Query(None,
                                               description="Optional species acronym (BU or PV) to filter isolate suggestions.")
):
    return await genome_service.search_strains(query, limit, species_acronym)


# API Endpoint to search genomes by query string
@genome_router.get("/type-strains", response=List[GenomeResponseSchema],
                   summary="Get all type strains",
                   description=(
                           "Returns a list of genomes that are designated as type strains. "
                           "Type strains represent reference genomes for a given species and are essential "
                           "for comparative analysis and classification.")
                   )
async def get_type_strains(request):
    try:
        return await genome_service.get_type_strains()
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching type strains.")


@genome_router.get(
    "/search",
    response=GenomePaginationSchema,
    summary="Search genomes by query",
    description=(
            "Searches genomes using a free-text query string. "
            "Returns a paginated list of matching genome records. "
            "Supports optional sorting by 'isolate_name' or 'species'."
    )
)
async def search_genomes_by_string(
        request,
        query: str = Query(..., description="Search term to match against genome names or metadata."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page."),
        sortField: Optional[str] = Query(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by."),
        sortOrder: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
        isolates: Optional[List[str]] = Query(None, description="Filter by a list of isolate names."),
        species_acronym: Optional[str] = Query(None, description="Filter by species acronym."),
):
    sortField = sortField or STRAIN_FIELD_ISOLATE_NAME
    sortOrder = sortOrder or DEFAULT_SORT

    try:
        return await genome_service.search_genomes_by_string(
            query=query,
            page=page,
            per_page=per_page,
            sortField=sortField,
            sortOrder=sortOrder,
            isolates=isolates,
            species_acronym=species_acronym,
        )
    except ServiceError:
        raise HttpError(500, f"An error occurred while fetching genomes by query: {query}")


@genome_router.get(
    "/by-isolate-names",
    response=List[GenomeResponseSchema],
    summary="Get genomes by isolate names",
    description=(
            "Retrieves genome records for one or more isolate names. "
            "Accepts a comma-separated list of isolate names as input. "
            "Useful for batch lookups when isolate identifiers are known."
    )
)
async def get_genomes_by_isolate_names(
        request,
        isolates: str = Query(...,
                              description="Comma-separated list of isolate names (e.g., 'BU_61,BU_909,BU_ATCC8492').")
):
    try:
        if not isolates:
            raise_http_error(400, "Isolate names list is empty.")
        isolate_names_list = [id.strip() for id in isolates.split(",")]
        return await genome_service.get_genomes_by_isolate_names(isolate_names_list)
    except ServiceError as e:
        raise_http_error(500, f"An error occurred: {str(e)}")


# API Endpoint to retrieve all genomes
@genome_router.get("/", response=GenomePaginationSchema,
                   summary="Get all genomes",
                   description="Retrieves a paginated list of all genomes available in the system. "
                               "Supports optional sorting by 'isolate_name' or 'species'. "
                   )
async def get_all_genomes(
        request,
        page: int = Query(1, description="Page number"),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of items per page"),
        sortField: Optional[str] = Query(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort by"),
        sortOrder: Optional[str] = Query(DEFAULT_SORT, description="Sort order: asc or desc"),
):
    try:
        return await genome_service.get_genomes(page, per_page, sortField, sortOrder)
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching genomes.")
    except Exception:
        raise_http_error(500, "An error occurred while fetching genomes.")


# API Endpoint to retrieve genes filtered by a single genome ID
@genome_router.get(
    "/{isolate_name}/genes",
    response=GenePaginationSchema,
    summary="Get genes by genome isolate",
    description=(
            "Retrieves a paginated list of genes associated with a specific genome isolate. "
            "Supports optional sorting by 'isolate_name', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'. "
            "Useful for viewing all genes within a selected genome."
    )
)
async def get_genes_by_genome(
        request,
        isolate_name: str = Path(..., description="Unique isolate name identifying the genome."),
        filter: Optional[str] = Query(None,
                                      description="Additional gene filter, e.g., 'pfam:pf07715;interpro:ipr012910'."),
        filter_operators: Optional[str] = Query(None,
                                                description="Logical operator (AND/OR) per facet, e.g., 'pfam:AND;interpro:OR'"),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."),
        sort_field: Optional[str] = Query(None, description="Field to sort results by."),
        sort_order: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await gene_service.get_genes_by_genome(
            isolate_name, filter, filter_operators, page, per_page, sort_field, sort_order
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(
            500, f"Failed to fetch the genes information for genome_id - {isolate_name}"
        )


# API endpoint to retrieve essentiality data from cache for a specific strain ID.
@genome_router.get(
    "/{isolate_name}/essentiality/{ref_name}",
    response=Dict[str, EssentialityByContigSchema],
    summary="Get essentiality data by genome and contig",
    description=(
            "Retrieves cached essentiality data for a given genome isolate and reference name (e.g. contig_1). "
            "Returns gene essentiality information grouped by contig. "
            "This data is typically precomputed and used to visualize gene essentiality in genome browsers or analysis tools."
    )
)
async def get_essentiality_data_by_contig(
        request,
        isolate_name: str = Path(..., description="Isolate name identifying the genome."),
        ref_name: str = Path(...,
                             description="Reference sequence (e.g. contig_1) name to retrieve essentiality data for.")
):
    try:
        essentiality_data = await essentiality_service.get_essentiality_data_by_strain_and_ref(
            isolate_name, ref_name
        )
        if not essentiality_data:
            return {}

        return essentiality_data
    except Exception as e:
        logger.error(
            f"Error retrieving essentiality data for isolate_name={isolate_name}, ref_name={ref_name}: {e}",
            exc_info=True,
        )
        raise HttpError(
            500,
            f"Failed to retrieve essentiality data for strain {isolate_name} and refName {ref_name}.",
        )
