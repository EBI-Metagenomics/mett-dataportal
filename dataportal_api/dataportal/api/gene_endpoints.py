import logging
from typing import List, Optional

from ninja import Router, Query, Path
from ninja.errors import HttpError

from ..schemas import (
    GeneAutocompleteResponseSchema,
    GenePaginationSchema,
    GeneProteinSeqSchema,
    GeneResponseSchema,
)
from ..services.gene_service import GeneService
from ..utils.constants import (
    DEFAULT_PER_PAGE_CNT,
    DEFAULT_SORT,
    DEFAULT_FACET_LIMIT,
)
from ..utils.errors import raise_http_error
from ..utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
    InvalidGenomeIdError,
)

logger = logging.getLogger(__name__)

gene_service = GeneService()

ROUTER_GENE = "Genes"
gene_router = Router(tags=[ROUTER_GENE])


@gene_router.get(
    "/autocomplete",
    response=List[GeneAutocompleteResponseSchema],
    summary="Autocomplete gene names",
    description=(
        "Provides gene name suggestions based on a query string. "
        "Supports optional filters such as essentiality, interpro, pfam and more. "
        "Allows to limit suggestions to specific isolates. Useful for building search dropdowns or gene lookup helpers."
    ),
    include_in_schema=False,
)
async def gene_autocomplete_suggestions(
    request,
    query: str = Query(..., description="Free-text input to search for gene metadata."),
    filter: Optional[str] = Query(
        None,
        description="Optional gene filter, e.g., 'essentiality:essential_liquid;interpro:IPR035952'.",
    ),
    limit: int = Query(
        DEFAULT_PER_PAGE_CNT, description="Maximum number of suggestions to return."
    ),
    species_acronym: Optional[str] = Query(
        None, description="Filter results by 'species_acronym'."
    ),
    isolates: Optional[str] = Query(
        None, description="Comma-separated isolate names to restrict the search scope."
    ),
):
    isolate_list = (
        [gid.strip() for gid in isolates.split(",") if gid.strip()]
        if isolates
        else None
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
        "Supports optional sorting by 'isolate_name', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'."
    ),
)
async def search_genes_by_string(
    request,
    query: str = Query(
        ..., description="Search term to match against gene names or locus tags."
    ),
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
    include_in_schema=False,
)
async def get_faceted_search(
    request,
    query: Optional[str] = Query(
        None, description="Search query across gene fields (gene name, product, etc.)"
    ),
    species_acronym: Optional[str] = Query(
        None, description="Species acronym to filter genes by (BU or PV)."
    ),
    essentiality: Optional[str] = Query(
        None, description="Essentiality status to filter genes (e.g., 'essential')."
    ),
    isolates: Optional[str] = Query(
        "", description="Comma-separated list of isolate names."
    ),
    cog_id: Optional[str] = Query(
        None, description="Comma-separated list of COG IDs to filter by."
    ),
    cog_funcats: Optional[str] = Query(
        None,
        description="Comma-separated list of COG functional categories to filter by.",
    ),
    kegg: Optional[str] = Query(
        None, description="KEGG pathway or gene ID to filter by."
    ),
    go_term: Optional[str] = Query(
        None, description="GO term ID or label to filter by."
    ),
    pfam: Optional[str] = Query(None, description="Pfam domain ID to filter by."),
    interpro: Optional[str] = Query(None, description="InterPro ID to filter by."),
    has_amr_info: Optional[bool] = Query(
        None, description="Filter genes that contain AMR information."
    ),
    pfam_operator: Optional[str] = Query(
        "OR", description="Logical operator (AND/OR) for Pfam filtering."
    ),
    interpro_operator: Optional[str] = Query(
        "OR", description="Logical operator (AND/OR) for InterPro filtering."
    ),
    cog_id_operator: Optional[str] = Query(
        "OR", description="Logical operator (AND/OR) for COG ID filtering."
    ),
    cog_funcats_operator: Optional[str] = Query(
        "OR",
        description="Logical operator (AND/OR) for COG functional categories filtering.",
    ),
    kegg_operator: Optional[str] = Query(
        "OR", description="Logical operator (AND/OR) for KEGG filtering."
    ),
    go_term_operator: Optional[str] = Query(
        "OR", description="Logical operator (AND/OR) for GO term filtering."
    ),
    limit: int = Query(
        DEFAULT_FACET_LIMIT, description="Maximum number of genes to return."
    ),
):
    isolate_names_list = [id.strip() for id in isolates.split(",")] if isolates else []
    logger.info(
        f"Isolates received: {isolate_names_list} (type: {type(isolate_names_list)})"
    )
    return await gene_service.get_faceted_search(
        query,
        species_acronym,
        isolate_names_list,
        essentiality,
        cog_id,
        cog_funcats,
        kegg,
        go_term,
        pfam,
        interpro,
        has_amr_info,
        limit,
        operators={
            "pfam": pfam_operator,
            "interpro": interpro_operator,
            "cog_id": cog_id_operator,
            "cog_funcats": cog_funcats_operator,
            "kegg": kegg_operator,
            "go_term": go_term_operator,
        },
    )


