from dataportal.services.app_health_service import AppHealthService
from dataportal.services.base_service import BaseService
from dataportal.services.essentiality_service import EssentialityService
from dataportal.services.gene_service import GeneService
from dataportal.services.genome_service import GenomeService
from dataportal.services.species_service import SpeciesService


class ServiceFactory:
    """
    Factory class for creating and managing service instances.
    Provides singleton pattern for services and centralized service management.
    """

    _instances: dict[str, BaseService] = {}

    @classmethod
    def get_species_service(cls) -> SpeciesService:
        """Get or create SpeciesService instance."""
        if "species" not in cls._instances:
            cls._instances["species"] = SpeciesService()
        return cls._instances["species"]

    @classmethod
    def get_essentiality_service(cls) -> EssentialityService:
        """Get or create EssentialityService instance."""
        if "essentiality" not in cls._instances:
            cls._instances["essentiality"] = EssentialityService()
        return cls._instances["essentiality"]

    @classmethod
    def get_app_health_service(cls) -> AppHealthService:
        """Get or create AppHealthService instance."""
        if "app_health" not in cls._instances:
            cls._instances["app_health"] = AppHealthService()
        return cls._instances["app_health"]

    @classmethod
    def get_genome_service(cls) -> GenomeService:
        """Get or create GenomeService instance."""
        if "genome" not in cls._instances:
            cls._instances["genome"] = GenomeService()
        return cls._instances["genome"]

    @classmethod
    def get_gene_service(cls) -> GeneService:
        """Get or create GeneService instance."""
        if "gene" not in cls._instances:
            cls._instances["gene"] = GeneService()
        return cls._instances["gene"]

    @classmethod
    def register_service(cls, name: str, service: BaseService) -> None:
        """Register a custom service instance."""
        cls._instances[name] = service

    @classmethod
    def get_service(cls, name: str) -> BaseService:
        """Get a service by name."""
        if name not in cls._instances:
            raise ValueError(f"Service '{name}' not found")
        return cls._instances[name]

    @classmethod
    def clear_instances(cls) -> None:
        """Clear all service instances (useful for testing)."""
        cls._instances.clear()

    @classmethod
    def get_all_services(cls) -> dict[str, BaseService]:
        """Get all registered services."""
        return cls._instances.copy()
