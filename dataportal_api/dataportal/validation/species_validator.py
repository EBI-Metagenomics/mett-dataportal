from typing import Dict, List, Any
from dataportal.validation.base_validator import ValidationService


class SpeciesValidationService(ValidationService):
    """Validation service for species data."""

    def __init__(self):
        super().__init__("species_index")
        self.required_fields = ["acronym", "scientific_name"]
        self.field_types = {
            "acronym": str,
            "scientific_name": str,
            "common_name": str,
            "taxonomy_id": int,
        }
        self.field_lengths = {"acronym": 50, "scientific_name": 200, "common_name": 100}

    async def validate_entity(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate species entity data."""
        errors = {}

        # Required fields
        required_errors = self._validate_required_fields(data, self.required_fields)
        if required_errors:
            errors["required"] = required_errors

        # Field types
        type_errors = self._validate_field_types(data, self.field_types)
        if type_errors:
            errors["types"] = type_errors

        # String lengths
        length_errors = self._validate_string_length(data, self.field_lengths)
        if length_errors:
            errors["lengths"] = length_errors

        return errors

    async def validate_query(self, query: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate species query parameters."""
        errors = {}

        # Validate search parameters
        if "acronym" in query and not isinstance(query["acronym"], str):
            errors["acronym"] = ["Acronym must be a string"]

        if "scientific_name" in query and not isinstance(query["scientific_name"], str):
            errors["scientific_name"] = ["Scientific name must be a string"]

        return errors

    async def is_valid(self, data: Dict[str, Any]) -> bool:
        """Check if species data is valid."""
        validation_errors = await self.validate_entity(data)
        return len(validation_errors) == 0