# API Endpoint to retrieve gene by locus tag
@gene_router.get(
    "/{locus_tag}",
    response=GeneResponseSchema,
    summary="Get gene by locus tag",
    description=(
        "Retrieves detailed information for a specific gene using its unique locus tag. "
        "Returns metadata and functional annotation associated with the gene. "
        "This endpoint is useful for direct lookups when the locus tag is already known."
    ),
)
async def get_gene_by_locus_tag(
    request,
    locus_tag: str = Path(
        ..., description="Unique locus tag identifier for the gene (e.g., 'ABC_123')."
    ),
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
        "Supports optional sorting by 'isolate_name', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'. "
        "Useful for browsing the full gene catalog without applying filters."
    ),
)
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
        return await gene_service.get_all_genes(page, per_page, sort_field, sort_order)
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(500, "Failed to fetch the genes information")


# API Endpoint to search genes across multiple genome IDs using a gene string
@gene_router.get(
    "/search/advanced",
    response=GenePaginationSchema,
    summary="Advanced gene search across genomes and species",
    description=(
        "Performs an advanced gene search using a free-text query across multiple genome isolates "
        "and/or a specific species. Supports filtering by species, essentiality, isolates, "
        "and annotation sources like COG, KEGG, GO terms, Pfam, and InterPro. "
        "Supports optional sorting by 'isolate_name', 'gene_name', 'alias', 'seq_id', 'locus_tag' and 'product'."
        "Useful for cross-genome comparisons or focused searches within a species context."
    ),
)
async def search_genes_by_multiple_genomes_and_species_and_string(
    request,
    isolates: str = Query(
        "",
        description="Comma-separated list of isolate names to restrict the search scope.",
    ),
    species_acronym: Optional[str] = Query(
        None, description="Optional species acronym to filter by."
    ),
    query: str = Query(
        "",
        description="Free-text search string to match against gene names or annotations.",
    ),
    filter: Optional[str] = Query(
        None,
        description="Additional gene filter, e.g., 'pfam:pf07715;interpro:ipr012910'.",
    ),
    filter_operators: Optional[str] = Query(
        None,
        description="Logical operator (AND/OR) per facet, e.g., 'pfam:AND;interpro:OR'",
    ),
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
            filter_operators,
            page,
            per_page,
            sort_field,
            sort_order,
            use_scroll=False,
        )
    except InvalidGenomeIdError:
        raise_http_error(400, f"Invalid genome ID provided: {isolates}")
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_http_error(500, f"Failed to fetch the genes information: {str(e)}")


@gene_router.get(
    "/protein/{locus_tag}",
    response=GeneProteinSeqSchema,
    summary="Get protein sequence by locus tag",
    description=(
        "Retrieves the protein sequence for a specific gene using its unique locus tag. "
        "Returns the amino acid sequence in FASTA format. "
        "This endpoint is useful for protein sequence analysis and visualization."
    ),
    include_in_schema=False,
)
async def get_gene_protein_seq(
    request,
    locus_tag: str = Path(
        ...,
        description="Unique locus tag identifier for the gene (e.g., 'BU_ATCC8492_00001').",
    ),
):
    try:
        return await gene_service.get_gene_protein_seq(locus_tag)
    except GeneNotFoundError as e:
        logger.error(f"Gene not found: {e.locus_tag}")
        raise HttpError(404, str(e))
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise HttpError(
            500, f"Failed to fetch the protein sequence for locus_tag - {locus_tag}"
        )


