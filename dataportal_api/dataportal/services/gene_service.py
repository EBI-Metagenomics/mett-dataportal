import logging
from typing import Optional, List, Tuple, Dict

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from dataportal.models import Gene
from dataportal.schemas import GenePaginationSchema, GeneResponseSchema

logger = logging.getLogger(__name__)


class GeneService:
    def __init__(self, limit: int = 10):
        self.limit = limit

    async def autocomplete_gene_suggestions(
        self,
        query: str,
        limit: int = None,
        species_id: Optional[int] = None,
        genome_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        try:
            # Build the filter criteria
            gene_filter = (
                Q(gene_name__iexact=query)
                | Q(gene_name__icontains=query)
                | Q(product__icontains=query)
                | Q(locus_tag__icontains=query)
                | Q(kegg__icontains=query)
                | Q(pfam__icontains=query)
                | Q(interpro__icontains=query)
                | Q(dbxref__icontains=query)
            )

            # Add optional filters for species_id and genome_ids
            if species_id:
                gene_filter &= Q(strain__species_id=species_id)
            if genome_ids:
                gene_filter &= Q(strain_id__in=genome_ids)

            # Log the filter criteria for debugging
            logger.debug(
                f"Query: {query}, Species ID: {species_id}, Genome IDs: {genome_ids}"
            )
            logger.debug(f"Gene Filter: {gene_filter}")

            # Fetch the paginated and sorted genes
            genes, total_results = await self._fetch_paginated_genes(
                filter_criteria=gene_filter,
                page=1,
                per_page=limit or self.limit,
                sort_field="gene_name",  # Default sorting by gene name
                sort_order="asc",  # Change to "desc" if required
            )

            # Build and return the response
            response = [
                {
                    "gene_id": gene.id,
                    "gene_name": gene.gene_name,
                    "strain_name": gene.strain.isolate_name,
                    "product": gene.product,
                    "locus_tag": gene.locus_tag,
                    "kegg": gene.kegg,
                    "pfam": gene.pfam,
                    "interpro": gene.interpro,
                    "dbxref": gene.dbxref,
                }
                for gene in genes
            ]

            logger.debug(f"API Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error fetching gene autocomplete suggestions: {e}")
            return []

    async def get_gene_by_id(self, gene_id: int) -> GeneResponseSchema:
        try:
            gene = await sync_to_async(
                lambda: get_object_or_404(
                    Gene.objects.select_related("strain"), id=gene_id
                )
            )()
            return self._serialize_gene(gene)
        except Http404:
            raise HttpError(404, f"Gene with id {gene_id} not found")
        except Exception as e:
            logger.error(f"Error in get_gene_by_id: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_all_genes(
        self,
        page: int = 1,
        per_page: int = 10,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = "asc",
    ) -> GenePaginationSchema:
        try:
            genes, total_results = await self._fetch_paginated_genes(
                Q(), page, per_page, sort_field, sort_order
            )
            serialized_genes = [self._serialize_gene(gene) for gene in genes]
            return self._create_pagination_schema(
                serialized_genes, page, per_page, total_results
            )
        except Exception as e:
            logger.error(f"Error fetching all genes: {e}")
            raise HttpError(500, "Internal Server Error")

    async def search_genes(
        self,
        query: str = None,
        genome_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 10,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = "asc",
    ) -> GenePaginationSchema:
        try:
            filters = Q()
            if query:
                filters &= Q(gene_name__icontains=query) | Q(
                    description__icontains=query
                )
            if genome_id:
                filters &= Q(strain_id=genome_id)

            genes, total_results = await self._fetch_paginated_genes(
                filters, page, per_page, sort_field, sort_order
            )
            serialized_genes = [self._serialize_gene(gene) for gene in genes]
            return self._create_pagination_schema(
                serialized_genes, page, per_page, total_results
            )
        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genes_by_genome(
        self,
        genome_id: int,
        page: int = 1,
        per_page: int = 10,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = "asc",
    ) -> GenePaginationSchema:
        try:
            genes, total_results = await self._fetch_paginated_genes(
                Q(strain_id=genome_id), page, per_page, sort_field, sort_order
            )
            serialized_genes = [self._serialize_gene(gene) for gene in genes]
            return self._create_pagination_schema(
                serialized_genes, page, per_page, total_results
            )
        except Exception as e:
            logger.error(f"Error fetching genes for genome ID {genome_id}: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genes_by_multiple_genomes(
        self, genome_ids: List[int], page: int = 1, per_page: int = 10
    ):
        try:
            filter_criteria = Q(strain_id__in=genome_ids)
            genes, total_results = await self._fetch_paginated_genes(
                filter_criteria, page, per_page
            )
            serialized_genes = [self._serialize_gene(gene) for gene in genes]
            return self._create_pagination_schema(
                serialized_genes, page, per_page, total_results
            )
        except Exception as e:
            logger.error(f"Error fetching genes for genome IDs {genome_ids}: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genes_by_multiple_genomes_and_string(
        self,
        genome_ids: str = None,
        species_id: Optional[int] = None,
        query: str = None,
        page: int = 1,
        per_page: int = 10,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = "asc",
    ) -> GenePaginationSchema:
        try:
            # Parse genome IDs
            genome_id_list = (
                [int(gid) for gid in genome_ids.split(",") if gid.strip()]
                if genome_ids
                else []
            )
            filters = Q()

            # Add filters for genome IDs and species ID
            if genome_id_list:
                filters &= Q(strain_id__in=genome_id_list)
            if species_id:
                filters &= Q(strain__species_id=species_id)

            # Add gene search filters if query is provided
            if query:
                gene_filter = (
                    Q(gene_name__iexact=query.strip())
                    | Q(gene_name__icontains=query.strip())
                    | Q(product__icontains=query.strip())
                    | Q(locus_tag__icontains=query.strip())
                    | Q(kegg__icontains=query.strip())
                    | Q(pfam__icontains=query.strip())
                    | Q(interpro__icontains=query.strip())
                    | Q(dbxref__icontains=query.strip())
                )
                filters &= gene_filter

            # Valid sorting fields and their mappings
            valid_sort_fields = {
                "gene_name": "gene_name",
                "strain": "strain__isolate_name",
                "description": "description",
                "locus_tag": "locus_tag",
                "product": "product",
            }

            # Validate and map sort_field
            sort_field_mapped = valid_sort_fields.get(sort_field, "gene_name")
            if sort_field not in valid_sort_fields:
                logger.warning(
                    f"Invalid sort_field '{sort_field}', defaulting to 'gene_name'"
                )
                sort_field_mapped = "gene_name"

            logger.info(
                f"Fetching genes with sort_field='{sort_field_mapped}', sort_order='{sort_order}'"
            )

            # Fetch paginated genes with sorting
            genes, total_results = await self._fetch_paginated_genes(
                filters, page, per_page, sort_field_mapped, sort_order
            )

            # Serialize genes for the response
            serialized_genes = [self._serialize_gene(gene) for gene in genes]

            return self._create_pagination_schema(
                serialized_genes, page, per_page, total_results
            )
        except ValueError:
            logger.error("Invalid genome ID provided")
            raise HttpError(400, "Invalid genome ID provided")
        except Exception as e:
            logger.error(f"Error in get_genes_by_multiple_genomes_and_string: {e}")
            raise HttpError(500, "Internal Server Error")

    # helper methods

    def _serialize_gene(self, gene: Gene) -> dict:
        return GeneResponseSchema.model_validate(
            {
                "id": gene.id,
                "seq_id": gene.seq_id,
                "gene_name": gene.gene_name or "N/A",
                "description": gene.description or None,
                "strain_id": gene.strain.id if gene.strain else None,
                "strain": gene.strain.isolate_name if gene.strain else "Unknown",
                "assembly": (
                    gene.strain.assembly_name
                    if gene.strain and gene.strain.assembly_name
                    else None
                ),
                "locus_tag": gene.locus_tag or None,
                "cog": gene.cog or None,
                "kegg": gene.kegg or None,
                "pfam": gene.pfam or None,
                "interpro": gene.interpro or None,
                "dbxref": gene.dbxref or None,
                "ec_number": gene.ec_number or None,
                "product": gene.product or None,
                "start_position": gene.start_position or None,
                "end_position": gene.end_position or None,
                "annotations": gene.annotations or {},
            }
        )

    def _create_pagination_schema(
        self, serialized_genes, page, per_page, total_results
    ) -> GenePaginationSchema:
        return GenePaginationSchema(
            results=serialized_genes,
            page_number=page,
            num_pages=(total_results + per_page - 1) // per_page,
            has_previous=page > 1,
            has_next=(page * per_page) < total_results,
            total_results=total_results,
        )

    async def _fetch_paginated_genes(
        self,
        filter_criteria: Q,
        page: int,
        per_page: int,
        sort_field: Optional[str] = None,
        sort_order: Optional[str] = "asc",
    ) -> Tuple[List[Gene], int]:
        start = (page - 1) * per_page
        order_prefix = "-" if sort_order == "desc" else ""
        sort_by = f"{order_prefix}{sort_field}" if sort_field else "gene_name"

        try:
            logger.debug(f"Filter criteria: {filter_criteria}")
            logger.debug(f"Sorting by: {sort_by}")
            logger.debug(f"Pagination: start={start}, end={start + per_page}")

            # paginated and sorted gene list
            genes = await sync_to_async(
                lambda: list(
                    Gene.objects.select_related("strain")
                    .filter(filter_criteria)
                    .order_by(sort_by)[start : start + per_page]
                )
            )()

            total_results = await sync_to_async(
                Gene.objects.filter(filter_criteria).count
            )()

            logger.debug(f"Fetched genes: {[gene.gene_name for gene in genes]}")
            logger.debug(f"Total matching genes: {total_results}")

            return genes, total_results
        except Exception as e:
            logger.error(f"Error in _fetch_paginated_genes: {e}")
            raise
