import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from dataportal.schema.nl_schemas import METT_GENE_QUERY_SCHEMA
from dataportal.schema.gene_schemas import NaturalLanguageGeneQuery, GenePaginationSchema
from dataportal.services.gene_service import GeneService
from dataportal.schema.gene_schemas import GeneFacetedSearchQuerySchema, GeneAdvancedSearchQuerySchema, GeneSearchQuerySchema

SYSTEM_PROMPT = """
You are an intelligent bioinformatics data portal assistant that converts natural language queries into structured API requests.

Your job is to interpret user requests and convert them into valid JSON objects for querying gene data.

IMPORTANT: When referencing a species, you MUST use the species_acronym field with the correct acronym:
- "Bacteroides uniformis" or "B. uniformis" → species_acronym: "BU"
- "Phocaeicola vulgatus" or "P. vulgatus" → species_acronym: "PV"

⚠️ Output ONLY a valid JSON object. Do not include any explanation, prefix, or suffix.
Do NOT say anything like "Sure!" or "Here is your output".

The JSON object should contain the appropriate fields based on the user's query:
- query: for free-text searches
- species_acronym: for species filtering (BU, PV, etc.) - ALWAYS use acronyms
- essentiality: for essentiality filtering (essential, non_essential)
- has_amr_info: for AMR information filtering (true/false)
- cog_funcats: for COG functional categories
- cog_id: for specific COG IDs
- kegg: for KEGG pathways
- go_term: for GO terms
- pfam: for Pfam domains
- interpro: for InterPro domains
- isolates: for specific isolate filtering
- page, per_page: for pagination
- sort_field, sort_order: for sorting

Example:
User: Show essential genes in Bacteroides uniformis not involved in AMR
Output:
{
  "species_acronym": "BU",
  "essentiality": "essential",
  "has_amr_info": false
}
"""

class NaturalLanguageQueryService:
    def __init__(self):
        self.gene_service = GeneService()
    
    def _get_openai_client(self):
        """Get OpenAI client instance. This method can be overridden for testing."""
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def interpret_and_execute_query(self, user_query: str) -> Dict[str, Any]:
        """
        Interpret natural language query and automatically execute the appropriate API request.
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary containing query results and metadata
        """
        try:
            # Step 1: Interpret the natural language query
            interpreted_query = await self._interpret_query(user_query)
            
            if "error" in interpreted_query:
                return interpreted_query
            
            # Step 2: Execute the API call directly using the interpreted query
            results = await self._execute_api_call(interpreted_query)
            
            return {
                "original_query": user_query,
                "interpreted_query": interpreted_query,
                "results": results,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": f"Failed to process query: {str(e)}",
                "original_query": user_query,
                "success": False
            }
    
    async def _interpret_query(self, user_query: str) -> Dict[str, Any]:
        """Interpret natural language query using OpenAI."""
        try:
            client = self._get_openai_client()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_query}
                ],
                tools=[{
                    "type": "function",
                    "function": METT_GENE_QUERY_SCHEMA
                }],
                tool_choice="auto",
                temperature=0
            )

            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                return {"error": "No tool call returned by GPT. Check prompt or query clarity."}

            arguments = tool_calls[0].function.arguments
            parsed_query = NaturalLanguageGeneQuery.model_validate_json(arguments)
            return parsed_query.model_dump(exclude_none=True)

        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_api_call(self, interpreted_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the API call based on the interpreted query parameters.
        
        Args:
            interpreted_query: Dictionary containing the interpreted query parameters
            
        Returns:
            API response results
        """
        try:
            # Determine the best API method based on the query complexity
            method_name = self._determine_api_method(interpreted_query)
            
            if method_name == "get_faceted_search":
                # Create faceted search query schema
                faceted_params = GeneFacetedSearchQuerySchema(
                    query=interpreted_query.get("query"),
                    species_acronym=interpreted_query.get("species_acronym"),
                    isolates=interpreted_query.get("isolates", ""),
                    essentiality=interpreted_query.get("essentiality"),
                    cog_id=interpreted_query.get("cog_id"),
                    cog_funcats=interpreted_query.get("cog_funcats"),
                    kegg=interpreted_query.get("kegg"),
                    go_term=interpreted_query.get("go_term"),
                    pfam=interpreted_query.get("pfam"),
                    interpro=interpreted_query.get("interpro"),
                    has_amr_info=interpreted_query.get("has_amr_info"),
                    limit=interpreted_query.get("limit", 50)
                )
                result = await self.gene_service.get_faceted_search(faceted_params)
                return {
                    "type": "faceted_results",
                    "data": result,
                    "total_results": len(result.get("genes", [])) if isinstance(result, dict) else len(result) if isinstance(result, list) else 0
                }
            
            elif method_name == "get_genes_by_multiple_genomes_and_string":
                # Create advanced search query schema
                advanced_params = GeneAdvancedSearchQuerySchema(
                    isolates=interpreted_query.get("isolates", ""),
                    species_acronym=interpreted_query.get("species_acronym"),
                    query=interpreted_query.get("query", ""),
                    filter=interpreted_query.get("filter"),
                    filter_operators=interpreted_query.get("filter_operators"),
                    page=interpreted_query.get("page", 1),
                    per_page=interpreted_query.get("per_page", 50),
                    sort_field=interpreted_query.get("sort_field"),
                    sort_order=interpreted_query.get("sort_order", "asc")
                )
                result = await self.gene_service.get_genes_by_multiple_genomes_and_string(advanced_params)
                return {
                    "type": "paginated_results",
                    "data": result.model_dump() if hasattr(result, 'model_dump') else result,
                    "total_results": result.total_results if hasattr(result, 'total_results') else len(result.results) if hasattr(result, 'results') else 0
                }
            
            else:  # Default to search_genes
                # Create basic search query schema
                search_params = GeneSearchQuerySchema(
                    query=interpreted_query.get("query", ""),
                    page=interpreted_query.get("page", 1),
                    per_page=interpreted_query.get("per_page", 50),
                    sort_field=interpreted_query.get("sort_field"),
                    sort_order=interpreted_query.get("sort_order", "asc")
                )
                result = await self.gene_service.search_genes(search_params)
                return {
                    "type": "paginated_results",
                    "data": result.model_dump() if hasattr(result, 'model_dump') else result,
                    "total_results": result.total_results if hasattr(result, 'total_results') else len(result.results) if hasattr(result, 'results') else 0
                }
                
        except Exception as e:
            return {
                "error": f"API execution failed: {str(e)}",
                "type": "error"
            }
    
    def _determine_api_method(self, interpreted_query: Dict[str, Any]) -> str:
        """
        Determine the best API method based on the interpreted query parameters.
        
        Args:
            interpreted_query: Dictionary containing the interpreted query parameters
            
        Returns:
            String indicating the API method to use
        """
        # Check if we have faceted search parameters
        faceted_params = [
            "essentiality", "cog_id", "cog_funcats", "kegg", "go_term", 
            "pfam", "interpro", "has_amr_info"
        ]
        
        has_faceted_params = any(interpreted_query.get(param) for param in faceted_params)
        has_species = bool(interpreted_query.get("species_acronym"))
        
        if has_faceted_params and has_species:
            return "get_faceted_search"
        elif has_species:
            return "get_genes_by_multiple_genomes_and_string"
        else:
            return "search_genes"

# Backward compatibility function
async def interpret_natural_language_query(user_query: str) -> dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Now returns the full automated query execution results.
    """
    service = NaturalLanguageQueryService()
    return await service.interpret_and_execute_query(user_query)
