import logging
from typing import List, Optional

from ninja import NinjaAPI, Router
from ninja.errors import HttpError

from .models import Strain
from .schemas import (
    StrainSuggestionSchema,
    SpeciesSchema,
    GenomePaginationSchema,
    TypeStrainSchema,
    SearchGenomeSchema,
    GeneAutocompleteResponseSchema,
    GenePaginationSchema,
    GeneResponseSchema,
)
from .services.gene_service import GeneService
from .services.genome_service import GenomeService
from .services.species_service import SpeciesService

logger = logging.getLogger(__name__)

genome_service = GenomeService()
gene_service = GeneService()
species_service = SpeciesService()

api = NinjaAPI(
    title="ME TT DataPortal Data Portal API",
    description="API for genome browser and contextual information.",
    urls_namespace="api",
    csrf=True,
)

genome_router = Router(tags=["Genomes"])
gene_router = Router(tags=["Genes"])
species_router = Router(tags=["Species"])
jbrowse_router = Router(tags=["JBrowse Viewer"])


# Map the router to the class methods
@genome_router.get("/autocomplete", response=List[StrainSuggestionSchema])
async def autocomplete_suggestions(
    request, query: str, limit: int = 10, species_id: Optional[int] = None
):
    return await genome_service.search_strains(query, limit, species_id)


# API Endpoint to retrieve all species
@species_router.get("/", response=List[SpeciesSchema])
async def get_all_species(request):
    try:
        species = await species_service.get_all_species()
        return species
    except Exception as e:
        logger.error(f"Error fetching species: {e}")
        raise HttpError(500, "An error occurred while fetching species.")


# API Endpoint to retrieve all genomes
@genome_router.get("/", response=GenomePaginationSchema)
async def get_all_genomes(
    request,
    page: int = 1,
    per_page: int = 10,
    sortField: Optional[str] = "isolate_name",
    sortOrder: Optional[str] = "asc",
):
    try:
        return await genome_service.get_genomes(page, per_page, sortField, sortOrder)
    except Exception as e:
        logger.error(f"Error in get_all_genomes: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to search genomes by query string
@genome_router.get("/type-strains", response=List[TypeStrainSchema])
async def get_type_strains(request):
    return await genome_service.get_type_strains()


@genome_router.get("/search", response=GenomePaginationSchema)
async def search_genomes_by_string(
    request,
    query: str,
    page: int = 1,
    per_page: int = 10,
    sortField: Optional[str] = "isolate_name",
    sortOrder: Optional[str] = "asc",
):
    sortField = sortField or "isolate_name"
    sortOrder = sortOrder or "asc"
    return await genome_service.search_genomes_by_string(
        query, page, per_page, sortField, sortOrder
    )


# API Endpoint to retrieve genome by ID
@genome_router.get("/{genome_id}", response=SearchGenomeSchema)
async def get_genome(request, genome_id: int):
    try:
        return await genome_service.get_genome_by_id(genome_id)
    except Strain.DoesNotExist:
        raise HttpError(404, "Genome not found")


# API Endpoint to retrieve genomes filtered by species ID
@species_router.get("/{species_id}/genomes", response=GenomePaginationSchema)
async def get_genomes_by_species(
    request,
    species_id: int,
    page: int = 1,
    per_page: int = 10,
    sortField: Optional[str] = "isolate_name",
    sortOrder: Optional[str] = "asc",
):
    return await genome_service.get_genomes_by_species(
        species_id, page, per_page, sortField, sortOrder
    )


# API Endpoint to search genomes by species ID and query string
@species_router.get("/{species_id}/genomes/search", response=GenomePaginationSchema)
async def search_genomes_by_species_and_string(
    request,
    species_id: int,
    query: str,
    page: int = 1,
    per_page: int = 10,
    sortField: Optional[str] = "isolate_name",
    sortOrder: Optional[str] = "asc",
):
    return await genome_service.search_genomes_by_species_and_string(
        species_id, query, page, per_page, sortField, sortOrder
    )


@gene_router.get("/autocomplete", response=List[GeneAutocompleteResponseSchema])
async def gene_autocomplete_suggestions(
    request,
    query: str,
    limit: int = 10,
    species_id: Optional[int] = None,
    genome_ids: Optional[str] = None,
):
    genome_id_list = (
        [int(gid) for gid in genome_ids.split(",") if gid.strip()]
        if genome_ids
        else None
    )
    return await gene_service.autocomplete_gene_suggestions(
        query, limit, species_id, genome_id_list
    )


# API Endpoint to search genes by query string
@gene_router.get("/search", response=GenePaginationSchema)
async def search_genes_by_string(
    request, query: str, page: int = 1, per_page: int = 10
):
    try:
        paginated_results = await gene_service.search_genes(
            query=query, page=page, per_page=per_page
        )
        return paginated_results
    except Exception as e:
        logger.error(f"Error in search_genes_by_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to retrieve gene by ID
@gene_router.get("/{gene_id}", response=GeneResponseSchema)
async def get_gene_by_id(request, gene_id: int):
    return await gene_service.get_gene_by_id(gene_id)


# API Endpoint to retrieve all genes
@gene_router.get("/", response=GenePaginationSchema)
async def get_all_genes(request, page: int = 1, per_page: int = 10):
    return await gene_service.get_all_genes(page, per_page)


# API Endpoint to retrieve genes filtered by a single genome ID
@genome_router.get("/{genome_id}/genes", response=GenePaginationSchema)
async def get_genes_by_genome(
    request, genome_id: int, page: int = 1, per_page: int = 10
):
    try:
        return await gene_service.get_genes_by_genome(genome_id, page, per_page)
    except Exception as e:
        logger.error(f"Error in get_genes_by_genome: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to search genes by genome ID and gene string
@genome_router.get("/{genome_id}/genes/search", response=GenePaginationSchema)
async def search_genes_by_genome_and_string(
    request, genome_id: int, query: str, page: int = 1, per_page: int = 10
):
    try:
        return await gene_service.search_genes(query, genome_id, page, per_page)
    except Exception as e:
        logger.error(f"Error in search_genes_by_genome_and_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# API Endpoint to search genes across multiple genome IDs using a gene string
@gene_router.get("/search/filter", response=GenePaginationSchema)
async def search_genes_by_multiple_genomes_and_species_and_string(
    request,
    genome_ids: str = "",
    species_id: Optional[int] = None,
    query: str = "",
    page: int = 1,
    per_page: int = 10,
):
    try:
        return await gene_service.get_genes_by_multiple_genomes_and_string(
            genome_ids, species_id, query, page, per_page
        )
    except HttpError as e:
        raise e
    except ValueError:
        logger.error("Invalid genome ID provided")
        raise HttpError(400, "Invalid genome ID provided")
    except Exception as e:
        logger.error(f"Error in search_genes_by_multiple_genomes_and_string: {e}")
        raise HttpError(500, f"Internal Server Error: {str(e)}")


# Register routers with the main API
api.add_router("/species", species_router)
api.add_router("/genomes", genome_router)
api.add_router("/genes", gene_router)
