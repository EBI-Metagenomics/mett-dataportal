from pydantic import BaseModel, ConfigDict


class BasePaginationSchema(BaseModel):
    page_number: int
    num_pages: int
    has_previous: bool
    has_next: bool
    total_results: int

    model_config = ConfigDict(from_attributes=True)
