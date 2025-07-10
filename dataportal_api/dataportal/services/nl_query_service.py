import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from dataportal.schema.nl_schemas import METT_GENE_QUERY_SCHEMA
from dataportal.schema.gene_schemas import GeneQuery, GenePaginationSchema
from dataportal.services.gene_service import GeneService

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are an intelligent bioinformatics data portal assistant that converts natural language queries into structured API requests.

Your job is to interpret user requests and convert them into valid JSON objects for querying gene data.

When referencing a species, always return the acronym in case full scientific name is given
(e.g. BU for "Bacteroides uniformis" or "B. uniformis", and PV for "Phocaeicola vulgatus" or "P. vulgatus").

⚠️ Output ONLY a valid JSON object. Do not include any explanation, prefix, or suffix.
Do NOT say anything like "Sure!" or "Here is your output".

Supported JSON fields: species, essentiality, amr, function, cog_category.

Example:
User: Show essential genes in PV not involved in AMR
Output:
{
  "species": "PV",
  "essentiality": "essential",
  "amr": false
}
"""

class NaturalLanguageQueryService:
    def __init__(self):
        self.gene_service = GeneService()
    
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
            
            # Step 2: Map the interpreted query to appropriate API call
            api_params = self._map_to_api_parameters(interpreted_query)
            
            # Step 3: Execute the API call
            results = await self._execute_api_call(api_params)
            
            return {
                "original_query": user_query,
                "interpreted_query": interpreted_query,
                "api_parameters": api_params,
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
            parsed_query = GeneQuery.model_validate_json(arguments)
            return parsed_query.model_dump(exclude_none=True)

        except Exception as e:
            return {"error": str(e)}
    
    def _map_to_api_parameters(self, interpreted_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map interpreted query to appropriate API parameters.
        
        This method determines which API endpoint and parameters to use based on the interpreted query.
        """
        api_params = {
            "method": "search_genes",
            "parameters": {}
        }
        
        # Extract parameters from interpreted query
        species = interpreted_query.get("species")
        essentiality = interpreted_query.get("essentiality")
        amr = interpreted_query.get("amr")
        function = interpreted_query.get("function")
        cog_category = interpreted_query.get("cog_category")
        
        # Build filter string based on interpreted parameters
        filters = []
        
        if essentiality:
            filters.append(f"essentiality:{essentiality}")
        
        if amr is not None:
            if amr:
                filters.append("has_amr_info:true")
            else:
                filters.append("has_amr_info:false")
        
        if cog_category:
            filters.append(f"cog_funcats:{cog_category}")
        
        # Determine the best API method based on the query complexity
        if species and len(filters) > 0:
            # Use faceted search for complex queries with species and filters
            api_params["method"] = "get_faceted_search"
            api_params["parameters"] = {
                "query": function or "",
                "species_acronym": species,
                "isolates": "",
                "essentiality": essentiality,
                "cog_funcats": cog_category,
                "has_amr_info": amr,
                "limit": 50
            }
        elif species:
            # Use advanced search for species-specific queries
            api_params["method"] = "get_genes_by_multiple_genomes_and_string"
            api_params["parameters"] = {
                "isolates": "",
                "species_acronym": species,
                "query": function or "",
                "filter": ";".join(filters) if filters else None,
                "page": 1,
                "per_page": 50
            }
        elif function:
            # Use basic search for function-based queries
            api_params["method"] = "search_genes"
            api_params["parameters"] = {
                "query": function,
                "isolate_name": None,
                "filter": ";".join(filters) if filters else None,
                "page": 1,
                "per_page": 50
            }
        else:
            # Default to basic search
            api_params["method"] = "search_genes"
            api_params["parameters"] = {
                "query": "",
                "isolate_name": None,
                "filter": ";".join(filters) if filters else None,
                "page": 1,
                "per_page": 50
            }
        
        return api_params
    
    async def _execute_api_call(self, api_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the API call based on the mapped parameters.
        
        Args:
            api_params: Dictionary containing method name and parameters
            
        Returns:
            API response results
        """
        method_name = api_params["method"]
        parameters = api_params["parameters"]
        
        try:
            if method_name == "search_genes":
                result = await self.gene_service.search_genes(
                    query=parameters.get("query", ""),
                    isolate_name=parameters.get("isolate_name"),
                    filter=parameters.get("filter"),
                    page=parameters.get("page", 1),
                    per_page=parameters.get("per_page", 50)
                )
                return {
                    "type": "paginated_results",
                    "data": result.model_dump() if hasattr(result, 'model_dump') else result,
                    "total_results": result.total_results if hasattr(result, 'total_results') else len(result.results) if hasattr(result, 'results') else 0
                }
            
            elif method_name == "get_faceted_search":
                result = await self.gene_service.get_faceted_search(
                    query=parameters.get("query", ""),
                    species_acronym=parameters.get("species_acronym"),
                    isolates=parameters.get("isolates", []),
                    essentiality=parameters.get("essentiality"),
                    cog_id=parameters.get("cog_id"),
                    cog_funcats=parameters.get("cog_funcats"),
                    kegg=parameters.get("kegg"),
                    go_term=parameters.get("go_term"),
                    pfam=parameters.get("pfam"),
                    interpro=parameters.get("interpro"),
                    has_amr_info=parameters.get("has_amr_info"),
                    limit=parameters.get("limit", 50)
                )
                return {
                    "type": "faceted_results",
                    "data": result,
                    "total_results": len(result.get("genes", [])) if isinstance(result, dict) else len(result) if isinstance(result, list) else 0
                }
            
            elif method_name == "get_genes_by_multiple_genomes_and_string":
                result = await self.gene_service.get_genes_by_multiple_genomes_and_string(
                    isolates=parameters.get("isolates", ""),
                    species_acronym=parameters.get("species_acronym"),
                    query=parameters.get("query", ""),
                    filter=parameters.get("filter"),
                    page=parameters.get("page", 1),
                    per_page=parameters.get("per_page", 50)
                )
                return {
                    "type": "paginated_results",
                    "data": result.model_dump() if hasattr(result, 'model_dump') else result,
                    "total_results": result.total_results if hasattr(result, 'total_results') else len(result.results) if hasattr(result, 'results') else 0
                }
            
            else:
                return {
                    "error": f"Unknown API method: {method_name}",
                    "type": "error"
                }
                
        except Exception as e:
            return {
                "error": f"API execution failed: {str(e)}",
                "type": "error"
            }

# Backward compatibility function
async def interpret_natural_language_query(user_query: str) -> dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Now returns the full automated query execution results.
    """
    service = NaturalLanguageQueryService()
    return await service.interpret_and_execute_query(user_query)
