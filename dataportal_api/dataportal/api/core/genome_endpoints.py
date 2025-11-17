import logging
from typing import List, Dict

from ninja import Router, Query, Path
from ninja.errors import HttpError

from dataportal.schema.core.gene_schemas import (
    EssentialityByContigSchema,
)
from dataportal.schema.core.genome_schemas import (
    StrainSuggestionSchema,
    GenomeResponseSchema,
    GenomeAutocompleteQuerySchema,
    GenomeSearchQuerySchema,
    GenomesByIsolateNamesQuerySchema,
    GetAllGenomesQuerySchema,
    GenesByGenomeQuerySchema,
    GenomeDownloadTSVQuerySchema,
)
from dataportal.schema.response_schemas import (
    GenomePaginatedResponseSchema,
    GenePaginatedResponseSchema,
)
from dataportal.services.core.gene_service import GeneService
from dataportal.services.experimental.drug_service import DrugService
from dataportal.services.experimental.essentiality_service import EssentialityService
from dataportal.services.service_factory import ServiceFactory
from dataportal.utils.constants import (
    DEFAULT_SORT_DIRECTION,
    GENOME_FIELD_ISOLATE_NAME,
    SCROLL_MAX_RESULTS,
)
from dataportal.utils.errors import raise_http_error, raise_internal_server_error
from dataportal.utils.exceptions import (
    ServiceError,
)
from dataportal.utils.response_wrappers import wrap_paginated_response

logger = logging.getLogger(__name__)

genome_service = ServiceFactory.get_genome_service()
gene_service = GeneService()
essentiality_service = EssentialityService()
drug_service = DrugService()

ROUTER_GENOME = "Genomes"
genome_router = Router(tags=[ROUTER_GENOME])


@genome_router.get(
    "/autocomplete",
    response=List[StrainSuggestionSchema],
    summary="Suggest isolates / genomes",
    description="Returns isolate suggestions based on the input query. You can optionally filter by species acronym. ",
    include_in_schema=False,
)
async def autocomplete_suggestions(request, query: GenomeAutocompleteQuerySchema = Query(...)):
    return await genome_service.search_strains(query)


# API Endpoint to search genomes by query string
@genome_router.get(
    "/type-strains",
    response=List[GenomeResponseSchema],
    summary="Get all type strains",
    description=(
        "Returns a list of genomes that are designated as type strains. "
        "Type strains represent reference genomes for a given species and are essential "
        "for comparative analysis and classification."
    ),
)
async def get_type_strains(request):
    try:
        return await genome_service.get_type_strains()
    except ServiceError:
        raise HttpError(500, "An error occurred while fetching type strains.")


