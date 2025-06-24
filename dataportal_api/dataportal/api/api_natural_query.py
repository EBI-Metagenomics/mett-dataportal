from ninja import Router
from pydantic import BaseModel
from ..services.nl_query_service import interpret_natural_language_query

router = Router()

class QueryRequest(BaseModel):
    query: str

@router.post("/interpret")
def interpret_query(request, payload: QueryRequest):
    result = interpret_natural_language_query(payload.query)
    return result