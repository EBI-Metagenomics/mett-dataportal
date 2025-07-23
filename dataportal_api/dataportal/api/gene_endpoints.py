import logging
from typing import Optional

from ninja import Router, Query, Path

from dataportal.schema.gene_schemas import (
    GeneAutocompleteQuerySchema,
    GeneSearchQuerySchema,
    GeneFacetedSearchQuerySchema,
    GeneAdvancedSearchQuerySchema,
    GeneDownloadTSVQuerySchema,
)
from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    PaginatedResponseSchema,
    create_success_response,
)
from ..services.gene_service import GeneService
from ..utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    ES_FIELD_PFAM,
    ES_FIELD_INTERPRO,
    ES_FIELD_COG_ID,
    ES_FIELD_COG_FUNCATS,
    ES_FIELD_KEGG,
    ES_FIELD_ISOLATE_NAME,
    ES_FIELD_GENE_NAME,
    ES_FIELD_ALIAS,
    STRAIN_FIELD_CONTIG_SEQ_ID,
    ES_FIELD_LOCUS_TAG,
    ES_FIELD_PRODUCT,
    ES_FIELD_UNIPROT_ID,
    GENE_ESSENTIALITY,
    ES_FIELD_AMR,
    ES_FIELD_AMR_DRUG_CLASS,
    ES_FIELD_AMR_DRUG_SUBCLASS,
)
from ..utils.errors import (
    raise_not_found_error,
    raise_internal_server_error,
    raise_validation_error,
)
from ..utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
    InvalidGenomeIdError,
)
from ..utils.response_wrappers import wrap_success_response, wrap_paginated_response

logger = logging.getLogger(__name__)

gene_service = GeneService()

ROUTER_GENE = "Genes"
gene_router = Router(tags=[ROUTER_GENE])


@gene_router.get(
    "/autocomplete",
    response=SuccessResponseSchema,
    summary="Autocomplete gene names",
    include_in_schema=False,
)
@wrap_success_response
async def gene_autocomplete_suggestions(
    request, query: GeneAutocompleteQuerySchema = Query(...)
):
    try:
        result = await gene_service.autocomplete_gene_suggestions(query)
        return create_success_response(
            data=result, message=f"Found {len(result)} gene suggestions"
        )
    except ServiceError as e:
        logger.error(f"Service error in autocomplete: {e}")
        raise_internal_server_error(f"Failed to fetch gene suggestions: {str(e)}")


# API Endpoint to search genes by query string
@gene_router.get(
    "/search",
    response=PaginatedResponseSchema,
    summary="Search genes by query string",
)
@wrap_paginated_response
async def search_genes_by_string(request, query: GeneSearchQuerySchema = Query(...)):
    try:
        result = await gene_service.search_genes(query)
        return result
    except ServiceError as e:
        logger.error(f"Service error in gene search: {e}")
        raise_internal_server_error(f"Failed to search genes: {str(e)}")


@gene_router.get(
    "/faceted-search",
    response=SuccessResponseSchema,
    summary="Perform faceted search on genes",
    include_in_schema=False,
)
@wrap_success_response
async def get_faceted_search(request, query: GeneFacetedSearchQuerySchema = Query(...)):
    try:
        result = await gene_service.get_faceted_search(query)
        return create_success_response(
            data=result, message="Faceted search completed successfully"
        )
    except ServiceError as e:
        logger.error(f"Service error in faceted search: {e}")
        raise_internal_server_error(f"Failed to perform faceted search: {str(e)}")


