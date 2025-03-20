import logging
from typing import List, Optional, Dict

from django.http import JsonResponse
from ninja import NinjaAPI, Router
from ninja.errors import HttpError

from .models import EssentialityTag
from .schemas import (
    StrainSuggestionSchema,
    SpeciesSchema,
    GenomePaginationSchema,
    GenomeResponseSchema,
    GeneAutocompleteResponseSchema,
    GenePaginationSchema,
    GeneResponseSchema,
    EssentialityTagSchema,
    EssentialityByContigSchema,
)
from .services.gene_service import GeneService
from .services.genome_service import GenomeService
from .services.species_service import SpeciesService
from .utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    ROUTER_GENOME,
    ROUTER_GENE,
    ROUTER_SPECIES,
    STRAIN_FIELD_ISOLATE_NAME, URL_PREFIX_GENES, URL_PREFIX_GENOMES, URL_PREFIX_SPECIES,
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
species_service = SpeciesService()

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="API for genome browser and contextual information.",
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
@genome_router.get("/autocomplete", response=List[StrainSuggestionSchema])
@log_endpoint_access("genome_autocomplete_suggestions")
async def autocomplete_suggestions(
        request,
        query: str,
        limit: int = DEFAULT_PER_PAGE_CNT,
        species_acronym: Optional[str] = None,
):
    return await genome_service.search_strains(query, limit, species_acronym)


# API Endpoint to retrieve all species
@species_router.get("/", response=List[SpeciesSchema])
async def get_all_species(request):
    try:
        species = await species_service.get_all_species()
        return species
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching species.")
    except Exception:
        raise_http_error(500, "An error occurred while fetching species.")


# API Endpoint to retrieve all genomes
@genome_router.get("/", response=GenomePaginationSchema)
async def get_all_genomes(
        request,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sortField: Optional[str] = STRAIN_FIELD_ISOLATE_NAME,
        sortOrder: Optional[str] = DEFAULT_SORT,
):
    try:
        return await genome_service.get_genomes(page, per_page, sortField, sortOrder)
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching genomes.")
    except Exception:
        raise_http_error(500, "An error occurred while fetching genomes.")


# API Endpoint to search genomes by query string
@genome_router.get("/type-strains", response=List[GenomeResponseSchema])
async def get_type_strains(request):
    try:
        return await genome_service.get_type_strains()
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching type strains.")


@genome_router.get("/search", response=GenomePaginationSchema)
async def search_genomes_by_string(
        request,
        query: str,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sortField: Optional[str] = STRAIN_FIELD_ISOLATE_NAME,
        sortOrder: Optional[str] = DEFAULT_SORT,
):
    sortField = sortField or STRAIN_FIELD_ISOLATE_NAME
    sortOrder = sortOrder or DEFAULT_SORT
    try:
        return await genome_service.search_genomes_by_string(
            query, page, per_page, sortField, sortOrder
        )
    except ServiceError:
        raise HttpError(
            500, f"An error occurred while fetching genomes by query: {query}"
        )


@genome_router.get("/by-isolate-names", response=List[GenomeResponseSchema])
async def get_genomes_by_isolate_names(request, isolates: str):
    try:
        if not isolates:
            raise_http_error(400, "Isolate names list is empty.")
        isolate_names_list = [id.strip() for id in isolates.split(",")]
        return await genome_service.get_genomes_by_isolate_names(isolate_names_list)
    except ServiceError as e:
        raise_http_error(500, f"An error occurred: {str(e)}")


