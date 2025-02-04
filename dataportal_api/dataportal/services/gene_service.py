import logging
from typing import Optional, List, Tuple, Dict

from asgiref.sync import sync_to_async
from cachetools import LRUCache
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from dataportal.models import Gene, GeneEssentiality
from dataportal.schemas import GenePaginationSchema, GeneResponseSchema
from dataportal.utils.constants import (
    FIELD_ID,
    GENE_FIELD_ID,
    GENE_FIELD_NAME,
    FIELD_SEQ_ID,
    GENE_FIELD_PRODUCT,
    GENE_FIELD_LOCUS_TAG,
    GENE_FIELD_COG,
    GENE_FIELD_KEGG,
    GENE_FIELD_PFAM,
    GENE_FIELD_INTERPRO,
    GENE_FIELD_DBXREF,
    GENE_FIELD_EC_NUMBER,
    GENE_FIELD_START_POS,
    GENE_FIELD_END_POS,
    GENE_FIELD_ANNOTATIONS,
    GENE_SORT_FIELD_STRAIN,
    GENE_SORT_FIELD_STRAIN_ISO,
    GENE_FIELD_DESCRIPTION,
    GENE_ESSENTIALITY_DATA,
    GENE_DEFAULT_SORT_FIELD,
    DEFAULT_SORT,
    DEFAULT_PER_PAGE_CNT,
    SORT_DESC,
    SORT_ASC,
    GENE_ESSENTIALITY,
    GENE_ESSENTIALITY_MEDIA,
    STRAIN_FIELD_ISOLATE_NAME,
    STRAIN_FIELD_ASSEMBLY_NAME,
    GENE_ESSENTIALITY_SOLID,
)
from dataportal.utils.exceptions import (
    GeneNotFoundError,
    ServiceError,
    InvalidGenomeIdError,
)

logger = logging.getLogger(__name__)