@gene_router.get(
    "/download/tsv",
    summary="Download all genes in TSV format",
    description=(
        "Downloads all genes matching the current filters in TSV (Tab-Separated Values) format. "
        "This endpoint returns all records without pagination, suitable for bulk data export. "
        "Supports the same filtering options as the search endpoints."
    ),
    include_in_schema=False,
)
async def download_genes_tsv(
    request,
    isolates: str = Query(
        "",
        description="Comma-separated list of isolate names to restrict the search scope.",
    ),
    species_acronym: Optional[str] = Query(
        None, description="Optional species acronym to filter by."
    ),
    query: str = Query(
        "",
        description="Free-text search string to match against gene names or annotations.",
    ),
    filter: Optional[str] = Query(
        None,
        description="Additional gene filter, e.g., 'pfam:pf07715;interpro:ipr012910'.",
    ),
    filter_operators: Optional[str] = Query(
        None,
        description="Logical operator (AND/OR) per facet, e.g., 'pfam:AND;interpro:OR'",
    ),
    sort_field: Optional[str] = Query(None, description="Field to sort results by."),
    sort_order: Optional[str] = Query(
        DEFAULT_SORT, description="Sort order: 'asc' or 'desc'."
    ),
):
    try:
        logger.debug(
            f"Download TSV request received with params: query={query}, filter={filter}, sortField={sort_field}, sortOrder={sort_order}"
        )
        
        # Use streaming response for large datasets
        from django.http import StreamingHttpResponse
        
        def generate_tsv():
            # Define the columns to include in the TSV export
            columns = [
                'isolate_name', 'gene_name', 'alias', 'seq_id', 'locus_tag', 
                'product', 'uniprot_id', 'essentiality', 'pfam', 'interpro', 
                'kegg', 'cog_funcats', 'cog_id', 'amr'
            ]
            
            # Yield header row
            yield '\t'.join(columns) + '\n'
            
            # Stream genes directly from the service
            import asyncio
            
            async def stream_genes():
                async for gene in gene_service.stream_genes_with_scroll(
                    isolates=isolates,
                    species_acronym=species_acronym,
                    query=query,
                    filter=filter,
                    filter_operators=filter_operators,
                    sort_field=sort_field,
                    sort_order=sort_order,
                ):
                    row_data = []
                    for col in columns:
                        value = getattr(gene, col, '')
                        
                        # Handle special cases
                        if col == 'alias' and value:
                            value = '; '.join(value) if isinstance(value, list) else str(value)
                        elif col == 'pfam' and value:
                            value = '; '.join(value) if isinstance(value, list) else str(value)
                        elif col == 'interpro' and value:
                            value = '; '.join(value) if isinstance(value, list) else str(value)
                        elif col == 'kegg' and value:
                            value = '; '.join(value) if isinstance(value, list) else str(value)
                        elif col == 'amr' and value:
                            # Format AMR data
                            amr_parts = []
                            for amr_item in value:
                                # Handle both dictionary and Pydantic model cases
                                if hasattr(amr_item, 'drug_class') and amr_item.drug_class:
                                    drug_class = amr_item.drug_class
                                    drug_subclass = getattr(amr_item, 'drug_subclass', '')
                                    amr_parts.append(f"{drug_class}({drug_subclass})")
                                elif isinstance(amr_item, dict) and amr_item.get('drug_class'):
                                    drug_class = amr_item['drug_class']
                                    drug_subclass = amr_item.get('drug_subclass', '')
                                    amr_parts.append(f"{drug_class}({drug_subclass})")
                            value = '; '.join(amr_parts) if amr_parts else ''
                        else:
                            value = str(value) if value is not None else ''
                        
                        # Escape tabs and newlines in the value
                        value = value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
                        row_data.append(value)
                    
                    yield '\t'.join(row_data) + '\n'
            
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
            generate_tsv(),
            content_type='text/tab-separated-values'
        )
        response['Content-Disposition'] = 'attachment; filename="genes_export.tsv"'
        return response
        
    except InvalidGenomeIdError:
        raise_http_error(400, f"Invalid genome ID provided: {isolates}")
    except ServiceError as e:
        logger.error(f"Service error: {e}")
        raise_http_error(500, f"Failed to download genes: {str(e)}")
