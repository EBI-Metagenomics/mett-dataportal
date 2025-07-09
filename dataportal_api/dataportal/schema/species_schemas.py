from pydantic import BaseModel, ConfigDict


class SpeciesSchema(BaseModel):
    scientific_name: str
    common_name: str
    acronym: str
    taxonomy_id: int

    model_config = ConfigDict(from_attributes=True)

__all__ = [
    "SpeciesSchema",
]
