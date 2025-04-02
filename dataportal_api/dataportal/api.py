import logging
from typing import List, Optional, Dict

from django.http import JsonResponse
from ninja import NinjaAPI, Router, Query, Path
from ninja.errors import HttpError

from .schemas import (
    StrainSuggestionSchema,
    SpeciesSchema,
    GenomePaginationSchema,
    GenomeResponseSchema,
    GeneAutocompleteResponseSchema,
    GenePaginationSchema,
    GeneResponseSchema,
    EssentialityByContigSchema,
)
from .services.essentiality_service import EssentialityService
from .services.gene_service import GeneService
from .services.genome_service import GenomeService
from .services.species_service import SpeciesService
from .utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    ROUTER_GENOME,
    ROUTER_GENE,
    ROUTER_SPECIES,
    STRAIN_FIELD_ISOLATE_NAME, URL_PREFIX_GENES, URL_PREFIX_GENOMES, URL_PREFIX_SPECIES, DEFAULT_FACET_LIMIT,
)
from .utils.decorators import log_endpoint_access
from .utils.errors import raise_http_error
from .utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
    InvalidGenomeIdError,
)

logger = logging.getLogger(__name__)

genome_service = GenomeService()
gene_service = GeneService()
essentiality_service = EssentialityService()
species_service = SpeciesService()

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="ME TT DataPortal Data Portal APIs to fetch Gut Microbes Genomes / Genes information.",
    urls_namespace="api",
    csrf=True,
    docs_url="/docs",
)

genome_router = Router(tags=[ROUTER_GENOME])
gene_router = Router(tags=[ROUTER_GENE])
species_router = Router(tags=[ROUTER_SPECIES])


def custom_error_handler(request, exc):
    if isinstance(exc, HttpError):
        return JsonResponse({"error": str(exc)}, status=exc.status_code)
    return JsonResponse({"error": "Internal server error"}, status=500)


# Map the router to the class methods
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


# API Endpoint to retrieve all species
@species_router.get("/", response=List[SpeciesSchema],
                    summary="Get all species",
                    description="Get all available species"
                    )
async def get_all_species(request):
    try:
        species = await species_service.get_all_species()
        return species
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching species.")
    except Exception:
        raise_http_error(500, "An error occurred while fetching species.")


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
        "Supports optional sorting by isolate_name or 'species'."
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


