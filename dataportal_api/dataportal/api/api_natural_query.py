import logging

from ninja import Router
from ninja.errors import HttpError

from dataportal.schema.response_schemas import (
    SuccessResponseSchema,
    create_success_response,
)
from dataportal.services.nl_query_service import NaturalLanguageQueryService
from dataportal.utils.errors import raise_internal_server_error, raise_validation_error
from dataportal.utils.response_wrappers import wrap_success_response

logger = logging.getLogger(__name__)

nl_query_service = NaturalLanguageQueryService()

ROUTER_NL_QUERY = "Natural Language Queries"
nl_query_router = Router(tags=[ROUTER_NL_QUERY])


@nl_query_router.post(
    "/query",
    response=SuccessResponseSchema,
    summary="Execute natural language query",
    description=(
        "Convert natural language queries into structured API requests and automatically execute them. "
        "This endpoint interprets user intent and returns actual database results without requiring "
        "manual API parameter construction."
    ),
    include_in_schema=False,
)
@wrap_success_response
async def execute_natural_language_query(request, query: str):
    """
    Execute a natural language query and return the results.

    This endpoint automatically:
    1. Interprets the natural language query using AI
    2. Maps it to the appropriate API endpoint and parameters
    3. Executes the query against the database
    4. Returns the results with metadata about the interpretation

    Example queries:
    - "Show essential genes in Bacteroides uniformis"
    - "Find genes involved in AMR in PV"
    - "Get all transport proteins in BU"
    - "Show non-essential genes with COG category J"
    """
    try:
        if not query or not query.strip():
            raise_validation_error("Query cannot be empty")

        # Execute the natural language query
        result = await nl_query_service.interpret_and_execute_query(query.strip())

        if not result.get("success", False):
            error_msg = result.get("error", "Unknown error occurred")
            logger.error(f"Natural language query failed: {error_msg}")
            raise_internal_server_error(f"Query execution failed: {error_msg}")

        # Extract results for response
        results_data = result.get("results", {})
        total_results = results_data.get("total_results", 0)

        # Determine API method used
        method_name = nl_query_service._determine_api_method(result.get("interpreted_query", {}))

        return create_success_response(
            data={
                "query_interpretation": {
                    "original_query": result.get("original_query"),
                    "interpreted_parameters": result.get("interpreted_query"),
                    "api_method_used": method_name,
                    "api_parameters": result.get("interpreted_query"),
                },
                "results": results_data.get("data", {}),
                "summary": {
                    "total_results": total_results,
                    "result_type": results_data.get("type", "unknown"),
                    "success": True,
                },
            },
            message=f"Query executed successfully. Found {total_results} results.",
        )

    except HttpError:
        # Re-raise HTTP errors as they're already properly formatted
        raise
    except Exception as e:
        logger.error(f"Unexpected error in natural language query: {str(e)}", exc_info=True)
        raise_internal_server_error(f"Unexpected error occurred: {str(e)}")


@nl_query_router.post(
    "/interpret",
    response=SuccessResponseSchema,
    summary="Interpret natural language query only",
    description=(
        "Convert natural language query to structured parameters without executing the query. "
        "Useful for debugging or when you want to see how the AI interprets the query before execution."
    ),
    include_in_schema=False,
)
@wrap_success_response
async def interpret_query_only(request, query: str):
    """
    Interpret a natural language query without executing it.

    This endpoint only performs the interpretation step and returns the structured parameters
    that would be used for the API call, without actually executing the query.
    """
    try:
        if not query or not query.strip():
            raise_validation_error("Query cannot be empty")

        # Only interpret the query
        interpreted_query = await nl_query_service._interpret_query(query.strip())

        if "error" in interpreted_query:
            logger.error(f"Query interpretation failed: {interpreted_query['error']}")
            raise_internal_server_error(
                f"Query interpretation failed: {interpreted_query['error']}"
            )

        # Determine API method (no mapping needed since we use schema directly)
        method_name = nl_query_service._determine_api_method(interpreted_query)

        return create_success_response(
            data={
                "original_query": query.strip(),
                "interpreted_parameters": interpreted_query,
                "api_method_used": method_name,
                "api_parameters": interpreted_query,
            },
            message="Query interpreted successfully",
        )

    except HttpError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query interpretation: {str(e)}", exc_info=True)
        raise_internal_server_error(f"Unexpected error occurred: {str(e)}")