# API Endpoint to retrieve gene by locus tag
@gene_router.get(
    "/{locus_tag}",
    response=SuccessResponseSchema,
    summary="Get gene by locus tag",
    description=(
        "Retrieves detailed information for a specific gene using its unique locus tag. "
        "Returns metadata and functional annotation associated with the gene. "
        "This endpoint is useful for direct lookups when the locus tag is already known."
    ),
)
@wrap_success_response
async def get_gene_by_locus_tag(
    request,
    locus_tag: str = Path(
        ..., description="Unique locus tag identifier for the gene (e.g., 'ABC_123')."
    ),
):
    try:
        result = await gene_service.get_gene_by_locus_tag(locus_tag)
        return create_success_response(
            data=result, message=f"Gene {locus_tag} retrieved successfully"
        )
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {e.locus_tag}")
        raise_not_found_error(
            f"Gene with locus tag '{locus_tag}' not found", error_code="GENE_NOT_FOUND"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(
            f"Failed to fetch gene information for locus tag '{locus_tag}'"
        )


# API Endpoint to retrieve all genes
@gene_router.get(
    "/",
    response=PaginatedResponseSchema,
    summary="Get all genes",
    description=(
        "Retrieves a paginated list of all genes across all available genomes. "
        "Supports optional sorting by 'isolate_name', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'. "
        "Useful for browsing the full gene catalog without applying filters."
    ),
)
@wrap_paginated_response
async def get_all_genes(
    request,
    page: int = Query(1, description="Page number to retrieve."),
    per_page: int = Query(
        DEFAULT_PER_PAGE_CNT, description="Number of genes to return per page."
    ),
    sort_field: Optional[str] = Query(None, description="Field to sort results by."),
    sort_order: Optional[str] = Query(
        DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."
    ),
):
    try:
        result = await gene_service.get_all_genes(
            page, per_page, sort_field, sort_order
        )
        return result
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error("Failed to fetch genes information")


# API Endpoint to search genes across multiple genome IDs using a gene string
@gene_router.get(
    "/search/advanced",
    response=PaginatedResponseSchema,
    summary="Advanced gene search across genomes and species",
)
@wrap_paginated_response
async def search_genes_by_multiple_genomes_and_species_and_string(
    request, query: GeneAdvancedSearchQuerySchema = Query(...)
):
    try:
        result = await gene_service.get_genes_by_multiple_genomes_and_string(query)
        return result
    except InvalidGenomeIdError:
        raise_validation_error(f"Invalid genome ID provided: {query.isolates}")
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to fetch genes information: {str(e)}")


@gene_router.get(
    "/protein/{locus_tag}",
    response=SuccessResponseSchema,
    summary="Get protein sequence by locus tag",
    description=(
        "Retrieves the protein sequence for a specific gene using its unique locus tag. "
        "Returns the amino acid sequence in FASTA format. "
        "This endpoint is useful for protein sequence analysis and visualization."
    ),
    include_in_schema=False,
)
@wrap_success_response
async def get_gene_protein_seq(
    request,
    locus_tag: str = Path(
        ...,
        description="Unique locus tag identifier for the gene (e.g., 'BU_ATCC8492_00001').",
    ),
):
    try:
        result = await gene_service.get_gene_protein_seq(locus_tag)
        return create_success_response(
            data=result,
            message=f"Protein sequence for gene {locus_tag} retrieved successfully",
        )
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {e.locus_tag}")
        raise_not_found_error(
            f"Gene with locus tag '{locus_tag}' not found", error_code="GENE_NOT_FOUND"
        )
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(
            f"Failed to fetch protein sequence for locus tag '{locus_tag}'"
        )


@gene_router.get(
    "/download/tsv",
    summary="Download all genes in TSV format",
    include_in_schema=False,
)
async def download_genes_tsv(request, query: GeneDownloadTSVQuerySchema = Query(...)):
    try:
        logger.debug(
            f"Download TSV request received with params: query={query}, filter={filter}, sortField={query.sort_field}, sortOrder={query.sort_order}"
        )

        # Use streaming response for large datasets
        from django.http import StreamingHttpResponse

        def generate_tsv():
            # Define the columns to include in the TSV export
            columns = [
                ES_FIELD_ISOLATE_NAME,
                ES_FIELD_GENE_NAME,
                ES_FIELD_ALIAS,
                STRAIN_FIELD_CONTIG_SEQ_ID,
                ES_FIELD_LOCUS_TAG,
                ES_FIELD_PRODUCT,
                ES_FIELD_UNIPROT_ID,
                GENE_ESSENTIALITY,
                ES_FIELD_PFAM,
                ES_FIELD_INTERPRO,
                ES_FIELD_KEGG,
                ES_FIELD_COG_FUNCATS,
                ES_FIELD_COG_ID,
                ES_FIELD_AMR,
            ]

            # Yield header row
            yield "\t".join(columns) + "\n"

            # Stream genes directly from the service
            import asyncio

            async def stream_genes():
                async for gene in gene_service.stream_genes_with_scroll(
                    isolates=query.isolates,
                    species_acronym=query.species_acronym,
                    query=query.query,
                    filter=filter,
                    filter_operators=query.filter_operators,
                    sort_field=query.sort_field,
                    sort_order=query.sort_order,
                ):
                    row_data = []
                    for col in columns:
                        value = getattr(gene, col, "")

                        # Handle special cases
                        if col == ES_FIELD_ALIAS and value:
                            value = (
                                "; ".join(value)
                                if isinstance(value, list)
                                else str(value)
                            )
                        elif col == ES_FIELD_PFAM and value:
                            value = (
                                "; ".join(value)
                                if isinstance(value, list)
                                else str(value)
                            )
                        elif col == ES_FIELD_INTERPRO and value:
                            value = (
                                "; ".join(value)
                                if isinstance(value, list)
                                else str(value)
                            )
                        elif col == ES_FIELD_KEGG and value:
                            value = (
                                "; ".join(value)
                                if isinstance(value, list)
                                else str(value)
                            )
                        elif col == ES_FIELD_COG_ID and value:
                            value = (
                                "; ".join(value)
                                if isinstance(value, list)
                                else str(value)
                            )
                        elif col == ES_FIELD_AMR and value:
                            # Format AMR data
                            amr_parts = []
                            for amr_item in value:
                                # Handle both dictionary and Pydantic model cases
                                if (
                                    hasattr(amr_item, ES_FIELD_AMR_DRUG_CLASS)
                                    and amr_item.drug_class
                                ):
                                    drug_class = amr_item.drug_class
                                    drug_subclass = getattr(
                                        amr_item, ES_FIELD_AMR_DRUG_SUBCLASS, ""
                                    )
                                    amr_parts.append(f"{drug_class}({drug_subclass})")
                                elif isinstance(amr_item, dict) and amr_item.get(
                                    ES_FIELD_AMR_DRUG_CLASS
                                ):
                                    drug_class = amr_item[ES_FIELD_AMR_DRUG_CLASS]
                                    drug_subclass = amr_item.get(
                                        ES_FIELD_AMR_DRUG_SUBCLASS, ""
                                    )
                                    amr_parts.append(f"{drug_class}({drug_subclass})")
                            value = "; ".join(amr_parts) if amr_parts else ""
                        else:
                            value = str(value) if value is not None else ""

                        # Escape tabs and newlines in the value
                        value = (
                            value.replace("\t", " ")
                            .replace("\n", " ")
                            .replace("\r", " ")
                        )
                        row_data.append(value)

                    yield "\t".join(row_data) + "\n"

            # Run the async generator in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async_gen = stream_genes()
                while True:
                    try:
                        result = loop.run_until_complete(async_gen.__anext__())
                        yield result
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()

        # Return streaming response
        response = StreamingHttpResponse(
            generate_tsv(), content_type="text/tab-separated-values"
        )
        response["Content-Disposition"] = 'attachment; filename="genes_export.tsv"'
        return response

    except InvalidGenomeIdError:
        raise_validation_error(f"Invalid genome ID provided: {query.isolates}")
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_internal_server_error(f"Failed to download genes: {str(e)}")
