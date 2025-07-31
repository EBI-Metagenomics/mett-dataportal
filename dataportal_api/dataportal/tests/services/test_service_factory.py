from dataportal.services.service_factory import ServiceFactory
from dataportal.services.species_service import SpeciesService
from dataportal.services.genome_service import GenomeService
from dataportal.services.gene_service import GeneService
from dataportal.services.essentiality_service import EssentialityService
from dataportal.services.app_health_service import AppHealthService


class TestServiceFactory:
    """Test cases for ServiceFactory class."""

    def test_get_species_service_singleton(self):
        """Test that get_species_service returns the same instance."""
        service1 = ServiceFactory.get_species_service()
        service2 = ServiceFactory.get_species_service()

        assert service1 is service2
        assert isinstance(service1, SpeciesService)

    def test_get_genome_service_singleton(self):
        """Test that get_genome_service returns the same instance."""
        service1 = ServiceFactory.get_genome_service()
        service2 = ServiceFactory.get_genome_service()

        assert service1 is service2
        assert isinstance(service1, GenomeService)

    def test_get_gene_service_singleton(self):
        """Test that get_gene_service returns the same instance."""
        service1 = ServiceFactory.get_gene_service()
        service2 = ServiceFactory.get_gene_service()

        assert service1 is service2
        assert isinstance(service1, GeneService)

    def test_get_essentiality_service_singleton(self):
        """Test that get_essentiality_service returns the same instance."""
        service1 = ServiceFactory.get_essentiality_service()
        service2 = ServiceFactory.get_essentiality_service()

        assert service1 is service2
        assert isinstance(service1, EssentialityService)

    def test_get_app_health_service_singleton(self):
        """Test that get_app_health_service returns the same instance."""
        service1 = ServiceFactory.get_app_health_service()
        service2 = ServiceFactory.get_app_health_service()

        assert service1 is service2
        assert isinstance(service1, AppHealthService)


    def test_different_services_are_different_instances(self):
        """Test that different services are different instances."""
        species_service = ServiceFactory.get_species_service()
        genome_service = ServiceFactory.get_genome_service()
        gene_service = ServiceFactory.get_gene_service()

        assert species_service is not genome_service
        assert species_service is not gene_service
        assert genome_service is not gene_service

    def test_service_instances_persist(self):
        """Test that service instances persist across multiple calls."""
        # Clear any existing instances
        ServiceFactory._instances.clear()

        # Get services
        species1 = ServiceFactory.get_species_service()
        genome1 = ServiceFactory.get_genome_service()
        gene1 = ServiceFactory.get_gene_service()

        # Get them again
        species2 = ServiceFactory.get_species_service()
        genome2 = ServiceFactory.get_genome_service()
        gene2 = ServiceFactory.get_gene_service()

        # Verify they're the same instances
        assert species1 is species2
        assert genome1 is genome2
        assert gene1 is gene2

        # Verify the instances dict contains them
        assert "species" in ServiceFactory._instances
        assert "genome" in ServiceFactory._instances
        assert "gene" in ServiceFactory._instances

    def test_service_abc_inheritance(self):
        """Test that all services properly inherit from BaseService."""
        from dataportal.services.base_service import BaseService

        species_service = ServiceFactory.get_species_service()
        genome_service = ServiceFactory.get_genome_service()
        gene_service = ServiceFactory.get_gene_service()

        assert isinstance(species_service, BaseService)
        assert isinstance(genome_service, BaseService)
        assert isinstance(gene_service, BaseService)

    def test_service_index_names(self):
        """Test that services have correct index names."""
        species_service = ServiceFactory.get_species_service()
        genome_service = ServiceFactory.get_genome_service()
        gene_service = ServiceFactory.get_gene_service()

        assert species_service.index_name == "species_index"
        assert genome_service.index_name == "strain_index"
        assert gene_service.index_name == "gene_index"

    def test_service_abc_methods_exist(self):
        """Test that all services have the required ABC methods."""
        species_service = ServiceFactory.get_species_service()
        genome_service = ServiceFactory.get_genome_service()
        gene_service = ServiceFactory.get_gene_service()

        # Check that all services have the required ABC methods
        for service in [species_service, genome_service, gene_service]:
            assert hasattr(service, "get_by_id")
            assert hasattr(service, "get_all")
            assert hasattr(service, "search")
            assert hasattr(service, "_convert_hit_to_entity")
            assert hasattr(service, "_create_search")
            assert hasattr(service, "_handle_elasticsearch_error")
            assert hasattr(service, "_validate_required_fields")

    def test_service_factory_cleanup(self):
        """Test that service factory can be cleaned up."""
        # Get some services
        ServiceFactory.get_species_service()
        ServiceFactory.get_genome_service()

        # Verify instances exist
        assert len(ServiceFactory._instances) >= 2

        # Clear instances
        ServiceFactory._instances.clear()

        # Verify instances are cleared
        assert len(ServiceFactory._instances) == 0