# API Endpoint to retrieve genomes filtered by species_acronym
@species_router.get("/{species_acronym}/genomes", response=GenomePaginationSchema)
async def get_genomes_by_species(
        request,
        species_acronym: str,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sortField: Optional[str] = STRAIN_FIELD_ISOLATE_NAME,
        sortOrder: Optional[str] = DEFAULT_SORT,
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
@species_router.get("/{species_acronym}/genomes/search", response=GenomePaginationSchema)
async def search_genomes_by_species_and_string(
        request,
        species_acronym: str,
        query: str,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sortField: Optional[str] = STRAIN_FIELD_ISOLATE_NAME,
        sortOrder: Optional[str] = DEFAULT_SORT,
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


@gene_router.get("/autocomplete", response=List[GeneAutocompleteResponseSchema])
async def gene_autocomplete_suggestions(
        request,
        query: str,
        filter: Optional[str] = None,
        limit: int = DEFAULT_PER_PAGE_CNT,
        species_acronym: Optional[str] = None,
        isolates: Optional[str] = None,
):
    isolate_list = (
        [gid.strip() for gid in isolates.split(",") if gid.strip()]
        if isolates else None
    )

    return await gene_service.autocomplete_gene_suggestions(
        query, filter, limit, species_acronym, isolate_list
    )


# API Endpoint to search genes by query string
@gene_router.get("/search", response=GenePaginationSchema)
async def search_genes_by_string(
        request,
        query: str,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = DEFAULT_SORT,
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


@gene_router.get("/faceted-search")
async def get_faceted_search(request, species_acronym: Optional[str] = None,
                             essentiality: Optional[str] = None,
                             isolates: Optional[List[str]] = None,
                             cog_funcats: Optional[str] = None,
                             kegg: Optional[str] = None,
                             go_term: Optional[str] = None,
                             pfam: Optional[str] = None,
                             interpro: Optional[str] = None,
                             limit: int = DEFAULT_PER_PAGE_CNT):
    return await gene_service.get_faceted_search(species_acronym, essentiality, isolates,
                                                 cog_funcats, kegg, go_term, pfam, interpro,
                                                 limit)


# API Endpoint to retrieve gene by locus tag
@gene_router.get("/{locus_tag}", response=GeneResponseSchema)
async def get_gene_by_locus_tag(request, locus_tag: str):
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
@gene_router.get("/", response=GenePaginationSchema)
async def get_all_genes(
        request,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = DEFAULT_SORT,
):
    try:
        return await gene_service.get_all_genes(page, per_page, sort_field, sort_order)
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, "Failed to fetch the genes information")


# API Endpoint to retrieve genes filtered by a single genome ID
@genome_router.get("/{isolate_name}/genes", response=GenePaginationSchema)
async def get_genes_by_genome(
        request,
        isolate_name: str,
        filter: Optional[str] = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = DEFAULT_SORT,
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


# API Endpoint to search genes by genome ID and gene string
@genome_router.get("/{isolate_name}/genes/search", response=GenePaginationSchema)
async def search_genes_by_genome_and_string(
        request,
        isolate_name: str,
        query: str,
        filter: Optional[str] = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = DEFAULT_SORT,
):
    try:
        return await gene_service.search_genes(
            query, isolate_name, filter, page, per_page, sort_field, sort_order
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(
            500,
            f"Failed to fetch the genes information for genome_id - {isolate_name} and query - {query}",
        )
    except Exception as e:
        raise_http_error(500, f"Failed to fetch the genes information: {str(e)}")


# API Endpoint to search genes across multiple genome IDs using a gene string
@gene_router.get("/search/advanced", response=GenePaginationSchema)
async def search_genes_by_multiple_genomes_and_species_and_string(
        request,
        isolates: str = "",
        species_acronym: Optional[str] = None,
        query: str = "",
        filter: Optional[str] = None,
        page: int = 1,
        per_page: int = DEFAULT_PER_PAGE_CNT,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = DEFAULT_SORT,
):
    try:
        logger.debug(
            f"Request received with params: query={query}, filter={filter}, page={page}, per_page={per_page}, sortField={sort_field}, sortOrder={sort_order}"
        )
        if not isolates:
            raise_http_error(400, "Isolate names list is empty.")
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


@gene_router.get("/essentiality/tags", response=list[EssentialityTagSchema])
def list_essentiality_tags(request):
    tags = EssentialityTag.objects.all()
    return tags


# API endpoint to retrieve essentiality data from cache for a specific strain ID.
@genome_router.get("/{isolate_name}/essentiality/{ref_name}", response=Dict[str, EssentialityByContigSchema])
async def get_essentiality_data_by_contig(request, isolate_name: str, ref_name: str):
    try:
        essentiality_data = await gene_service.get_essentiality_data_by_strain_and_ref(
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
