from abc import abstractmethod
from typing import Any, Dict, List, Optional
from dataportal.services.base_service import BaseService


class ValidationService(BaseService[Dict, Dict]):
    """
    Abstract base class for validation services.
    Provides common validation functionality across the application.
    """

    def __init__(self, index_name: str):
        super().__init__(index_name)

    @abstractmethod
    async def validate_entity(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate entity data and return validation errors.

        Args:
            data: The data to validate

        Returns:
            Dictionary mapping field names to lists of error messages
        """
        pass

    @abstractmethod
    async def validate_query(self, query: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate query parameters and return validation errors.

        Args:
            query: The query parameters to validate

        Returns:
            Dictionary mapping field names to lists of error messages
        """
        pass

    @abstractmethod
    async def is_valid(self, data: Dict[str, Any]) -> bool:
        """
        Check if data is valid.

        Args:
            data: The data to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def _validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate that required fields are present."""
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"Field '{field}' is required")
        return errors

    def _validate_field_types(
        self, data: Dict[str, Any], field_types: Dict[str, type]
    ) -> List[str]:
        """Validate field types."""
        errors = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}' must be of type {expected_type.__name__}"
                )
        return errors

    def _validate_string_length(
        self, data: Dict[str, Any], field_lengths: Dict[str, int]
    ) -> List[str]:
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
        self, data: Dict[str, Any], field_ranges: Dict[str, tuple]
    ) -> List[str]:
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
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """Not implemented for validation service."""
        raise NotImplementedError("Validation service does not support get_by_id")

    async def get_all(self, **kwargs) -> List[Dict]:
        """Not implemented for validation service."""
        raise NotImplementedError("Validation service does not support get_all")

    async def search(self, query: Dict) -> List[Dict]:
        """Not implemented for validation service."""
        raise NotImplementedError("Validation service does not support search")