class GeneService:
    def __init__(self, limit: int = 10, cache_size: int = 10000):
        self.limit = limit
        self.essentiality_cache = LRUCache(maxsize=cache_size)

    async def load_essentiality_data_by_strain(self) -> Dict[int, Dict[str, Dict[str, List[Dict[str, str]]]]]:
        """Load essentiality data into cache."""
        if self.essentiality_cache:
            return self.essentiality_cache

        logger.info("Loading essentiality data into cache...")
        try:
            fields_to_fetch = [
                f"gene__strain__{FIELD_ID}",
                f"gene__strain__{STRAIN_FIELD_ISOLATE_NAME}",
                f"gene__strain__{STRAIN_FIELD_ASSEMBLY_NAME}",
                f"gene__{FIELD_SEQ_ID}",
                f"gene__{GENE_FIELD_LOCUS_TAG}",
                f"gene__{GENE_FIELD_START_POS}",
                f"gene__{GENE_FIELD_END_POS}",
                GENE_ESSENTIALITY_MEDIA,
                f"{GENE_ESSENTIALITY}__name",
            ]

            essentiality_data = await sync_to_async(list)(
                GeneEssentiality.objects.select_related(GENE_ESSENTIALITY, "gene__strain")
                .values(*fields_to_fetch)
            )

            cache_data = {}
            for entry in essentiality_data:
                strain_id = entry[f"gene__strain__{FIELD_ID}"]
                ref_name = entry[f"gene__{FIELD_SEQ_ID}"]
                locus_tag = entry[f"gene__{GENE_FIELD_LOCUS_TAG}"]
                start = entry[f"gene__{GENE_FIELD_START_POS}"]
                end = entry[f"gene__{GENE_FIELD_END_POS}"]
                media = entry[GENE_ESSENTIALITY_MEDIA]
                essentiality = entry[f"{GENE_ESSENTIALITY}__name"] or "Unknown"

                if strain_id not in cache_data:
                    cache_data[strain_id] = {}

                if ref_name not in cache_data[strain_id]:
                    cache_data[strain_id][ref_name] = {}

                if locus_tag not in cache_data[strain_id][ref_name]:
                    cache_data[strain_id][ref_name][locus_tag] = {
                        GENE_FIELD_LOCUS_TAG: locus_tag,
                        GENE_FIELD_START_POS: start,
                        GENE_FIELD_END_POS: end,
                        GENE_ESSENTIALITY_DATA: [],
                    }

                cache_data[strain_id][ref_name][locus_tag][GENE_ESSENTIALITY_DATA].append(
                    {GENE_ESSENTIALITY_MEDIA: media, GENE_ESSENTIALITY: essentiality}
                )

            self.essentiality_cache.update(cache_data)
            logger.info(f"Loaded {len(essentiality_data)} essentiality records into cache.")
            return cache_data

        except Exception as e:
            logger.error(f"Error loading essentiality data: {e}")
            return {}

    async def get_essentiality_data_by_strain_and_ref(self, strain_id: int, ref_name: str) -> Dict[str, Dict]:
        """Retrieve essentiality data for a given strain and reference name."""
        if not self.essentiality_cache:
            await self.load_essentiality_data_by_strain()

        strain_data = self.essentiality_cache.get(strain_id, {})
        contig_data = strain_data.get(ref_name, {})

        response = {}
        for gene_data in contig_data.values():
            locus_tag = gene_data[GENE_FIELD_LOCUS_TAG]
            response[locus_tag] = {
                GENE_FIELD_LOCUS_TAG: locus_tag,
                "start": gene_data.get(GENE_FIELD_START_POS),
                "end": gene_data.get(GENE_FIELD_END_POS),
                GENE_ESSENTIALITY_DATA: [
                    {
                        GENE_ESSENTIALITY_MEDIA: record[GENE_ESSENTIALITY_MEDIA],
                        GENE_ESSENTIALITY: record[GENE_ESSENTIALITY]
                    }
                    for record in gene_data[GENE_ESSENTIALITY_DATA]
                ]
            }

        return response

    async def autocomplete_gene_suggestions(
            self,
            query: str,
            filter: Optional[str] = None,
            limit: int = None,
            species_id: Optional[int] = None,
            genome_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        try:
            # Build the filter criteria
            gene_filter = (
                    Q(**{f"{GENE_FIELD_NAME}__iexact": query})
                    | Q(**{f"{GENE_FIELD_NAME}__icontains": query})
                    | Q(**{f"{GENE_FIELD_PRODUCT}__icontains": query})
                    | Q(**{f"{GENE_FIELD_LOCUS_TAG}__icontains": query})
                    | Q(**{f"{GENE_FIELD_KEGG}__icontains": query})
                    | Q(**{f"{GENE_FIELD_PFAM}__icontains": query})
                    | Q(**{f"{GENE_FIELD_INTERPRO}__icontains": query})
                    | Q(**{f"{GENE_FIELD_DBXREF}__icontains": query})
            )
            if species_id:
                gene_filter &= Q(strain__species_id=species_id)
            if genome_ids:
                gene_filter &= Q(strain_id__in=genome_ids)

            # Parse additional filters and apply only if strain is a type strain
            parsed_filters = self._parse_filters(filter)
            gene_filter = await self._apply_filters_for_type_strain(
                gene_filter, parsed_filters
            )

            logger.debug(
                f"Query: {query}, Species ID: {species_id}, Genome IDs: {genome_ids}"
            )
            logger.debug(f"Gene Filter: {gene_filter}")

            genes, total_results = await self._fetch_paginated_genes(
                filter_criteria=gene_filter,
                page=1,
                per_page=limit or self.limit,
                sort_field=GENE_FIELD_NAME,
                sort_order=SORT_ASC,
            )

            # Build and return the response
            response = [
                {
                    GENE_FIELD_ID: gene.id,
                    GENE_FIELD_NAME: gene.gene_name,
                    STRAIN_FIELD_ISOLATE_NAME: gene.strain.isolate_name if gene.strain else "Unknown",
                    GENE_FIELD_PRODUCT: gene.product,
                    GENE_FIELD_LOCUS_TAG: gene.locus_tag,
                    GENE_FIELD_KEGG: gene.kegg,
                    GENE_FIELD_PFAM: gene.pfam,
                    GENE_FIELD_INTERPRO: gene.interpro,
                    GENE_FIELD_DBXREF: gene.dbxref,
                }
                for gene in genes
            ]

            logger.debug(f"API Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error fetching gene autocomplete suggestions: {e}")
            return []

    def fetch_gene_by_id(self, gene_id: int):
        return get_object_or_404(
            Gene.objects.select_related("strain").prefetch_related(
                f"essentiality_data__{GENE_ESSENTIALITY}"
            ),
            id=gene_id,
        )

    async def get_gene_by_id(self, gene_id: int) -> GeneResponseSchema:
        try:
            gene = await sync_to_async(self.fetch_gene_by_id, thread_sensitive=False)(
                gene_id
            )
            return self._serialize_gene(gene)
        except Http404:
            raise GeneNotFoundError(gene_id)
        except Exception as e:
            logger.error(f"Error in get_gene_by_id: {e}")
            raise ServiceError(e)

    async def get_all_genes(
            self,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = DEFAULT_SORT,
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
            logger.error(f"Error in get_all_genes: {e}")
            raise ServiceError(e)

    async def search_genes(
            self,
            query: str = None,
            genome_id: Optional[int] = None,
            filter: Optional[str] = None,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = DEFAULT_SORT,
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
            raise ServiceError(e)

    async def get_genes_by_genome(
            self,
            genome_id: int,
            filter: Optional[str] = None,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = SORT_ASC,
    ) -> GenePaginationSchema:
        try:
            gene_filter = Q(strain_id=genome_id)

            # Parse additional filters and apply only if strain is a type strain
            parsed_filters = self._parse_filters(filter)
            gene_filter = await self._apply_filters_for_type_strain(
                gene_filter, parsed_filters
            )

            genes, total_results = await self._fetch_paginated_genes(
                gene_filter, page, per_page, sort_field, sort_order
            )
            serialized_genes = [self._serialize_gene(gene) for gene in genes]
            return self._create_pagination_schema(
                serialized_genes, page, per_page, total_results
            )
        except Exception as e:
            logger.error(f"Error fetching genes for genome ID {genome_id}: {e}")
            raise ServiceError(e)

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
            raise ServiceError(e)

    async def get_genes_by_multiple_genomes_and_string(
            self,
            genome_ids: str = None,
            species_id: Optional[int] = None,
            query: str = None,
            filter: Optional[str] = None,
            page: int = 1,
            per_page: int = DEFAULT_PER_PAGE_CNT,
            sort_field: Optional[str] = None,
            sort_order: Optional[str] = SORT_ASC,
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

            # Parse additional filters and apply only if strain is a type strain
            parsed_filters = self._parse_filters(filter)
            filters = await self._apply_filters_for_type_strain(filters, parsed_filters)

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

            # Valid sorting fields
            valid_sort_fields = {
                GENE_FIELD_NAME: GENE_FIELD_NAME,
                GENE_SORT_FIELD_STRAIN: GENE_SORT_FIELD_STRAIN_ISO,
                GENE_FIELD_DESCRIPTION: GENE_FIELD_DESCRIPTION,
                GENE_FIELD_LOCUS_TAG: GENE_FIELD_LOCUS_TAG,
                GENE_FIELD_PRODUCT: GENE_FIELD_PRODUCT,
                FIELD_SEQ_ID: FIELD_SEQ_ID,
            }

            # Validate and map sort_field
            sort_field_mapped = valid_sort_fields.get(sort_field, GENE_FIELD_NAME)
            if sort_field not in valid_sort_fields:
                logger.warning(
                    f"Invalid sort_field '{sort_field}', defaulting to '{GENE_FIELD_NAME}'"
                )
                sort_field_mapped = GENE_FIELD_NAME

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
            raise InvalidGenomeIdError(genome_ids)
        except Exception as e:
            logger.error(f"Error in get_genes_by_multiple_genomes_and_string: {e}")
            raise ServiceError(e)

    # helper methods

    def _serialize_gene_essentiality(self, gene_essentiality):
        return {
            GENE_ESSENTIALITY_MEDIA: gene_essentiality.media,
            GENE_ESSENTIALITY: (
                gene_essentiality.essentiality.name
                if gene_essentiality.essentiality
                else None
            ),
        }

    def _serialize_gene(self, gene: Gene) -> dict:
        return GeneResponseSchema.model_validate(
            {
                FIELD_ID: gene.id,
                FIELD_SEQ_ID: gene.seq_id,
                GENE_FIELD_NAME: gene.gene_name or "N/A",
                GENE_FIELD_DESCRIPTION: gene.description or None,
                GENE_SORT_FIELD_STRAIN: {
                    FIELD_ID: gene.strain.id if gene.strain else None,
                    STRAIN_FIELD_ISOLATE_NAME: gene.strain.isolate_name if gene.strain else "Unknown",
                    STRAIN_FIELD_ASSEMBLY_NAME: gene.strain.assembly_name if gene.strain else None,
                },
                GENE_FIELD_LOCUS_TAG: gene.locus_tag or None,
                GENE_FIELD_COG: gene.cog or None,
                GENE_FIELD_KEGG: gene.kegg or None,
                GENE_FIELD_PFAM: gene.pfam or None,
                GENE_FIELD_INTERPRO: gene.interpro or None,
                GENE_FIELD_DBXREF: gene.dbxref or None,
                GENE_FIELD_EC_NUMBER: gene.ec_number or None,
                GENE_FIELD_PRODUCT: gene.product or None,
                GENE_FIELD_START_POS: gene.start_position or None,
                GENE_FIELD_END_POS: gene.end_position or None,
                GENE_FIELD_ANNOTATIONS: gene.annotations or {},
                GENE_ESSENTIALITY_DATA: [
                    self._serialize_gene_essentiality(ge)
                    for ge in gene.essentiality_data.all()
                ],
            }
        )

    def _parse_filters(self, filter_str: Optional[str]) -> Dict[str, List[str]]:
        if not filter_str:
            return {}

        filters = {}
        try:
            # Match key:values where values can contain commas
            key, values_str = filter_str.split(":", 1)
            key = key.strip()
            values = [v.strip() for v in values_str.split(",")]
            filters[key] = values
        except ValueError:
            logger.error(f"Invalid filter format: {filter_str}")
            raise ServiceError(
                "Invalid filter format. Use 'key:value' pairs separated by commas."
            )

        logger.debug(f"Parsed filters: {filters}")
        return filters

    async def _apply_essentiality_filter(
            self, query: Q, essentiality_values: List[str]
    ) -> Q:
        from dataportal.models import EssentialityTag

        try:
            tags = await sync_to_async(list)(
                EssentialityTag.objects.filter(name__in=essentiality_values)
            )
            if tags:
                return query & Q(
                    essentiality_data__essentiality__in=tags,
                    essentiality_data__media=GENE_ESSENTIALITY_SOLID,
                )
            else:
                logger.error(
                    f"No matching essentiality tags found for values: {essentiality_values}"
                )
                return query
        except Exception as e:
            logger.error(f"Error applying essentiality filter: {e}")
            return query

    async def _apply_filters_for_type_strain(
            self, query: Q, filters: Dict[str, list]
    ) -> Q:
        if filters:
            query &= Q(strain__type_strain=True)

            for key, values in filters.items():
                if key == GENE_ESSENTIALITY:
                    query = await self._apply_essentiality_filter(query, values)
                else:
                    for value in values:
                        query &= Q(**{f"{key}__icontains": value})

        return query

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
            sort_order: Optional[str] = DEFAULT_SORT,
    ) -> Tuple[List[Gene], int]:
        start = (page - 1) * per_page
        order_prefix = "-" if sort_order == SORT_DESC else ""
        sort_by = f"{order_prefix}{sort_field or GENE_DEFAULT_SORT_FIELD}"

        try:
            logger.debug(f"Filter criteria: {filter_criteria}")
            logger.debug(f"Sorting by: {sort_by}")
            logger.debug(f"Pagination: start={start}, end={start + per_page}")

            # Fetch paginated gene list
            genes = await sync_to_async(
                lambda: list(
                    Gene.objects.select_related(GENE_SORT_FIELD_STRAIN)
                    .prefetch_related(f"essentiality_data__{GENE_ESSENTIALITY}")
                    .filter(filter_criteria)
                    .order_by(sort_by)[start: start + per_page]
                )
            )()

            # Count total results
            total_results = await sync_to_async(
                lambda: Gene.objects.filter(filter_criteria).count()
            )()

            logger.debug(f"Fetched genes: {[gene.gene_name for gene in genes]}")
            logger.debug(f"Total matching genes: {total_results}")

            return genes, total_results

        except Exception as e:
            logger.error(f"Error fetching paginated genes: {str(e)}")
            raise ServiceError(e)
