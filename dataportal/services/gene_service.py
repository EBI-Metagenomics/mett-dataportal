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
            self, query: str, limit: int = None, species_id: Optional[int] = None,
            genome_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        try:
            gene_filter = Q(gene_name__icontains=query)
            if species_id:
                gene_filter &= Q(strain__species_id=species_id)
            if genome_ids:
                gene_filter &= Q(strain_id__in=genome_ids)

            genes, _ = await self._fetch_paginated_genes(gene_filter, page=1, per_page=limit or self.limit)
            return [{"gene_id": gene.id, "gene_name": gene.gene_name, "strain_name": gene.strain.isolate_name} for gene
                    in genes]
        except Exception as e:
            logger.error(f"Error fetching gene autocomplete suggestions: {e}")
            return []

    async def get_gene_by_id(self, gene_id: int) -> GeneResponseSchema:
        try:
            gene = await sync_to_async(lambda: get_object_or_404(Gene.objects.select_related('strain'), id=gene_id))()
            return self._serialize_gene(gene)
        except Http404:
            raise HttpError(404, f"Gene with id {gene_id} not found")
        except Exception as e:
            logger.error(f"Error in get_gene_by_id: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_all_genes(self, page: int = 1, per_page: int = 10) -> GenePaginationSchema:
        try:
            genes, total_results = await self._fetch_paginated_genes(Q(), page, per_page)
            serialized_genes = [self._serialize_gene(gene) for gene in genes]

            return GenePaginationSchema(
                results=serialized_genes,
                page_number=page,
                num_pages=(total_results + per_page - 1) // per_page,
                has_previous=page > 1,
                has_next=(page * per_page) < total_results,
                total_results=total_results
            )
        except Exception as e:
            logger.error(f"Error fetching all genes: {e}")
            raise HttpError(500, "Internal Server Error")

    async def search_genes(self, query: str = None, genome_id: Optional[int] = None,
                           page: int = 1, per_page: int = 10):
        try:
            filters = Q()
            if query:
                filters &= Q(gene_name__icontains=query) | Q(description__icontains=query)
            if genome_id:
                filters &= Q(strain_id=genome_id)

            genes, total_results = await self._fetch_paginated_genes(filters, page, per_page)
            serialized_genes = [self._serialize_gene(gene) for gene in genes]

            return GenePaginationSchema(
                results=serialized_genes,
                page_number=page,
                num_pages=(total_results + per_page - 1) // per_page,
                has_previous=page > 1,
                has_next=(page * per_page) < total_results,
                total_results=total_results
            )
        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genes_by_genome(self, genome_id: int, page: int = 1, per_page: int = 10):
        try:
            genes, total_results = await self._fetch_paginated_genes(Q(strain_id=genome_id), page, per_page)
            serialized_genes = [self._serialize_gene(gene) for gene in genes]

            return GenePaginationSchema(
                results=serialized_genes,
                page_number=page,
                num_pages=(total_results + per_page - 1) // per_page,
                has_previous=page > 1,
                has_next=(page * per_page) < total_results,
                total_results=total_results
            )
        except Exception as e:
            logger.error(f"Error fetching genes for genome ID {genome_id}: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genes_by_multiple_genomes(self, genome_ids: List[int], page: int = 1, per_page: int = 10):
        try:
            filter_criteria = Q(strain_id__in=genome_ids)
            genes, total_results = await self._fetch_paginated_genes(filter_criteria, page, per_page)
            serialized_genes = [self._serialize_gene(gene) for gene in genes]
            return self._create_pagination_schema(
                serialized_genes,
                page,
                per_page,
                total_results
            )
        except Exception as e:
            logger.error(f"Error fetching genes for genome IDs {genome_ids}: {e}")
            raise HttpError(500, "Internal Server Error")

    async def get_genes_by_multiple_genomes_and_string(
            self, genome_ids: str = None, species_id: Optional[int] = None,
            query: str = None, page: int = 1, per_page: int = 10
    ) -> GenePaginationSchema:
        try:
            genome_id_list = [int(gid) for gid in genome_ids.split(",") if gid.strip()] if genome_ids else []
            filters = Q()

            if genome_id_list:
                filters &= Q(strain_id__in=genome_id_list)
            if species_id:
                filters &= Q(strain__species_id=species_id)
            if query:
                filters &= Q(gene_name__icontains=query.strip())

            genes, total_results = await self._fetch_paginated_genes(filters, page, per_page)
            serialized_genes = [self._serialize_gene(gene) for gene in genes]

            return GenePaginationSchema(
                results=serialized_genes,
                page_number=page,
                num_pages=(total_results + per_page - 1) // per_page,
                has_previous=page > 1,
                has_next=(page * per_page) < total_results,
                total_results=total_results,
            )
        except ValueError:
            logger.error("Invalid genome ID provided")
            raise HttpError(400, "Invalid genome ID provided")
        except Exception as e:
            logger.error(f"Error in search_genes_by_multiple_genomes_and_string: {e}")
            raise HttpError(500, "Internal Server Error")

    async def search_genes_in_strain(self, strain_id: int, query: str, limit: int = 10):
        try:
            gene_filter = Q(strain_id=strain_id, gene_name__icontains=query)
            genes = await sync_to_async(lambda: list(
                Gene.objects.filter(gene_filter).select_related('strain')[:limit]
            ))()
            return [{"gene_name": gene.gene_name, "description": gene.description} for gene in genes]
        except Exception as e:
            logger.error(f"Error searching genes in strain: {e}")
            return []

    async def search_genes_globally(self, query: str, limit: int = 10):
        try:
            gene_filter = Q(gene_name__icontains=query) | Q(description__icontains=query)
            genes = await sync_to_async(lambda: list(
                Gene.objects.filter(gene_filter).select_related('strain')[:limit]
            ))()
            return [
                {
                    "gene_name": gene.gene_name,
                    "seq_id": gene.seq_id,
                    "strain": gene.strain.isolate_name if gene.strain else "Unknown",
                    "assembly": gene.strain.assembly_name if gene.strain else None,
                    "description": gene.description
                }
                for gene in genes
            ]

        except Exception as e:
            logger.error(f"Error searching genes globally: {e}")
            return []

    # helper methods

    def _serialize_gene(self, gene: Gene) -> dict:
        return GeneResponseSchema.model_validate({
            "id": gene.id,
            "seq_id": gene.seq_id,
            "gene_name": gene.gene_name or "N/A",
            "description": gene.description or None,
            "strain_id": gene.strain.id if gene.strain else None,
            "strain": gene.strain.isolate_name if gene.strain else "Unknown",
            "assembly": gene.strain.assembly_name if gene.strain and gene.strain.assembly_name else None,
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
            "annotations": gene.annotations or {}
        })

    async def _fetch_paginated_genes(self, filter_criteria: Q, page: int, per_page: int) -> Tuple[List[Gene], int]:
        start = (page - 1) * per_page
        genes = await sync_to_async(lambda: list(
            Gene.objects.select_related('strain').filter(filter_criteria).order_by('gene_name')[start:start + per_page]
        ))()
        total_results = await sync_to_async(Gene.objects.filter(filter_criteria).count)()
        return genes, total_results