# API Endpoint to retrieve genomes filtered by species_acronym
@species_router.get(
    "/{species_acronym}/genomes",
    response=GenomePaginationSchema,
    summary="Get genomes by species",
    description=(
            "Retrieves a paginated list of genomes that belong to the specified species. "
            "Supports optional sorting by 'isolate_name' or 'species'. "
            "Useful for browsing all genomes under a given species acronym."
    )
)
async def get_genomes_by_species(
        request,
        species_acronym: str = Path(..., description="Acronym for the species (BU or PV)."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page."),
        sortField: Optional[str] = Query(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by."),
        sortOrder: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await genome_service.get_genomes_by_species(
            species_acronym, page, per_page, sortField, sortOrder
        )
    except ServiceError:
        raise HttpError(
            500, f"An error occurred while fetching genomes by species: {species_acronym}"
        )


# API Endpoint to search genomes by species_acronym and query string
@species_router.get(
    "/{species_acronym}/genomes/search",
    response=GenomePaginationSchema,
    summary="Search genomes by species and query string",
    description=(
            "Performs a search for genomes within a specific species using a free-text query. "
            "Returns a paginated list of matching genome records. "
            "Useful for narrowing down results within a species context, with optional sorting by 'isolate_name' or 'species'."
    )
)
async def search_genomes_by_species_and_string(
        request,
        species_acronym: str = Path(..., description="Acronym for the species (BU or PV)."),
        query: str = Query(..., description="Search term to match against genome names or metadata."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genomes to return per page."),
        sortField: Optional[str] = Query(STRAIN_FIELD_ISOLATE_NAME, description="Field to sort results by."),
        sortOrder: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await genome_service.search_genomes_by_species_and_string(
            species_acronym, query, page, per_page, sortField, sortOrder
        )
    except ServiceError:
        raise HttpError(
            500,
            f"An error occurred while fetching genomes by species: {species_acronym} and query: {query}",
        )


@gene_router.get(
    "/autocomplete",
    response=List[GeneAutocompleteResponseSchema],
    summary="Autocomplete gene names",
    description=(
            "Provides gene name suggestions based on a query string. "
            "Supports optional filters such as essentiality, interpro, pfam and more. "
            "Allows to limit suggestions to specific isolates. Useful for building search dropdowns or gene lookup helpers."
    ),
    include_in_schema=False
)
async def gene_autocomplete_suggestions(
        request,
        query: str = Query(..., description="Free-text input to search for gene metadata."),
        filter: Optional[str] = Query(None,
                                      description="Optional gene filter, e.g., 'essentiality:essential_liquid;interpro:IPR035952'."),
        limit: int = Query(DEFAULT_PER_PAGE_CNT, description="Maximum number of suggestions to return."),
        species_acronym: Optional[str] = Query(None, description="Filter results by 'species_acronym'."),
        isolates: Optional[str] = Query(None, description="Comma-separated isolate names to restrict the search scope.")
):
    isolate_list = (
        [gid.strip() for gid in isolates.split(",") if gid.strip()]
        if isolates else None
    )

    return await gene_service.autocomplete_gene_suggestions(
        query, filter, limit, species_acronym, isolate_list
    )


# API Endpoint to search genes by query string
@gene_router.get(
    "/search",
    response=GenePaginationSchema,
    summary="Search genes by query string",
    description=(
            "Searches for genes using a free-text query. "
            "Returns a paginated list of genes that match the input string across any genome or isolate. "
            "Supports optional sorting by 'strain', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'."
    )
)
async def search_genes_by_string(
        request,
        query: str = Query(..., description="Search term to match against gene names or locus tags."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."),
        sort_field: Optional[str] = Query(None, description="Field to sort results by."),
        sort_order: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await gene_service.search_genes(
            query, "", "", page, per_page, sort_field, sort_order
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(
            500,
            f"Failed to fetch the genes information for gene query - {query}",
        )


@gene_router.get(
    "/faceted-search",
    summary="Perform faceted search on genes",
    description=(
            "Returns filtered gene search results based on multiple metadata facets. "
            "Supports filtering by species, essentiality, isolates, and annotation sources like COG, KEGG, GO terms, "
            "Pfam, and InterPro. Useful for narrowing down genes based on specific functional or experimental criteria."
    ),
    include_in_schema=False
)
async def get_faceted_search(
        request,
        species_acronym: Optional[str] = Query(None, description="Species acronym to filter genes by (BU or PV)."),
        essentiality: Optional[str] = Query(None,
                                            description="Essentiality status to filter genes (e.g., 'essential')."),
        isolates: Optional[str] = Query("", description="Comma-separated list of isolate names."),
        cog_ids: Optional[str] = Query(None, description="Comma-separated list of COG IDs to filter by."),
        kegg: Optional[str] = Query(None, description="KEGG pathway or gene ID to filter by."),
        go_term: Optional[str] = Query(None, description="GO term ID or label to filter by."),
        pfam: Optional[str] = Query(None, description="Pfam domain ID to filter by."),
        interpro: Optional[str] = Query(None, description="InterPro ID to filter by."),
        limit: int = Query(DEFAULT_FACET_LIMIT, description="Maximum number of genes to return.")
):
    isolate_names_list = [id.strip() for id in isolates.split(",")] if isolates else []
    logger.info(f"Isolates received: {isolate_names_list} (type: {type(isolate_names_list)})")
    return await gene_service.get_faceted_search(species_acronym, isolate_names_list, essentiality,
                                                 cog_ids, kegg, go_term, pfam, interpro,
                                                 limit)


# API Endpoint to retrieve gene by locus tag
@gene_router.get(
    "/{locus_tag}",
    response=GeneResponseSchema,
    summary="Get gene by locus tag",
    description=(
            "Retrieves detailed information for a specific gene using its unique locus tag. "
            "Returns metadata and functional annotation associated with the gene. "
            "This endpoint is useful for direct lookups when the locus tag is already known."
    )
)
async def get_gene_by_locus_tag(
        request,
        locus_tag: str = Path(..., description="Unique locus tag identifier for the gene (e.g., 'ABC_123').")
):
    try:
        return await gene_service.get_gene_by_locus_tag(locus_tag)
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {e.locus_tag}")
        raise HttpError(404, str(e))
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(
            500, f"Failed to fetch the gene information for locus_tag - {locus_tag}"
        )


# API Endpoint to retrieve all genes
@gene_router.get(
    "/",
    response=GenePaginationSchema,
    summary="Get all genes",
    description=(
            "Retrieves a paginated list of all genes across all available genomes. "
            "Supports optional sorting by 'strain', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'. "
            "Useful for browsing the full gene catalog without applying filters."
    )
)
async def get_all_genes(
        request,
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."),
        sort_field: Optional[str] = Query(None, description="Field to sort results by."),
        sort_order: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await gene_service.get_all_genes(page, per_page, sort_field, sort_order)
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, "Failed to fetch the genes information")


# API Endpoint to retrieve genes filtered by a single genome ID
@genome_router.get(
    "/{isolate_name}/genes",
    response=GenePaginationSchema,
    summary="Get genes by genome isolate",
    description=(
            "Retrieves a paginated list of genes associated with a specific genome isolate. "
            "Supports optional sorting by 'strain', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'. "
            "Useful for viewing all genes within a selected genome."
    )
)
async def get_genes_by_genome(
        request,
        isolate_name: str = Path(..., description="Unique isolate name identifying the genome."),
        filter: Optional[str] = Query(None, description="Optional filter string to narrow gene results."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."),
        sort_field: Optional[str] = Query(None, description="Field to sort results by."),
        sort_order: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        return await gene_service.get_genes_by_genome(
            isolate_name, filter, page, per_page, sort_field, sort_order
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(
            500, f"Failed to fetch the genes information for genome_id - {isolate_name}"
        )


# API Endpoint to search genes across multiple genome IDs using a gene string
@gene_router.get(
    "/search/advanced",
    response=GenePaginationSchema,
    summary="Advanced gene search across genomes and species",
    description=(
            "Performs an advanced gene search using a free-text query across multiple genome isolates "
            "and/or a specific species. Supports filtering by species, essentiality, isolates, "
            "and annotation sources like COG, KEGG, GO terms, Pfam, and InterPro. "
            "Supports optional sorting by 'strain', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'."
            "Useful for cross-genome comparisons or focused searches within a species context."
    )
)
async def search_genes_by_multiple_genomes_and_species_and_string(
        request,
        isolates: str = Query("", description="Comma-separated list of isolate names to restrict the search scope."),
        species_acronym: Optional[str] = Query(None, description="Optional species acronym to filter by."),
        query: str = Query("", description="Free-text search string to match against gene names or annotations."),
        filter: Optional[str] = Query(None, description="Additional gene filter, e.g., 'essential'."),
        page: int = Query(1, description="Page number to retrieve."),
        per_page: int = Query(DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."),
        sort_field: Optional[str] = Query(None, description="Field to sort results by."),
        sort_order: Optional[str] = Query(DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."),
):
    try:
        logger.debug(
            f"Request received with params: query={query}, filter={filter}, page={page}, per_page={per_page}, sortField={sort_field}, sortOrder={sort_order}"
        )
        # if not isolates:
        #     raise_http_error(400, "Isolate names list is empty.")
        return await gene_service.get_genes_by_multiple_genomes_and_string(
            isolates,
            species_acronym,
            query,
            filter,
            page,
            per_page,
            sort_field,
            sort_order,
        )
    except InvalidGenomeIdError:
        raise_http_error(400, f"Invalid genome ID provided: {isolates}")
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_http_error(500, f"Failed to fetch the genes information: {str(e)}")


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


# Register routers with the main API
api.add_router(URL_PREFIX_SPECIES, species_router)
api.add_router(URL_PREFIX_GENOMES, genome_router)
api.add_router(URL_PREFIX_GENES, gene_router)
api.add_exception_handler(Exception, custom_error_handler)
