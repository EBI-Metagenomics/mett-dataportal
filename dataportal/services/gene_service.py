import logging
from typing import Optional, List
from asgiref.sync import sync_to_async
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from dataportal.models import Gene
from dataportal.schemas import GenePaginationSchema
from dataportal.utils import paginate_queryset, fetch_objects

logger = logging.getLogger(__name__)


class GeneService:
    def __init__(self, limit: int = 10):
        self.limit = limit

    async def autocomplete_gene_suggestions(self, query: str, limit: int = None, species_id: Optional[int] = None,
                                            genome_ids: Optional[List[int]] = None):
        try:
            gene_filter = Q(gene_name__icontains=query)

            if species_id:
                gene_filter &= Q(strain__species_id=species_id)
            if genome_ids:
                gene_filter &= Q(strain_id__in=genome_ids)

            genes = await fetch_objects(
                model=Gene,
                filters=gene_filter,
                select_related=['strain'],
                limit=limit or self.limit
            )

            return [
                {"gene_id": gene.id, "gene_name": gene.gene_name, "strain_name": gene.strain.isolate_name}
                for gene in genes
            ]
        except Exception as e:
            logger.error(f"Error fetching gene autocomplete suggestions: {e}")
            return []

    async def get_gene_by_id(self, gene_id: int):
        try:
            return await sync_to_async(lambda: get_object_or_404(Gene, id=gene_id))()
        except Http404:
            raise HttpError(404, f"Gene with id {gene_id} not found")
        except Exception as e:
            logger.error(f"Error fetching gene by ID {gene_id}: {e}")
            raise HttpError(500, f"Internal Server Error: {str(e)}")

    async def get_genes(self, page: int = 1, per_page: int = 10):
        try:
            genes = await fetch_objects(model=Gene, select_related=['strain'])
            return paginate_queryset(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes: {e}")
            return paginate_queryset([], page, per_page)

    async def search_genes(self, query: str = None, genome_id: Optional[int] = None,
                           page: int = 1, per_page: int = 10):
        try:
            filters = Q()
            if query:
                filters &= Q(gene_name__icontains=query) | Q(description__icontains=query)
            if genome_id:
                filters &= Q(strain_id=genome_id)

            genes = await fetch_objects(model=Gene, filters=filters, select_related=['strain'])

            # Serialize the genes to a dictionary format
            serialized_genes = [
                {
                    "id": gene.id,
                    "seq_id": gene.seq_id,
                    "gene_name": gene.gene_name,
                    "description": gene.description,
                    "strain_id": gene.strain.id if gene.strain else None,
                    "strain": gene.strain.isolate_name if gene.strain else None,
                    "assembly": gene.strain.assembly_name if gene.strain else None,
                    "locus_tag": gene.locus_tag,
                    "cog": gene.cog,
                    "kegg": gene.kegg,
                    "pfam": gene.pfam,
                    "interpro": gene.interpro,
                    "dbxref": gene.dbxref,
                    "ec_number": gene.ec_number,
                    "product": gene.product,
                    "start_position": gene.start_position,
                    "end_position": gene.end_position,
                    "annotations": gene.annotations,
                }
                for gene in genes
            ]

            return paginate_queryset(serialized_genes, page, per_page)
        except Exception as e:
            logger.error(f"Error searching genes: {e}")
            return paginate_queryset([], page, per_page)

    async def get_genes_by_genome(self, genome_id: int, page: int = 1, per_page: int = 10):
        try:
            genes = await fetch_objects(
                model=Gene,
                filters=Q(strain_id=genome_id),
                select_related=['strain']
            )

            serialized_results = [
                {
                    "id": gene.id,
                    "seq_id": gene.seq_id,
                    "gene_name": gene.gene_name if gene.gene_name else "N/A",  # Handle None values
                    "description": gene.description if gene.description else None,
                    "locus_tag": gene.locus_tag,
                    "strain": gene.strain.isolate_name,
                    "assembly": gene.strain.assembly_name if gene.strain.assembly_name else None,
                }
                for gene in genes
            ]
            return paginate_queryset(serialized_results, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes for genome ID {genome_id}: {e}")
            return paginate_queryset([], page, per_page)

    async def get_genes_by_multiple_genomes(self, genome_ids: List[int], page: int = 1, per_page: int = 10):
        try:
            genes = await fetch_objects(
                model=Gene,
                filters=Q(strain_id__in=genome_ids),
                select_related=['strain']
            )
            return paginate_queryset(genes, page, per_page)
        except Exception as e:
            logger.error(f"Error fetching genes for genome IDs {genome_ids}: {e}")
            return paginate_queryset([], page, per_page)

    async def get_genes_by_multiple_genomes_and_string(self, genome_ids: str=None, species_id: Optional[int] = None, query: str = None, page: int = 1,
                                                       per_page: int = 10):
        try:
            genome_id_list = [int(gid) for gid in genome_ids.split(",") if gid.strip()] if genome_ids.strip() else []
            genes_query = Gene.objects.select_related('strain')

            if genome_id_list:
                genes_query = genes_query.filter(strain_id__in=genome_id_list)

            if species_id:
                genes_query = genes_query.filter(strain__species_id=species_id)

            if query.strip():
                genes_query = genes_query.filter(gene_name__icontains=query)

            total_results = await sync_to_async(genes_query.count)()
            start = (page - 1) * per_page
            end = start + per_page

            genes = await sync_to_async(lambda: list(genes_query[start:end]))()

            serialized_results = [
                {
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
                }
                for gene in genes
            ]

            return GenePaginationSchema(
                results=serialized_results,
                page_number=page,
                num_pages=(total_results + per_page - 1) // per_page,
                has_previous=page > 1,
                has_next=end < total_results,
                total_results=total_results,
            )
        except HttpError as e:
            raise e
        except ValueError:
            logger.error("Invalid genome ID provided")
            raise HttpError(400, "Invalid genome ID provided")
        except Exception as e:
            logger.error(f"Error in search_genes_by_multiple_genomes_and_string: {e}")
            raise HttpError(500, f"Internal Server Error: {str(e)}")

    async def search_genes_in_strain(self, strain_id: int, query: str, limit: int = 10):
        try:
            gene_filter = Q(strain_id=strain_id, gene_name__icontains=query)
            genes = await fetch_objects(
                model=Gene,
                filters=gene_filter,
                limit=limit
            )
            return [{"gene_name": gene.gene_name, "description": gene.description} for gene in genes]
        except Exception as e:
            logger.error(f"Error searching genes in strain: {e}")
            return []

    async def search_genes_globally(self, query: str, limit: int = 10):
        try:
            gene_filter = Q(gene_name__icontains=query) | Q(description__icontains=query)
            genes = await fetch_objects(
                model=Gene,
                filters=gene_filter,
                limit=limit
            )
            return [
                {
                    "gene_name": gene.gene_name,
                    "seq_id": gene.seq_id,
                    "strain": gene.strain.isolate_name,
                    "assembly": gene.strain.assembly_name,
                    "description": gene.description
                } for gene in genes
            ]
        except Exception as e:
            logger.error(f"Error searching genes globally: {e}")
            return []
