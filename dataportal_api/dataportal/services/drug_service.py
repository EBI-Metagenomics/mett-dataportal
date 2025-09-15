"""
Service for handling drug MIC and metabolism data operations.
"""

import logging
from typing import List, Optional, Dict, Any

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search, Q

from dataportal.models import StrainDocument
from dataportal.schema.drug_schemas import (
    StrainDrugMICResponseSchema,
    StrainDrugMetabolismResponseSchema,
    StrainDrugDataResponseSchema,
    DrugMICSearchQuerySchema,
    DrugMetabolismSearchQuerySchema,
    DrugMICSearchResultSchema,
    DrugMetabolismSearchResultSchema,
    DrugMICDataSchema,
    DrugMetabolismDataSchema,
    DrugMICPaginationSchema,
    DrugMetabolismPaginationSchema,
    DrugSuggestionSchema,
    DrugAutocompleteQuerySchema,
    PaginatedStrainDrugMICResponseSchema,
    PaginatedStrainDrugMetabolismResponseSchema,
    PaginatedStrainDrugDataResponseSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.decorators import log_execution_time
from dataportal.utils.constants import ES_INDEX_STRAIN
from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)


class DrugService(BaseService[StrainDrugMICResponseSchema, Dict[str, Any]]):
    """Service for managing drug data operations."""

    def __init__(self):
        super().__init__(ES_INDEX_STRAIN)

    async def get_by_id(self, id: str) -> Optional[StrainDrugMICResponseSchema]:
        """Retrieve drug data for a specific strain by isolate name."""
        return await self.get_strain_drug_mic(id)

    async def get_all(self, **kwargs) -> List[StrainDrugMICResponseSchema]:
        """Retrieve all strains with drug data (not implemented for drug service)."""
        raise NotImplementedError("get_all not implemented for drug service - use search methods instead")

    async def search(self, query: Dict[str, Any]) -> List[StrainDrugMICResponseSchema]:
        """Search drug data (not implemented for drug service)."""
        raise NotImplementedError("search not implemented for drug service - use specific search methods instead")

    @log_execution_time
    async def get_strain_drug_mic(self, isolate_name: str) -> Optional[StrainDrugMICResponseSchema]:
        """Get drug MIC data for a specific strain."""
        try:
            search = self._create_search().query("term", _id=isolate_name)
            response = await self._execute_search(search)
            
            if not response.hits:
                return None
                
            hit = response.hits[0]
            source = hit.to_dict()
            
            # Extract drug MIC data
            drug_mic_data = []
            for mic_data in source.get("drug_mic", []):
                drug_mic_data.append(DrugMICDataSchema(**mic_data))
            
            return StrainDrugMICResponseSchema(
                isolate_name=source.get("isolate_name", isolate_name),
                species_acronym=source.get("species_acronym"),
                species_scientific_name=source.get("species_scientific_name"),
                drug_mic_data=drug_mic_data
            )
            
        except Exception as e:
            logger.error(f"Error getting strain drug MIC data for {isolate_name}: {e}")
            raise ServiceError(f"Failed to retrieve drug MIC data: {str(e)}")

    @log_execution_time
    async def get_strain_drug_metabolism(self, isolate_name: str) -> Optional[StrainDrugMetabolismResponseSchema]:
        """Get drug metabolism data for a specific strain."""
        try:
            search = self._create_search().query("term", _id=isolate_name)
            response = await self._execute_search(search)
            
            if not response.hits:
                return None
                
            hit = response.hits[0]
            source = hit.to_dict()
            
            # Extract drug metabolism data
            drug_metabolism_data = []
            for metab_data in source.get("drug_metabolism", []):
                drug_metabolism_data.append(DrugMetabolismDataSchema(**metab_data))
            
            return StrainDrugMetabolismResponseSchema(
                isolate_name=source.get("isolate_name", isolate_name),
                species_acronym=source.get("species_acronym"),
                species_scientific_name=source.get("species_scientific_name"),
                drug_metabolism_data=drug_metabolism_data
            )
            
        except Exception as e:
            logger.error(f"Error getting strain drug metabolism data for {isolate_name}: {e}")
            raise ServiceError(f"Failed to retrieve drug metabolism data: {str(e)}")

    @log_execution_time
    async def get_strain_drug_data(self, isolate_name: str) -> Optional[StrainDrugDataResponseSchema]:
        """Get all drug data (MIC + metabolism) for a specific strain."""
        try:
            search = self._create_search().query("term", _id=isolate_name)
            response = await self._execute_search(search)
            
            if not response.hits:
                return None
                
            hit = response.hits[0]
            source = hit.to_dict()
            
            # Extract drug MIC data
            drug_mic_data = []
            for mic_data in source.get("drug_mic", []):
                drug_mic_data.append(DrugMICDataSchema(**mic_data))
            
            # Extract drug metabolism data
            drug_metabolism_data = []
            for metab_data in source.get("drug_metabolism", []):
                drug_metabolism_data.append(DrugMetabolismDataSchema(**metab_data))
            
            return StrainDrugDataResponseSchema(
                isolate_name=source.get("isolate_name", isolate_name),
                species_acronym=source.get("species_acronym"),
                species_scientific_name=source.get("species_scientific_name"),
                drug_mic_data=drug_mic_data,
                drug_metabolism_data=drug_metabolism_data
            )
            
        except Exception as e:
            logger.error(f"Error getting strain drug data for {isolate_name}: {e}")
            raise ServiceError(f"Failed to retrieve drug data: {str(e)}")

    @log_execution_time
    async def get_strain_drug_mic_paginated(self, isolate_name: str, page: int = 1, per_page: int = 20) -> Optional[PaginatedStrainDrugMICResponseSchema]:
        """Get paginated drug MIC data for a specific strain."""
        try:
            search = self._create_search().query("term", _id=isolate_name)
            response = await self._execute_search(search)
            
            if not response.hits:
                return None
                
            hit = response.hits[0]
            source = hit.to_dict()
            
            # Extract all drug MIC data
            all_drug_mic_data = []
            for mic_data in source.get("drug_mic", []):
                all_drug_mic_data.append(DrugMICDataSchema(**mic_data))
            
            # Apply pagination
            total_results = len(all_drug_mic_data)
            total_pages = (total_results + per_page - 1) // per_page
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            paginated_data = all_drug_mic_data[start_index:end_index]
            
            from dataportal.schema.response_schemas import PaginationMetadataSchema
            
            return PaginatedStrainDrugMICResponseSchema(
                isolate_name=source.get("isolate_name", isolate_name),
                species_acronym=source.get("species_acronym"),
                species_scientific_name=source.get("species_scientific_name"),
                drug_mic_data=paginated_data,
                pagination=PaginationMetadataSchema(
                    page_number=page,
                    num_pages=total_pages,
                    has_previous=page > 1,
                    has_next=page < total_pages,
                    total_results=total_results,
                    per_page=per_page
                )
            )
            
        except Exception as e:
            logger.error(f"Error getting paginated strain drug MIC data for {isolate_name}: {e}")
            raise ServiceError(f"Failed to retrieve paginated drug MIC data: {str(e)}")

    @log_execution_time
    async def get_strain_drug_metabolism_paginated(self, isolate_name: str, page: int = 1, per_page: int = 20) -> Optional[PaginatedStrainDrugMetabolismResponseSchema]:
        """Get paginated drug metabolism data for a specific strain."""
        try:
            search = self._create_search().query("term", _id=isolate_name)
            response = await self._execute_search(search)
            
            if not response.hits:
                return None
                
            hit = response.hits[0]
            source = hit.to_dict()
            
            # Extract all drug metabolism data
            all_drug_metabolism_data = []
            for metab_data in source.get("drug_metabolism", []):
                all_drug_metabolism_data.append(DrugMetabolismDataSchema(**metab_data))
            
            # Apply pagination
            total_results = len(all_drug_metabolism_data)
            total_pages = (total_results + per_page - 1) // per_page
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            paginated_data = all_drug_metabolism_data[start_index:end_index]
            
            from dataportal.schema.response_schemas import PaginationMetadataSchema
            
            return PaginatedStrainDrugMetabolismResponseSchema(
                isolate_name=source.get("isolate_name", isolate_name),
                species_acronym=source.get("species_acronym"),
                species_scientific_name=source.get("species_scientific_name"),
                drug_metabolism_data=paginated_data,
                pagination=PaginationMetadataSchema(
                    page_number=page,
                    num_pages=total_pages,
                    has_previous=page > 1,
                    has_next=page < total_pages,
                    total_results=total_results,
                    per_page=per_page
                )
            )
            
        except Exception as e:
            logger.error(f"Error getting paginated strain drug metabolism data for {isolate_name}: {e}")
            raise ServiceError(f"Failed to retrieve paginated drug metabolism data: {str(e)}")

    @log_execution_time
    async def get_strain_drug_data_paginated(self, isolate_name: str, page: int = 1, per_page: int = 20) -> Optional[PaginatedStrainDrugDataResponseSchema]:
        """Get paginated all drug data (MIC + metabolism) for a specific strain."""
        try:
            search = self._create_search().query("term", _id=isolate_name)
            response = await self._execute_search(search)
            
            if not response.hits:
                return None
                
            hit = response.hits[0]
            source = hit.to_dict()
            
            # Extract all drug MIC data
            all_drug_mic_data = []
            for mic_data in source.get("drug_mic", []):
                all_drug_mic_data.append(DrugMICDataSchema(**mic_data))
            
            # Extract all drug metabolism data
            all_drug_metabolism_data = []
            for metab_data in source.get("drug_metabolism", []):
                all_drug_metabolism_data.append(DrugMetabolismDataSchema(**metab_data))
            
            # Apply pagination to both datasets
            total_mic = len(all_drug_mic_data)
            total_metab = len(all_drug_metabolism_data)
            total_results = total_mic + total_metab
            total_pages = (total_results + per_page - 1) // per_page
            
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            
            # Combine and paginate the data
            combined_data = []
            for mic_data in all_drug_mic_data:
                combined_data.append({"type": "mic", "data": mic_data})
            for metab_data in all_drug_metabolism_data:
                combined_data.append({"type": "metabolism", "data": metab_data})
            
            paginated_combined = combined_data[start_index:end_index]
            
            # Separate back into MIC and metabolism
            paginated_mic = [item["data"] for item in paginated_combined if item["type"] == "mic"]
            paginated_metab = [item["data"] for item in paginated_combined if item["type"] == "metabolism"]
            
            from dataportal.schema.response_schemas import PaginationMetadataSchema
            
            return PaginatedStrainDrugDataResponseSchema(
                isolate_name=source.get("isolate_name", isolate_name),
                species_acronym=source.get("species_acronym"),
                species_scientific_name=source.get("species_scientific_name"),
                drug_mic_data=paginated_mic,
                drug_metabolism_data=paginated_metab,
                pagination=PaginationMetadataSchema(
                    page_number=page,
                    num_pages=total_pages,
                    has_previous=page > 1,
                    has_next=page < total_pages,
                    total_results=total_results,
                    per_page=per_page
                )
            )
            
        except Exception as e:
            logger.error(f"Error getting paginated strain drug data for {isolate_name}: {e}")
            raise ServiceError(f"Failed to retrieve paginated drug data: {str(e)}")

    @log_execution_time
    async def search_drug_mic(self, query: DrugMICSearchQuerySchema) -> Dict[str, Any]:
        """Search drug MIC data across strains."""
        try:
            search = self._create_search()
            
            # Build the main query
            main_queries = []
            
            # Build nested query for drug_mic fields
            nested_queries = []
            
            if query.drug_name:
                # Use fuzzy search for drug names
                drug_query = Q("bool", should=[
                    Q("term", drug_mic__drug_name__keyword=query.drug_name.lower()),
                    Q("fuzzy", drug_mic__drug_name__keyword={"value": query.drug_name.lower(), "fuzziness": "AUTO"}),
                    Q("wildcard", drug_mic__drug_name__keyword=f"*{query.drug_name.lower()}*")
                ])
                nested_queries.append(drug_query)
            
            if query.drug_class:
                nested_queries.append(Q("term", drug_mic__drug_class__keyword=query.drug_class))
            
            if query.unit:
                nested_queries.append(Q("term", drug_mic__unit__keyword=query.unit))
            
            if query.experimental_condition:
                nested_queries.append(Q("term", drug_mic__experimental_condition_name__keyword=query.experimental_condition))
            
            if query.min_mic_value is not None:
                nested_queries.append(Q("range", drug_mic__mic_value={"gte": query.min_mic_value}))
            
            if query.max_mic_value is not None:
                nested_queries.append(Q("range", drug_mic__mic_value={"lte": query.max_mic_value}))
            
            # Add nested query if we have any drug_mic filters
            if nested_queries:
                main_queries.append(Q("nested", path="drug_mic", query=Q("bool", must=nested_queries)))
            elif any([query.drug_name, query.drug_class, query.unit, query.experimental_condition, 
                     query.min_mic_value is not None, query.max_mic_value is not None]):
                # If we have any drug_mic related filters but no nested queries were built,
                # we still need to search within drug_mic field
                main_queries.append(Q("nested", path="drug_mic", query=Q("match_all")))
            
            # Add top-level filters
            if query.species_acronym:
                main_queries.append(Q("term", species_acronym=query.species_acronym.lower()))
            
            # Text search - handle nested fields properly
            if query.query:
                # For text search, we need to search within nested drug_mic fields
                text_nested_query = Q("nested", 
                                    path="drug_mic", 
                                    query=Q("multi_match", 
                                           query=query.query,
                                           fields=["drug_mic.drug_name^2", "drug_mic.drug_class"]))
                main_queries.append(text_nested_query)
                
                # Also search top-level fields
                top_level_query = Q("multi_match", 
                                   query=query.query,
                                   fields=["isolate_name", "species_acronym"])
                main_queries.append(top_level_query)
            
            # Apply main query
            if main_queries:
                if query.query:
                    # For text search, use should to allow either nested or top-level matches
                    search = search.query(Q("bool", should=main_queries, minimum_should_match=1))
                else:
                    # For exact filters, use must - all conditions must be met
                    search = search.query(Q("bool", must=main_queries))
            
            # Apply pagination
            from_index = (query.page - 1) * query.per_page
            search = search[from_index:from_index + query.per_page]
            
            # Apply sorting (only on top-level fields to avoid nested field issues)
            if query.sort_by and query.sort_by in ["isolate_name", "species_acronym", "species_scientific_name"]:
                # Use keyword fields for sorting
                sort_field = f"{query.sort_by}.keyword" if query.sort_by == "isolate_name" else query.sort_by
                search = search.sort({sort_field: {"order": query.sort_order}})
            else:
                # Default sort by isolate_name.keyword if no valid sort field specified
                search = search.sort({"isolate_name.keyword": {"order": "asc"}})
            
            response = await self._execute_search(search)
            
            # Process results
            results = []
            for hit in response.hits:
                source = hit.to_dict()
                
                # Extract drug MIC data for each strain
                for mic_data in source.get("drug_mic", []):
                    # Apply additional filters to individual MIC records
                    if query.drug_name and mic_data.get("drug_name") != query.drug_name:
                        continue
                    if query.drug_class and mic_data.get("drug_class") != query.drug_class:
                        continue
                    if query.unit and mic_data.get("unit") != query.unit:
                        continue
                    if query.experimental_condition and mic_data.get("experimental_condition_name") != query.experimental_condition:
                        continue
                    if query.min_mic_value is not None and mic_data.get("mic_value", 0) < query.min_mic_value:
                        continue
                    if query.max_mic_value is not None and mic_data.get("mic_value", float('inf')) > query.max_mic_value:
                        continue
                    
                    results.append(DrugMICSearchResultSchema(
                        isolate_name=source.get("isolate_name", ""),
                        species_acronym=source.get("species_acronym"),
                        species_scientific_name=source.get("species_scientific_name"),
                        drug_name=mic_data.get("drug_name"),
                        drug_class=mic_data.get("drug_class"),
                        mic_value=mic_data.get("mic_value"),
                        unit=mic_data.get("unit"),
                        relation=mic_data.get("relation"),
                        experimental_condition_name=mic_data.get("experimental_condition_name")
                    ))
            
            total_results = len(results)
            total_pages = (total_results + query.per_page - 1) // query.per_page
            
            return DrugMICPaginationSchema(
                results=results,
                page_number=query.page,
                num_pages=total_pages,
                has_previous=query.page > 1,
                has_next=query.page < total_pages,
                total_results=total_results
            )
            
        except Exception as e:
            logger.error(f"Error searching drug MIC data: {e}")
            raise ServiceError(f"Failed to search drug MIC data: {str(e)}")

    @log_execution_time
    async def search_drug_metabolism(self, query: DrugMetabolismSearchQuerySchema) -> Dict[str, Any]:
        """Search drug metabolism data across strains."""
        try:
            search = self._create_search()
            
            # Build the main query
            main_queries = []
            
            # Build nested query for drug_metabolism fields
            nested_queries = []
            
            if query.drug_name:
                # Use fuzzy search for drug names
                drug_query = Q("bool", should=[
                    Q("term", drug_metabolism__drug_name__keyword=query.drug_name.lower()),
                    Q("fuzzy", drug_metabolism__drug_name__keyword={"value": query.drug_name.lower(), "fuzziness": "AUTO"}),
                    Q("wildcard", drug_metabolism__drug_name__keyword=f"*{query.drug_name.lower()}*")
                ])
                nested_queries.append(drug_query)
            
            if query.drug_class:
                nested_queries.append(Q("term", drug_metabolism__drug_class__keyword=query.drug_class))
            
            if query.metabolizer_classification:
                nested_queries.append(Q("term", drug_metabolism__metabolizer_classification__keyword=query.metabolizer_classification))
            
            if query.experimental_condition:
                nested_queries.append(Q("term", drug_metabolism__experimental_condition_name__keyword=query.experimental_condition))
            
            if query.is_significant is not None:
                nested_queries.append(Q("term", drug_metabolism__is_significant=query.is_significant))
            
            if query.min_fdr is not None:
                nested_queries.append(Q("range", drug_metabolism__fdr={"lte": query.min_fdr}))
            
            if query.min_degr_percent is not None:
                nested_queries.append(Q("range", drug_metabolism__degr_percent={"gte": query.min_degr_percent}))
            
            # Add nested query if we have any drug_metabolism filters
            if nested_queries:
                main_queries.append(Q("nested", path="drug_metabolism", query=Q("bool", must=nested_queries)))
            
            # Add top-level filters
            if query.species_acronym:
                main_queries.append(Q("term", species_acronym=query.species_acronym.lower()))
            
            # Text search - handle nested fields properly
            if query.query:
                # For text search, we need to search within nested drug_metabolism fields
                text_nested_query = Q("nested", 
                                    path="drug_metabolism", 
                                    query=Q("multi_match", 
                                           query=query.query,
                                           fields=["drug_metabolism.drug_name^2", "drug_metabolism.drug_class"]))
                main_queries.append(text_nested_query)
                
                # Also search top-level fields
                top_level_query = Q("multi_match", 
                                   query=query.query,
                                   fields=["isolate_name", "species_acronym"])
                main_queries.append(top_level_query)
            
            # Apply main query - use should for text search to allow either nested or top-level matches
            if main_queries:
                if query.query:
                    # For text search, use should to allow either nested or top-level matches
                    search = search.query(Q("bool", should=main_queries, minimum_should_match=1))
                else:
                    # For exact filters, use must
                    search = search.query(Q("bool", must=main_queries))
            
            # Apply pagination
            from_index = (query.page - 1) * query.per_page
            search = search[from_index:from_index + query.per_page]
            
            # Apply sorting (only on top-level fields to avoid nested field issues)
            if query.sort_by and query.sort_by in ["isolate_name", "species_acronym", "species_scientific_name"]:
                # Use keyword fields for sorting
                sort_field = f"{query.sort_by}.keyword" if query.sort_by == "isolate_name" else query.sort_by
                search = search.sort({sort_field: {"order": query.sort_order}})
            else:
                # Default sort by isolate_name.keyword if no valid sort field specified
                search = search.sort({"isolate_name.keyword": {"order": "asc"}})
            
            response = await self._execute_search(search)
            
            # Process results
            results = []
            for hit in response.hits:
                source = hit.to_dict()
                
                # Extract drug metabolism data for each strain
                for metab_data in source.get("drug_metabolism", []):
                    # Apply additional filters to individual metabolism records
                    if query.drug_name and metab_data.get("drug_name") != query.drug_name:
                        continue
                    if query.drug_class and metab_data.get("drug_class") != query.drug_class:
                        continue
                    if query.metabolizer_classification and metab_data.get("metabolizer_classification") != query.metabolizer_classification:
                        continue
                    if query.experimental_condition and metab_data.get("experimental_condition_name") != query.experimental_condition:
                        continue
                    if query.is_significant is not None and metab_data.get("is_significant") != query.is_significant:
                        continue
                    if query.min_fdr is not None and metab_data.get("fdr", 1.0) > query.min_fdr:
                        continue
                    if query.min_degr_percent is not None and metab_data.get("degr_percent", 0) < query.min_degr_percent:
                        continue
                    
                    results.append(DrugMetabolismSearchResultSchema(
                        isolate_name=source.get("isolate_name", ""),
                        species_acronym=source.get("species_acronym"),
                        species_scientific_name=source.get("species_scientific_name"),
                        drug_name=metab_data.get("drug_name"),
                        drug_class=metab_data.get("drug_class"),
                        degr_percent=metab_data.get("degr_percent"),
                        pval=metab_data.get("pval"),
                        fdr=metab_data.get("fdr"),
                        metabolizer_classification=metab_data.get("metabolizer_classification"),
                        is_significant=metab_data.get("is_significant"),
                        experimental_condition_name=metab_data.get("experimental_condition_name")
                    ))
            
            total_results = len(results)
            total_pages = (total_results + query.per_page - 1) // query.per_page
            
            return DrugMetabolismPaginationSchema(
                results=results,
                page_number=query.page,
                num_pages=total_pages,
                has_previous=query.page > 1,
                has_next=query.page < total_pages,
                total_results=total_results
            )
            
        except Exception as e:
            logger.error(f"Error searching drug metabolism data: {e}")
            raise ServiceError(f"Failed to search drug metabolism data: {str(e)}")

    @log_execution_time
    async def get_drug_mic_by_drug(self, drug_name: str, species_acronym: Optional[str] = None) -> List[DrugMICSearchResultSchema]:
        """Get all MIC data for a specific drug."""
        try:
            search = self._create_search()
            
            # Build the main query
            main_queries = []
            
            # Use fuzzy search for drug names to handle partial matches and typos
            drug_query = Q("bool", should=[
                Q("term", drug_mic__drug_name__keyword=drug_name.lower()),
                Q("fuzzy", drug_mic__drug_name__keyword={"value": drug_name.lower(), "fuzziness": "AUTO"}),
                Q("wildcard", drug_mic__drug_name__keyword=f"*{drug_name.lower()}*")
            ])
            main_queries.append(Q("nested", path="drug_mic", query=drug_query))
            
            if species_acronym:
                main_queries.append(Q("term", species_acronym=species_acronym.lower()))
            
            search = search.query(Q("bool", must=main_queries))
            
            # Debug: Log the actual Elasticsearch query
            logger.info(f"Elasticsearch query for drug MIC by drug '{drug_name}' with species '{species_acronym}': {search.to_dict()}")
            
            response = await self._execute_search(search)
            
            results = []
            for hit in response.hits:
                source = hit.to_dict()
                for mic_data in source.get("drug_mic", []):
                    # Check if the drug name matches (case-insensitive partial match)
                    drug_name_lower = drug_name.lower()
                    actual_drug_name = mic_data.get("drug_name", "").lower()
                    if drug_name_lower in actual_drug_name or actual_drug_name in drug_name_lower:
                        results.append(DrugMICSearchResultSchema(
                            isolate_name=source.get("isolate_name", ""),
                            species_acronym=source.get("species_acronym"),
                            species_scientific_name=source.get("species_scientific_name"),
                            drug_name=mic_data.get("drug_name"),
                            drug_class=mic_data.get("drug_class"),
                            mic_value=mic_data.get("mic_value"),
                            unit=mic_data.get("unit"),
                            relation=mic_data.get("relation"),
                            experimental_condition_name=mic_data.get("experimental_condition_name")
                        ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting MIC data for drug {drug_name}: {e}")
            raise ServiceError(f"Failed to retrieve MIC data for drug: {str(e)}")

    @log_execution_time
    async def get_drug_metabolism_by_drug(self, drug_name: str, species_acronym: Optional[str] = None) -> List[DrugMetabolismSearchResultSchema]:
        """Get all metabolism data for a specific drug."""
        try:
            search = self._create_search()
            
            # Build the main query
            main_queries = []
            
            # Use fuzzy search for drug names to handle partial matches and typos
            drug_query = Q("bool", should=[
                Q("term", drug_metabolism__drug_name__keyword=drug_name.lower()),
                Q("fuzzy", drug_metabolism__drug_name__keyword={"value": drug_name.lower(), "fuzziness": "AUTO"}),
                Q("wildcard", drug_metabolism__drug_name__keyword=f"*{drug_name.lower()}*")
            ])
            main_queries.append(Q("nested", path="drug_metabolism", query=drug_query))
            
            if species_acronym:
                main_queries.append(Q("term", species_acronym=species_acronym.lower()))
            
            search = search.query(Q("bool", must=main_queries))
            response = await self._execute_search(search)
            
            results = []
            for hit in response.hits:
                source = hit.to_dict()
                for metab_data in source.get("drug_metabolism", []):
                    # Check if the drug name matches (case-insensitive partial match)
                    drug_name_lower = drug_name.lower()
                    actual_drug_name = metab_data.get("drug_name", "").lower()
                    if drug_name_lower in actual_drug_name or actual_drug_name in drug_name_lower:
                        results.append(DrugMetabolismSearchResultSchema(
                            isolate_name=source.get("isolate_name", ""),
                            species_acronym=source.get("species_acronym"),
                            species_scientific_name=source.get("species_scientific_name"),
                            drug_name=metab_data.get("drug_name"),
                            drug_class=metab_data.get("drug_class"),
                            degr_percent=metab_data.get("degr_percent"),
                            pval=metab_data.get("pval"),
                            fdr=metab_data.get("fdr"),
                            metabolizer_classification=metab_data.get("metabolizer_classification"),
                            is_significant=metab_data.get("is_significant"),
                            experimental_condition_name=metab_data.get("experimental_condition_name")
                        ))
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting metabolism data for drug {drug_name}: {e}")
            raise ServiceError(f"Failed to retrieve metabolism data for drug: {str(e)}")

    @log_execution_time
    async def get_drug_suggestions(self, query: DrugAutocompleteQuerySchema) -> List[DrugSuggestionSchema]:
        """Get drug name suggestions for autocomplete."""
        try:
            # For now, let's use a simpler approach - get all drug names and filter them
            search = self._create_search()
            
            # Build query filters
            filters = []
            
            if query.species_acronym:
                filters.append(Q("term", species_acronym=query.species_acronym.lower()))
            
            # Determine which nested field to search based on data_type
            nested_path = "drug_mic" if query.data_type == "mic" else "drug_metabolism"
            
            # Use wildcard search for drug names
            drug_query = Q("wildcard", **{f"{nested_path}__drug_name__keyword": f"*{query.query.lower()}*"})
            filters.append(Q("nested", path=nested_path, query=drug_query))
            
            # Apply filters
            if filters:
                search = search.query(Q("bool", must=filters))
            
            # Get all matching documents
            search = search[:1000]  # Limit to reasonable number for processing
            
            response = await self._execute_search(search)
            
            # Collect unique drug names with counts
            drug_counts = {}
            drug_classes = {}
            
            for hit in response.hits:
                source = hit.to_dict()
                nested_data = source.get(nested_path, [])
                
                for item in nested_data:
                    drug_name = item.get("drug_name")
                    if drug_name and query.query.lower() in drug_name.lower():
                        if drug_name not in drug_counts:
                            drug_counts[drug_name] = 0
                            drug_classes[drug_name] = item.get("drug_class")
                        drug_counts[drug_name] += 1
            
            # Convert to suggestions
            suggestions = []
            for drug_name, count in sorted(drug_counts.items(), key=lambda x: x[1], reverse=True):
                suggestions.append(DrugSuggestionSchema(
                    drug_name=drug_name,
                    drug_class=drug_classes[drug_name],
                    count=count
                ))
            
            return suggestions[:query.limit]
            
        except Exception as e:
            logger.error(f"Error getting drug suggestions: {e}")
            raise ServiceError(f"Failed to retrieve drug suggestions: {str(e)}")
