"""
Service for Pooled TTP (Thermal Proteome Profiling) data operations.
"""

import logging
from typing import List, Dict, Any, Tuple

from elasticsearch_dsl import Search, Q, connections

from dataportal.schema.ttp_schemas import (
    TTPInteractionQuerySchema,
    TTPGeneInteractionsQuerySchema,
    TTPCompoundInteractionsQuerySchema,
    TTPHitAnalysisQuerySchema,
    TTPPoolAnalysisQuerySchema,
    TTPDownloadQuerySchema,
    TTPInteractionSchema,
    TTPGeneInteractionSchema,
    TTPCompoundInteractionSchema,
    TTPInteractionResponseSchema,
    TTPHitSummarySchema,
    TTPPoolSummarySchema,
    TTPMetadataSchema,
)
from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)


class TTPService:
    """Service for handling TTP interaction data operations."""

    def __init__(self, index_name: str = "feature_index"):
        self.index_name = index_name
        self._es_client = None

    @property
    def es_client(self):
        """Lazy initialization of Elasticsearch client."""
        if self._es_client is None:
            self._es_client = connections.get_connection()
        return self._es_client

    def _build_base_search(self) -> Search:
        """Build base search query for TTP interactions."""
        search = Search(using=self.es_client, index=self.index_name)
        
        # Only return core fields we need for TTP interactions
        search = search.source([
            "locus_tag",
            "gene_name", 
            "product",
            "uniprot_id",
            "species_acronym",
            "isolate_name",
            "protein_compound"
        ])
        
        logger.debug(f"Built base search for index: {self.index_name}")
        return search

    def _build_interaction_query(self, query_params: Dict[str, Any]) -> Q:
        """Build Elasticsearch query for TTP interactions."""
        query = Q("bool", must=[])

        logger.debug(f"Building interaction query with params: {query_params}")

        # Free text search
        if query_params.get("query"):
            search_query = query_params["query"]
            
            # Use should clauses for flexible search - either gene fields OR compound field
            search_should = Q("bool", should=[
                Q("multi_match",
                  query=search_query,
                  fields=["locus_tag^2", "gene_name^2", "product"]),
                Q("nested",
                  path="protein_compound",
                  query=Q("term", protein_compound__compound=search_query))
            ], minimum_should_match=1)
            
            query.must.append(search_should)
            
            logger.debug(f"Added free text search filter for: {search_query}")

        # Locus tag filter
        if query_params.get("locus_tag"):
            query.must.append(Q("term", locus_tag__keyword=query_params["locus_tag"]))
            logger.debug(f"Added locus_tag filter (keyword): {query_params['locus_tag']}")

        # Species filter
        if query_params.get("species_acronym"):
            query.must.append(Q("term", species_acronym=query_params["species_acronym"]))
            logger.debug(f"Added species_acronym filter: {query_params['species_acronym']}")

        # Isolate filter
        if query_params.get("isolate_name"):
            query.must.append(Q("term", isolate_name=query_params["isolate_name"]))
            logger.debug(f"Added isolate_name filter: {query_params['isolate_name']}")

        # Compound filter
        if query_params.get("compound"):
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("term", protein_compound__compound=query_params["compound"]))
            )
            logger.debug(f"Added compound filter: {query_params['compound']}")

        # Hit calling filter
        if query_params.get("hit_calling") is not None:
            # Ensure boolean is serialized as lowercase for ES
            hit_calling_value = bool(query_params["hit_calling"])
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("term", protein_compound__hit_calling=hit_calling_value))
            )
            logger.debug(f"Added hit_calling filter: {hit_calling_value}")

        # Pool filters - both poolA and poolB must be in the same interaction
        if query_params.get("poolA") and query_params.get("poolB"):
            # Both pools specified - must be in same interaction
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("bool", must=[
                      Q("term", protein_compound__poolA=query_params["poolA"]),
                      Q("term", protein_compound__poolB=query_params["poolB"])
                  ]))
            )
        elif query_params.get("poolA"):
            # Only poolA specified
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("term", protein_compound__poolA=query_params["poolA"]))
            )
        elif query_params.get("poolB"):
            # Only poolB specified
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("term", protein_compound__poolB=query_params["poolB"]))
            )

        # Assay filter
        if query_params.get("assay"):
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("term", protein_compound__assay=query_params["assay"]))
            )

        # Score range filters
        if query_params.get("min_ttp_score") is not None:
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("range", protein_compound__ttp_score={"gte": query_params["min_ttp_score"]}))
            )

        if query_params.get("max_ttp_score") is not None:
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("range", protein_compound__ttp_score={"lte": query_params["max_ttp_score"]}))
            )

        # FDR range filters
        if query_params.get("min_fdr") is not None:
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("range", protein_compound__fdr={"gte": query_params["min_fdr"]}))
            )

        if query_params.get("max_fdr") is not None:
            query.must.append(
                Q("nested",
                  path="protein_compound",
                  query=Q("range", protein_compound__fdr={"lte": query_params["max_fdr"]}))
            )

        logger.debug(f"Final query built with {len(query.must)} must clauses")
        return query

    async def search_interactions(self, query_schema: TTPInteractionQuerySchema) -> TTPInteractionResponseSchema:
        """Search TTP interactions with basic query."""
        try:
            search = self._build_base_search()
            
            # For search, always filter for documents that have protein_compound interactions
            search = search.filter(
                Q("nested",
                  path="protein_compound",
                  query=Q("exists", field="protein_compound.compound"),
                  score_mode="none")
            )

            # Build query
            query_params = query_schema.dict()
            query = self._build_interaction_query(query_params)
            search = search.query(query)

            # Pagination
            page = query_schema.page
            per_page = query_schema.per_page
            search = search[(page - 1) * per_page:page * per_page]

            # Sorting
            if query_schema.sort_field:
                if query_schema.sort_field in ["ttp_score", "fdr", "compound", "hit_calling"]:
                    # For nested fields, use nested sort
                    search = search.sort({
                        f"protein_compound.{query_schema.sort_field}": {
                            "order": query_schema.sort_order,
                            "nested": {
                                "path": "protein_compound"
                            }
                        }
                    })
                else:
                    # For non-nested fields, use regular sort
                    search = search.sort({query_schema.sort_field: {"order": query_schema.sort_order}})

            # Log the final Elasticsearch query
            logger.info(f"TTP Search ES Query: {search.to_dict()}")
            
            # Execute search
            response = search.execute()
            
            logger.info(f"TTP Search Response: {response.hits.total} total hits, {len(response)} returned")

            # Process results and group by locus_tag
            gene_interactions = {}
            for hit in response:
                locus_tag = hit.locus_tag
                
                # Initialize gene data if not seen before
                if locus_tag not in gene_interactions:
                    gene_interactions[locus_tag] = {
                        'locus_tag': locus_tag,
                        'gene_name': getattr(hit, 'gene_name', None),
                        'product': getattr(hit, 'product', None),
                        'uniprot_id': getattr(hit, 'uniprot_id', None),
                        'species_acronym': getattr(hit, 'species_acronym', None),
                        'isolate_name': getattr(hit, 'isolate_name', None),
                        'compounds': []
                    }
                
                # Add compound interactions
                for pc in hit.protein_compound:
                    compound_interaction = TTPCompoundInteractionSchema(
                        compound=getattr(pc, 'compound', None),
                        ttp_score=getattr(pc, 'ttp_score', None),
                        fdr=getattr(pc, 'fdr', None),
                        hit_calling=getattr(pc, 'hit_calling', False),
                        notes=getattr(pc, 'notes', None),
                        assay=getattr(pc, 'assay', None),
                        poolA=getattr(pc, 'poolA', None),
                        poolB=getattr(pc, 'poolB', None),
                        experimental_condition=getattr(pc, 'experimental_condition', None)
                    )
                    gene_interactions[locus_tag]['compounds'].append(compound_interaction)
            
            # Convert to list of TTPGeneInteractionSchema
            interactions = [
                TTPGeneInteractionSchema(**gene_data) 
                for gene_data in gene_interactions.values()
            ]

            total_hits = response.hits.total.value if hasattr(response.hits.total, 'value') else response.hits.total
            total_pages = (total_hits + per_page - 1) // per_page
            
            return TTPInteractionResponseSchema(
                results=interactions,
                page_number=page,
                num_pages=total_pages,
                has_previous=page > 1,
                has_next=page < total_pages,
                total_results=total_hits
            )

        except Exception as e:
            logger.error(f"Error searching TTP interactions: {str(e)}")
            raise ServiceError(f"Failed to search TTP interactions: {str(e)}")


    async def get_gene_interactions(self, query_schema: TTPGeneInteractionsQuerySchema) -> TTPGeneInteractionSchema:
        """Get all interactions for a specific gene."""
        try:
            search = self._build_base_search()

            # Build query
            query_params = query_schema.dict()
            logger.info(f"TTP Gene Interactions Query Params: {query_params}")

            query = self._build_interaction_query(query_params)
            search = search.query(query)

            # Log the Elasticsearch query
            logger.info(f"TTP Gene Interactions ES Query: {search.to_dict()}")

            # Sorting
            if query_schema.sort_field:
                if query_schema.sort_field in ["ttp_score", "fdr", "compound", "hit_calling"]:
                    # For nested fields, use nested sort
                    search = search.sort({
                        f"protein_compound.{query_schema.sort_field}": {
                            "order": query_schema.sort_order,
                            "nested": {
                                "path": "protein_compound"
                            }
                        }
                    })
                else:
                    # For non-nested fields, use regular sort
                    search = search.sort({query_schema.sort_field: {"order": query_schema.sort_order}})

            # Execute search
            response = search.execute()
            logger.info(
                f"TTP Gene Interactions ES Response: {response.hits.total} total hits, {len(response)} returned")
            
            # Debug: Let's also check if there are any documents with protein_compound at all
            debug_search = self._build_base_search()
            debug_response = debug_search.execute()
            logger.info(f"Debug - Total docs with protein_compound: {debug_response.hits.total}")
            
            # Debug: Check if the locus_tag exists at all
            locus_search = Search(using=self.es_client, index=self.index_name).filter(
                "term", locus_tag="PV_ATCC8482_00051"
            )
            locus_response = locus_search.execute()
            logger.info(f"Debug - Total docs with locus_tag=PV_ATCC8482_00051: {locus_response.hits.total}")

            # Process results - group by locus_tag (should be only one gene)
            gene_interactions = {}
            for hit in response:
                locus_tag = hit.locus_tag
                logger.debug(
                    f"Processing hit: locus_tag={locus_tag}, protein_compound_count={len(hit.protein_compound) if hasattr(hit, 'protein_compound') else 0}")
                
                # Initialize gene data if not seen before
                if locus_tag not in gene_interactions:
                    gene_interactions[locus_tag] = {
                        'locus_tag': locus_tag,
                        'gene_name': getattr(hit, 'gene_name', None),
                        'product': getattr(hit, 'product', None),
                        'uniprot_id': getattr(hit, 'uniprot_id', None),
                        'species_acronym': getattr(hit, 'species_acronym', None),
                        'isolate_name': getattr(hit, 'isolate_name', None),
                        'compounds': []
                    }
                
                # Add compound interactions
                for pc in hit.protein_compound:
                    compound_interaction = TTPCompoundInteractionSchema(
                        compound=getattr(pc, 'compound', None),
                        ttp_score=getattr(pc, 'ttp_score', None),
                        fdr=getattr(pc, 'fdr', None),
                        hit_calling=getattr(pc, 'hit_calling', False),
                        notes=getattr(pc, 'notes', None),
                        assay=getattr(pc, 'assay', None),
                        poolA=getattr(pc, 'poolA', None),
                        poolB=getattr(pc, 'poolB', None),
                        experimental_condition=getattr(pc, 'experimental_condition', None)
                    )
                    gene_interactions[locus_tag]['compounds'].append(compound_interaction)
                    logger.debug(
                        f"Created interaction: compound={compound_interaction.compound}, hit_calling={compound_interaction.hit_calling}")

            # Return the gene interaction (should be only one)
            if gene_interactions:
                gene_data = list(gene_interactions.values())[0]
                logger.info(f"TTP Gene Interactions Final Result: {len(gene_data['compounds'])} compounds returned")
                return TTPGeneInteractionSchema(**gene_data)
            else:
                # Return empty gene interaction if no results
                return TTPGeneInteractionSchema(
                    locus_tag=query_schema.locus_tag,
                    gene_name=None,
                    product=None,
                    uniprot_id=None,
                    species_acronym=None,
                    isolate_name=None,
                    compounds=[]
                )

        except Exception as e:
            logger.error(f"Error getting gene interactions: {str(e)}")
            raise ServiceError(f"Failed to get gene interactions: {str(e)}")

    async def get_compound_interactions(self, query_schema: TTPCompoundInteractionsQuerySchema) -> List[TTPGeneInteractionSchema]:
        """Get all interactions for a specific compound."""
        try:
            search = self._build_base_search()

            # Build query
            query_params = query_schema.dict()
            query = self._build_interaction_query(query_params)
            search = search.query(query)

            # Sorting
            if query_schema.sort_field:
                if query_schema.sort_field in ["ttp_score", "fdr", "compound", "hit_calling"]:
                    # For nested fields, use nested sort
                    search = search.sort({
                        f"protein_compound.{query_schema.sort_field}": {
                            "order": query_schema.sort_order,
                            "nested": {
                                "path": "protein_compound"
                            }
                        }
                    })
                else:
                    # For non-nested fields, use regular sort
                    search = search.sort({query_schema.sort_field: {"order": query_schema.sort_order}})

            # Log the final Elasticsearch query
            logger.info(f"TTP Compound Interactions ES Query: {search.to_dict()}")
            
            # Execute search
            response = search.execute()
            
            logger.info(f"TTP Compound Interactions Response: {response.hits.total} total hits, {len(response)} returned")

            # Process results and group by locus_tag
            gene_interactions = {}
            for hit in response:
                locus_tag = hit.locus_tag
                
                # Initialize gene data if not seen before
                if locus_tag not in gene_interactions:
                    gene_interactions[locus_tag] = {
                        'locus_tag': locus_tag,
                        'gene_name': getattr(hit, 'gene_name', None),
                        'product': getattr(hit, 'product', None),
                        'uniprot_id': getattr(hit, 'uniprot_id', None),
                        'species_acronym': getattr(hit, 'species_acronym', None),
                        'isolate_name': getattr(hit, 'isolate_name', None),
                        'compounds': []
                    }
                
                # Add compound interactions
                for pc in hit.protein_compound:
                    compound_interaction = TTPCompoundInteractionSchema(
                        compound=getattr(pc, 'compound', None),
                        ttp_score=getattr(pc, 'ttp_score', None),
                        fdr=getattr(pc, 'fdr', None),
                        hit_calling=getattr(pc, 'hit_calling', False),
                        notes=getattr(pc, 'notes', None),
                        assay=getattr(pc, 'assay', None),
                        poolA=getattr(pc, 'poolA', None),
                        poolB=getattr(pc, 'poolB', None),
                        experimental_condition=getattr(pc, 'experimental_condition', None)
                    )
                    gene_interactions[locus_tag]['compounds'].append(compound_interaction)

            # Convert to list of TTPGeneInteractionSchema
            interactions = [
                TTPGeneInteractionSchema(**gene_data) 
                for gene_data in gene_interactions.values()
            ]
            
            return interactions

        except Exception as e:
            logger.error(f"Error getting compound interactions: {str(e)}")
            raise ServiceError(f"Failed to get compound interactions: {str(e)}")

    async def get_hit_analysis(self, query_schema: TTPHitAnalysisQuerySchema) -> Tuple[
        List[TTPGeneInteractionSchema], TTPHitSummarySchema]:
        """Get hit analysis - significant interactions."""
        try:
            search = self._build_base_search()

            # Build query
            query_params = query_schema.dict()
            query = self._build_interaction_query(query_params)
            search = search.query(query)

            # Pagination
            page = query_schema.page
            per_page = query_schema.per_page
            search = search[(page - 1) * per_page:page * per_page]

            # Execute search
            response = search.execute()

            # Process results and group by locus_tag
            gene_interactions = {}
            total_interactions = 0
            total_hits = 0
            ttp_scores = []

            for hit in response:
                locus_tag = hit.locus_tag
                
                # Initialize gene data if not seen before
                if locus_tag not in gene_interactions:
                    gene_interactions[locus_tag] = {
                        'locus_tag': locus_tag,
                        'gene_name': getattr(hit, 'gene_name', None),
                        'product': getattr(hit, 'product', None),
                        'uniprot_id': getattr(hit, 'uniprot_id', None),
                        'species_acronym': getattr(hit, 'species_acronym', None),
                        'isolate_name': getattr(hit, 'isolate_name', None),
                        'compounds': []
                    }
                
                # Add compound interactions
                for pc in hit.protein_compound:
                    if getattr(pc, 'hit_calling', False):
                        total_hits += 1

                    if getattr(pc, 'ttp_score', None) is not None:
                        ttp_scores.append(getattr(pc, 'ttp_score', 0))

                    total_interactions += 1

                    compound_interaction = TTPCompoundInteractionSchema(
                        compound=getattr(pc, 'compound', None),
                        ttp_score=getattr(pc, 'ttp_score', None),
                        fdr=getattr(pc, 'fdr', None),
                        hit_calling=getattr(pc, 'hit_calling', False),
                        notes=getattr(pc, 'notes', None),
                        assay=getattr(pc, 'assay', None),
                        poolA=getattr(pc, 'poolA', None),
                        poolB=getattr(pc, 'poolB', None),
                        experimental_condition=getattr(pc, 'experimental_condition', None)
                    )
                    gene_interactions[locus_tag]['compounds'].append(compound_interaction)

            # Convert to list of TTPGeneInteractionSchema
            interactions = [
                TTPGeneInteractionSchema(**gene_data) 
                for gene_data in gene_interactions.values()
            ]

            # Calculate summary statistics
            hit_rate = total_hits / total_interactions if total_interactions > 0 else 0
            avg_ttp_score = sum(ttp_scores) / len(ttp_scores) if ttp_scores else None
            median_ttp_score = sorted(ttp_scores)[len(ttp_scores) // 2] if ttp_scores else None

            summary = TTPHitSummarySchema(
                total_interactions=total_interactions,
                total_hits=total_hits,
                hit_rate=hit_rate,
                avg_ttp_score=avg_ttp_score,
                median_ttp_score=median_ttp_score,
                min_ttp_score=min(ttp_scores) if ttp_scores else None,
                max_ttp_score=max(ttp_scores) if ttp_scores else None
            )

            return interactions, summary

        except Exception as e:
            logger.error(f"Error getting hit analysis: {str(e)}")
            raise ServiceError(f"Failed to get hit analysis: {str(e)}")

    async def get_pool_analysis(self, query_schema: TTPPoolAnalysisQuerySchema) -> TTPPoolSummarySchema:
        """Get pool-based analysis summary."""
        try:
            search = self._build_base_search()

            # Build query
            query_params = query_schema.dict()
            query = self._build_interaction_query(query_params)
            search = search.query(query)

            # Log the final Elasticsearch query
            logger.info(f"TTP Pool Analysis ES Query: {search.to_dict()}")
            
            # Execute search
            response = search.execute()
            
            logger.info(f"TTP Pool Analysis Response: {response.hits.total} total hits, {len(response)} returned")

            # Process results
            total_interactions = 0
            total_hits = 0
            compounds = set()
            compound_hits = {}

            for hit in response:
                for pc in hit.protein_compound:
                    # Only count interactions that match the specific pool combination
                    pc_poolA = getattr(pc, 'poolA', None)
                    pc_poolB = getattr(pc, 'poolB', None)
                    
                    # Check if this interaction matches the requested pool combination
                    if (query_schema.poolA and query_schema.poolB and 
                        pc_poolA == query_schema.poolA and pc_poolB == query_schema.poolB):
                        total_interactions += 1
                        compound = getattr(pc, 'compound', None)
                        if compound:
                            compounds.add(compound)
                            if getattr(pc, 'hit_calling', False):
                                total_hits += 1
                                compound_hits[compound] = compound_hits.get(compound, 0) + 1
                    elif (query_schema.poolA and not query_schema.poolB and pc_poolA == query_schema.poolA):
                        # Only poolA specified
                        total_interactions += 1
                        compound = getattr(pc, 'compound', None)
                        if compound:
                            compounds.add(compound)
                            if getattr(pc, 'hit_calling', False):
                                total_hits += 1
                                compound_hits[compound] = compound_hits.get(compound, 0) + 1
                    elif (query_schema.poolB and not query_schema.poolA and pc_poolB == query_schema.poolB):
                        # Only poolB specified
                        total_interactions += 1
                        compound = getattr(pc, 'compound', None)
                        if compound:
                            compounds.add(compound)
                            if getattr(pc, 'hit_calling', False):
                                total_hits += 1
                                compound_hits[compound] = compound_hits.get(compound, 0) + 1

            # Calculate hit rate
            hit_rate = total_hits / total_interactions if total_interactions > 0 else 0

            # Get top compounds by hit count
            top_compounds = sorted(compound_hits.items(), key=lambda x: x[1], reverse=True)[:10]
            top_compounds = [{"compound": compound, "hit_count": count} for compound, count in top_compounds]

            return TTPPoolSummarySchema(
                poolA=query_schema.poolA,
                poolB=query_schema.poolB,
                total_interactions=total_interactions,
                total_hits=total_hits,
                hit_rate=hit_rate,
                compounds=list(compounds),
                top_compounds=top_compounds
            )

        except Exception as e:
            logger.error(f"Error getting pool analysis: {str(e)}")
            raise ServiceError(f"Failed to get pool analysis: {str(e)}")

    async def get_metadata(self) -> TTPMetadataSchema:
        """Get TTP dataset metadata."""
        try:
            # For metadata, we need all fields, not just the selected ones
            search = Search(using=self.es_client, index=self.index_name)
            
            # Filter for documents that have protein_compound interactions
            search = search.filter(
                Q("nested",
                  path="protein_compound",
                  query=Q("exists", field="protein_compound.compound"),
                  score_mode="none")
            )
            
            # large size to get all results for metadata calculation
            search = search[0:100000]  # Get up to 100k documents

            # Get total counts
            total_response = search.execute()
            total_interactions = 0
            total_genes = set()
            total_compounds = set()
            total_hits = 0
            ttp_scores = []
            pools = set()

            for hit in total_response:
                locus_tag = getattr(hit, 'locus_tag', None)
                if locus_tag:
                    total_genes.add(locus_tag)
                protein_compound = getattr(hit, 'protein_compound', [])
                for pc in protein_compound:
                    total_interactions += 1
                    compound = getattr(pc, 'compound', None)
                    if compound:
                        total_compounds.add(compound)
                    if getattr(pc, 'hit_calling', False):
                        total_hits += 1
                    if getattr(pc, 'ttp_score', None) is not None:
                        ttp_scores.append(getattr(pc, 'ttp_score', 0))
                    if getattr(pc, 'poolA', None):
                        pools.add(getattr(pc, 'poolA', ''))
                    if getattr(pc, 'poolB', None):
                        pools.add(getattr(pc, 'poolB', ''))

            # Calculate statistics
            hit_rate = total_hits / total_interactions if total_interactions > 0 else 0
            score_range = {
                "min": min(ttp_scores) if ttp_scores else 0,
                "max": max(ttp_scores) if ttp_scores else 0,
                "avg": sum(ttp_scores) / len(ttp_scores) if ttp_scores else 0
            }

            return TTPMetadataSchema(
                total_interactions=total_interactions,
                total_genes=len(total_genes),
                total_compounds=len(total_compounds),
                total_hits=total_hits,
                hit_rate=hit_rate,
                available_pools=sorted(list(pools)),
                available_compounds=sorted(list(total_compounds)),
                score_range=score_range
            )

        except Exception as e:
            logger.error(f"Error getting TTP metadata: {str(e)}")
            raise ServiceError(f"Failed to get TTP metadata: {str(e)}")


    async def download_data(self, query_schema: TTPDownloadQuerySchema) -> str:
        """Download TTP data in CSV/TSV format."""
        try:
            search = self._build_base_search()

            # Build query
            query_params = query_schema.dict()
            query = self._build_interaction_query(query_params)
            search = search.query(query)

            # Execute search
            response = search.execute()

            # Process results
            interactions = []
            for hit in response:
                for pc in hit.protein_compound:
                    interaction = {
                        "locus_tag": hit.locus_tag,
                        "gene_name": getattr(hit, 'gene_name', ''),
                        "product": getattr(hit, 'product', ''),
                        "uniprot_id": getattr(hit, 'uniprot_id', ''),
                        "species_acronym": getattr(hit, 'species_acronym', ''),
                        "isolate_name": getattr(hit, 'isolate_name', ''),
                        "compound": getattr(pc, 'compound', ''),
                        "ttp_score": getattr(pc, 'ttp_score', ''),
                        "fdr": getattr(pc, 'fdr', ''),
                        "hit_calling": getattr(pc, 'hit_calling', False),
                        "notes": getattr(pc, 'notes', ''),
                        "assay": getattr(pc, 'assay', ''),
                        "poolA": getattr(pc, 'poolA', ''),
                        "poolB": getattr(pc, 'poolB', ''),
                        "experimental_condition": getattr(pc, 'experimental_condition', '')
                    }
                    interactions.append(interaction)

            # Convert to CSV/TSV
            import csv
            import io

            output = io.StringIO()
            delimiter = '\t' if query_schema.format == 'tsv' else ','

            if interactions:
                writer = csv.DictWriter(output, fieldnames=interactions[0].keys(), delimiter=delimiter)
                writer.writeheader()
                writer.writerows(interactions)

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error downloading TTP data: {str(e)}")
            raise ServiceError(f"Failed to download TTP data: {str(e)}")