@genome_router.get(
    "/search",
    response=GenomePaginatedResponseSchema,
    summary="Search genomes by query",
    description=(
        "Searches genomes using a free-text query string. "
        "Returns a paginated list of matching genome records. "
        "Supports optional sorting by 'isolate_name' or 'species'."
    ),
)
@wrap_paginated_response
async def search_genomes_by_string(request, query: GenomeSearchQuerySchema = Query(...)):
    try:
        result = await genome_service.search_genomes_by_string(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error in genome search: {e}")
        raise_internal_server_error(f"Failed to search genomes: {str(e)}")


@genome_router.get(
    "/by-isolate-names",
    response=List[GenomeResponseSchema],
    summary="Get genomes by isolate names",
    description=(
        "Retrieves genome records for one or more isolate names. "
        "Accepts a comma-separated list of isolate names as input. "
        "Useful for batch lookups when isolate identifiers are known."
    ),
)
async def get_genomes_by_isolate_names(
    request, query: GenomesByIsolateNamesQuerySchema = Query(...)
):
    try:
        return await genome_service.get_genomes_by_isolate_names(query)
    except ServiceError as e:
        raise_http_error(500, f"An error occurred: {str(e)}")


# API Endpoint to retrieve all genomes
@genome_router.get(
    "/",
    response=GenomePaginatedResponseSchema,
    summary="Get all genomes",
    description="Retrieves a paginated list of all genomes available in the system. "
    "Supports optional sorting by 'isolate_name' or 'species'. ",
)
@wrap_paginated_response
async def get_all_genomes(request, query: GetAllGenomesQuerySchema = Query(...)):
    try:
        result = await genome_service.get_genomes(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error in get all genomes: {e}")
        raise_internal_server_error("Failed to fetch genomes")
    except Exception as e:
        logger.error(f"Unexpected error in get all genomes: {e}")
        raise_internal_server_error("Failed to fetch genomes")


# API Endpoint to retrieve genes filtered by a single genome ID
@genome_router.get(
    "/{isolate_name}/genes",
    response=GenePaginatedResponseSchema,
    summary="Get genes by genome isolate",
    description=(
        "Retrieves a paginated list of genes associated with a specific genome isolate. "
        "Supports optional sorting by 'isolate_name', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'. "
        "Useful for viewing all genes within a selected genome."
    ),
)
@wrap_paginated_response
async def get_genes_by_genome(
    request,
    isolate_name: str = Path(
        ...,
        description="Unique isolate name identifying the genome.",
        example="BU_ATCC8492",
    ),
    query: GenesByGenomeQuerySchema = Query(...),
):
    try:
        result = await gene_service.get_genes_by_genome(
            isolate_name,
            query.filter,
            query.filter_operators,
            query.page,
            query.per_page,
            query.sort_field,
            query.sort_order,
        )
        return result
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(
            f"Failed to fetch the genes information for genome_id - {isolate_name}"
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
    ),
)
async def get_essentiality_data_by_contig(
    request,
    isolate_name: str = Path(
        ...,
        description="Isolate name identifying the genome.",
        example="BU_ATCC8492",
    ),
    ref_name: str = Path(
        ...,
        description="Reference sequence (e.g. contig_1) name to retrieve essentiality data for.",
        example="contig_1",
    ),
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


@genome_router.get(
    "/download/tsv",
    summary="Download all genomes in TSV format",
    description=(
        "Downloads all genomes matching the current filters in TSV (Tab-Separated Values) format. "
        "This endpoint returns all records without pagination, suitable for bulk data export. "
        "Supports the same filtering options as the search endpoints."
    ),
    include_in_schema=False,
)
async def download_genomes_tsv(request, query: GenomeDownloadTSVQuerySchema = Query(...)):
    try:
        logger.debug(
            f"Download TSV request received with params: query={query.query}, sortField={query.sortField}, sortOrder={query.sortOrder}, isolates={query.isolates}, species_acronym={query.species_acronym}"
        )

        # Create a GenomeSearchQuerySchema object from the download query params
        search_params = GenomeSearchQuerySchema(
            query=query.query or "",  # Ensure empty string if None
            page=1,
            per_page=SCROLL_MAX_RESULTS,  # Use constant for large downloads
            sortField=query.sortField or GENOME_FIELD_ISOLATE_NAME,
            sortOrder=query.sortOrder or DEFAULT_SORT_DIRECTION,
            isolates=query.isolates,
            species_acronym=query.species_acronym,
        )

        # Get all records without pagination using the existing service method
        data_response = await genome_service.search_genomes_by_string(
            params=search_params,
            use_scroll=True,  # Use scroll API for large downloads
        )

        # Use streaming response for large datasets
        from django.http import StreamingHttpResponse

        def generate_tsv():
            # Define the columns to include in the TSV export
            columns = [
                "isolate_name",
                "species_scientific_name",
                "species_acronym",
                "assembly_name",
                "assembly_accession",
                "type_strain",
            ]

            # Yield header row
            yield "\t".join(columns) + "\n"

            # Yield data rows one by one
            for genome in data_response.results:
                row_data = []
                for col in columns:
                    value = getattr(genome, col, "")
                    value = str(value) if value is not None else ""

                    # Escape tabs and newlines in the value
                    value = value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
                    row_data.append(value)

                yield "\t".join(row_data) + "\n"

        # Return streaming response
        http_response = StreamingHttpResponse(
            generate_tsv(), content_type="text/tab-separated-values"
        )
        http_response["Content-Disposition"] = 'attachment; filename="genomes_export.tsv"'
        return http_response

    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, f"Failed to download genomes: {str(e)}")
