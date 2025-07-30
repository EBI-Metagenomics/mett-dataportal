from abc import abstractmethod
from typing import Any

from dataportal.services.base_service import BaseService


class ValidationService(BaseService[dict, dict]):
    """
    Abstract base class for validation services.
    Provides common validation functionality across the application.
    """

    def __init__(self, index_name: str):
        super().__init__(index_name)

    @abstractmethod
    async def validate_entity(self, data: dict[str, Any]) -> dict[str, list[str]]:
        """
        Validate entity data and return validation errors.

        Args:
            data: The data to validate

        Returns:
            Dictionary mapping field names to lists of error messages
        """
        pass

    @abstractmethod
    async def validate_query(self, query: dict[str, Any]) -> dict[str, list[str]]:
        """
        Validate query parameters and return validation errors.

        Args:
            query: The query parameters to validate

        Returns:
            Dictionary mapping field names to lists of error messages
        """
        pass

    @abstractmethod
    async def is_valid(self, data: dict[str, Any]) -> bool:
        """
        Check if data is valid.

        Args:
            data: The data to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def _validate_required_fields(
        self, data: dict[str, Any], required_fields: list[str]
    ) -> list[str]:
        """Validate that required fields are present."""
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"Field '{field}' is required")
        return errors

    def _validate_field_types(
        self, data: dict[str, Any], field_types: dict[str, type]
    ) -> list[str]:
        """Validate field types."""
        errors = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}' must be of type {expected_type.__name__}"
                )
        return errors

    def _validate_string_length(
        self, data: dict[str, Any], field_lengths: dict[str, int]
    ) -> list[str]:
        """Validate string field lengths."""
        errors = []
        for field, max_length in field_lengths.items():
            if (
                field in data
                and isinstance(data[field], str)
                and len(data[field]) > max_length
            ):
                errors.append(
                    f"Field '{field}' must be no longer than {max_length} characters"
                )
        return errors

    def _validate_numeric_range(
        self, data: dict[str, Any], field_ranges: dict[str, tuple]
    ) -> list[str]:
        """Validate numeric field ranges."""
        errors = []
        for field, (min_val, max_val) in field_ranges.items():
            if field in data:
                try:
                    value = float(data[field])
                    if value < min_val or value > max_val:
                        errors.append(
                            f"Field '{field}' must be between {min_val} and {max_val}"
                        )
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be a valid number")
        return errors

    # Implement abstract methods from BaseService
    async def get_by_id(self, id: str) -> dict | None:
        """Not implemented for validation service."""
        raise NotImplementedError("Validation service does not support get_by_id")

    async def get_all(self, **kwargs) -> list[dict]:
        """Not implemented for validation service."""
        raise NotImplementedError("Validation service does not support get_all")

    async def search(self, query: dict) -> list[dict]:
        """Not implemented for validation service."""
        raise NotImplementedError("Validation service does not support search")
