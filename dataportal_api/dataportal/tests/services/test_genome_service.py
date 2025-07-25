from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from dataportal.schema.genome_schemas import (
    GenomePaginationSchema,
    GenomeResponseSchema,
    GenomeSearchQuerySchema,
    GetAllGenomesQuerySchema,
    GenomesByIsolateNamesQuerySchema,
    GenomeAutocompleteQuerySchema,
    StrainSuggestionSchema,
)
from dataportal.services.genome_service import GenomeService
from dataportal.services.essentiality_service import EssentialityService
from dataportal.utils.exceptions import ServiceError


class MockESResponse:
    def __init__(self, hits):
        self.hits = type(
            "Hits", (), {"total": type("Total", (), {"value": len(hits)})}
        )()
        self._hits = hits

    def __iter__(self):
        return iter(self._hits)


@pytest.fixture
def mock_strain_hits():
    hit1 = MagicMock()
    hit1.to_dict.return_value = {
        "species_scientific_name": "Bacteroides uniformis",
        "species_acronym": "BU",
        "isolate_name": "BU_ATCC8492",
        "assembly_name": "ASM001",
        "assembly_accession": "GCA_000001405.1",
        "fasta_file": "file1.fna",
        "gff_file": "file1.gff",
        "fasta_url": "http://example.com/file1.fna",
        "gff_url": "http://example.com/file1.gff",
        "type_strain": True,
        "contigs": [
            {"seq_id": "contig_1", "length": 1000000},
            {"seq_id": "contig_2", "length": 500000}
        ],
    }
    hit1.isolate_name = "BU_ATCC8492"
    hit1.assembly_name = "ASM001"

    hit2 = MagicMock()
    hit2.to_dict.return_value = {
        "species_scientific_name": "Phocaeicola vulgatus",
        "species_acronym": "PV",
        "isolate_name": "PV_ATCC8482",
        "assembly_name": "ASM002",
        "assembly_accession": "GCA_000001406.1",
        "fasta_file": "file2.fna",
        "gff_file": "file2.gff",
        "fasta_url": "http://example.com/file2.fna",
        "gff_url": "http://example.com/file2.gff",
        "type_strain": True,
        "contigs": [
            {"seq_id": "contig_1", "length": 1200000},
            {"seq_id": "contig_2", "length": 600000}
        ],
    }
    hit2.isolate_name = "PV_ATCC8482"
    hit2.assembly_name = "ASM002"

    return [hit1, hit2]


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_type_strains(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_strain_hits)
    )

    service = GenomeService()
    result = await service.get_type_strains()

    assert len(result) == 2
    assert isinstance(result[0], GenomeResponseSchema)
    assert result[0].isolate_name == "BU_ATCC8492"
    assert result[1].isolate_name == "PV_ATCC8482"
    assert all(strain.type_strain for strain in result)


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_genomes_by_string(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_strain_hits)
    )

    service = GenomeService()

    # Create search query schema
    params = GenomeSearchQuerySchema(
        query="BU", page=1, per_page=10, sortField="isolate_name", sortOrder="asc"
    )

    result = await service.search_genomes_by_string(params)

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 2
    assert len(result.results) == 2
    assert result.results[0].isolate_name == "BU_ATCC8492"
    assert result.results[1].isolate_name == "PV_ATCC8482"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_genome_by_strain_name(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_strain_hits[0])

    service = GenomeService()
    result = await service.get_genome_by_strain_name("BU_ATCC8492")

    assert result.isolate_name == "BU_ATCC8492"
    assert result.species_scientific_name == "Bacteroides uniformis"
    assert result.type_strain is True


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_genome_by_strain_name_not_found(mock_sync_to_async):
    mock_sync_to_async.side_effect = Exception("Genome not found")

    service = GenomeService()
    with pytest.raises(ServiceError):
        await service.get_genome_by_strain_name("Genome not found")


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_strains(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_strain_hits)
    )

    service = GenomeService()

    # Create autocomplete query schema
    params = GenomeAutocompleteQuerySchema(query="BU", limit=10)

    result = await service.search_strains(params)

    assert len(result) == 2
    assert isinstance(result[0], StrainSuggestionSchema)
    assert result[0].isolate_name == "BU_ATCC8492"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_strains_with_species_filter(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse([mock_strain_hits[0]])
    )

    service = GenomeService()

    # Create autocomplete query schema with species filter
    params = GenomeAutocompleteQuerySchema(query="90", species_acronym="BU", limit=10)

    result = await service.search_strains(params)

    assert len(result) == 1
    assert result[0].isolate_name == "BU_ATCC8492"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_genomes_by_isolate_names(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_strain_hits)
    )

    service = GenomeService()

    # Create query schema
    params = GenomesByIsolateNamesQuerySchema(isolates="BU_ATCC8492,PV_ATCC8482")

    result = await service.get_genomes_by_isolate_names(params)

    assert len(result) == 2
    assert result[0].isolate_name == "BU_ATCC8492"
    assert result[1].isolate_name == "PV_ATCC8482"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_genomes_by_isolate_names_single(
    mock_sync_to_async, mock_strain_hits
):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse([mock_strain_hits[0]])
    )

    service = GenomeService()

    # Create query schema for single isolate
    params = GenomesByIsolateNamesQuerySchema(isolates="BU_ATCC8492")

    result = await service.get_genomes_by_isolate_names(params)

    assert len(result) == 1
    assert result[0].isolate_name == "BU_ATCC8492"
    assert result[0].species_scientific_name == "Bacteroides uniformis"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_genomes(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_strain_hits)
    )

    service = GenomeService()

    # Create query schema
    params = GetAllGenomesQuerySchema(
        page=1, per_page=10, sortField="isolate_name", sortOrder="asc"
    )

    result = await service.get_genomes(params)

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 2
    assert len(result.results) == 2
    assert result.results[0].isolate_name == "BU_ATCC8492"
    assert result.results[1].isolate_name == "PV_ATCC8482"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_genomes_by_string_with_species_filter(
    mock_sync_to_async, mock_strain_hits
):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse([mock_strain_hits[0]])
    )

    service = GenomeService()

    # Create search query schema with species filter
    params = GenomeSearchQuerySchema(
        query="",
        page=1,
        per_page=10,
        sortField="isolate_name",
        sortOrder="asc",
        species_acronym="BU",
    )

    result = await service.search_genomes_by_string(params)

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 1
    assert len(result.results) == 1
    assert result.results[0].isolate_name == "BU_ATCC8492"
    assert result.results[0].species_acronym == "BU"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_genomes_by_string_with_isolates_filter(
    mock_sync_to_async, mock_strain_hits
):
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse([mock_strain_hits[0]])
    )

    service = GenomeService()

    # Create search query schema with isolates filter
    params = GenomeSearchQuerySchema(
        query="",
        page=1,
        per_page=10,
        sortField="isolate_name",
        sortOrder="asc",
        isolates=["BU_ATCC8492"],
    )

    result = await service.search_genomes_by_string(params)

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 1
    assert len(result.results) == 1
    assert result.results[0].isolate_name == "BU_ATCC8492"


@patch(
    "dataportal.services.essentiality_service.EssentialityService.load_essentiality_data_by_strain"
)
@pytest.mark.asyncio
async def test_get_essentiality_data(mock_load_cache):
    # Mock the cache data
    mock_cache_data = {
        "BU_ATCC8492": {
            "contig_1": {
                "BU_ATCC8492_00001": {
                    "locus_tag": "BU_ATCC8492_00001",
                    "start": 1671862,
                    "end": 1672323,
                    "essentiality": "essential",
                }
            }
        }
    }
    mock_load_cache.return_value = mock_cache_data

    service = EssentialityService()
    # Set the cache directly
    service.essentiality_cache = mock_cache_data
    # The cache will be populated by our mock
    result = await service.get_essentiality_data_by_strain_and_ref(
        "BU_ATCC8492", "contig_1"
    )

    assert "BU_ATCC8492_00001" in result
    assert result["BU_ATCC8492_00001"]["essentiality"] == "essential"
    assert result["BU_ATCC8492_00001"]["start"] == 1671862
    assert result["BU_ATCC8492_00001"]["end"] == 1672323


# New tests for ABC methods
@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_by_id_success(mock_sync_to_async, mock_strain_hits):
    """Test the ABC get_by_id method."""
    service = GenomeService()
    
    # Mock the _execute_search method to return our test data
    with patch.object(service, '_execute_search', return_value=[mock_strain_hits[0]]):
        result = await service.get_by_id("BU_ATCC8492")

        assert result is not None
        assert isinstance(result, GenomeResponseSchema)
        assert result.isolate_name == "BU_ATCC8492"
        assert result.species_scientific_name == "Bacteroides uniformis"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_sync_to_async):
    """Test the ABC get_by_id method when genome not found."""
    service = GenomeService()
    
    # Mock the _execute_search method to return empty results
    with patch.object(service, '_execute_search', return_value=[]):
        result = await service.get_by_id("INVALID")

        assert result is None


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_by_id_exception(mock_sync_to_async):
    """Test the ABC get_by_id method when exception occurs."""
    service = GenomeService()
    
    # Mock the _execute_search method to raise an exception
    with patch.object(service, '_execute_search', side_effect=Exception("Database connection failed")):
        with pytest.raises(ServiceError):
            await service.get_by_id("BU_ATCC8492")


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_all_abc_method(mock_sync_to_async, mock_strain_hits):
    """Test the ABC get_all method."""
    service = GenomeService()
    
    # Mock the _execute_search method to return our test data
    with patch.object(service, '_execute_search', return_value=mock_strain_hits):
        result = await service.get_all()

        assert len(result) == 2
        assert isinstance(result[0], GenomeResponseSchema)
        assert result[0].isolate_name == "BU_ATCC8492"
        assert result[1].isolate_name == "PV_ATCC8482"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_all_abc_method_with_filters(mock_sync_to_async, mock_strain_hits):
    """Test the ABC get_all method with filters."""
    service = GenomeService()
    
    # Mock the _execute_search method to return our test data
    with patch.object(service, '_execute_search', return_value=[mock_strain_hits[0]]):
        result = await service.get_all(species="BU")

        assert len(result) == 1
        assert isinstance(result[0], GenomeResponseSchema)
        assert result[0].species_acronym == "BU"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_all_abc_method_exception(mock_sync_to_async):
    """Test the ABC get_all method when exception occurs."""
    service = GenomeService()
    
    # Mock the _execute_search method to raise an exception
    with patch.object(service, '_execute_search', side_effect=Exception("Database connection failed")):
        with pytest.raises(ServiceError):
            await service.get_all()


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_abc_method(mock_sync_to_async, mock_strain_hits):
    """Test the ABC search method."""
    service = GenomeService()
    
    # Mock the _execute_search method to return our test data
    with patch.object(service, '_execute_search', return_value=[mock_strain_hits[0]]):
        result = await service.search({"query": "BU"})

        assert len(result) == 1
        assert isinstance(result[0], GenomeResponseSchema)
        assert result[0].isolate_name == "BU_ATCC8492"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_abc_method_with_sorting(mock_sync_to_async, mock_strain_hits):
    """Test the ABC search method with sorting."""
    service = GenomeService()
    
    # Mock the _execute_search method to return our test data
    with patch.object(service, '_execute_search', return_value=mock_strain_hits):
        result = await service.search({
            "query": "test",
            "sort_by": "isolate_name",
            "sort_order": "asc",
            "page": 1,
            "page_size": 10
        })

        assert len(result) == 2
        assert isinstance(result[0], GenomeResponseSchema)


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_abc_method_exception(mock_sync_to_async):
    """Test the ABC search method when exception occurs."""
    service = GenomeService()
    
    # Mock the _execute_search method to raise an exception
    with patch.object(service, '_execute_search', side_effect=Exception("Database connection failed")):
        with pytest.raises(ServiceError):
            await service.search({"query": "test"})


@pytest.mark.asyncio
async def test_convert_hit_to_entity(mock_strain_hits):
    """Test the _convert_hit_to_entity method."""
    service = GenomeService()
    
    result = service._convert_hit_to_entity(mock_strain_hits[0])
    
    assert isinstance(result, GenomeResponseSchema)
    assert result.isolate_name == "BU_ATCC8492"
    assert result.species_scientific_name == "Bacteroides uniformis"


@pytest.mark.asyncio
async def test_create_search():
    """Test the _create_search method from base class."""
    service = GenomeService()
    
    search = service._create_search()
    
    # Verify it's a Search object with correct index
    assert hasattr(search, 'index')
    # The actual index name should match what's defined in the service
    assert service.index_name == "strain_index"


@pytest.mark.asyncio
async def test_handle_elasticsearch_error():
    """Test the _handle_elasticsearch_error method from base class."""
    service = GenomeService()
    
    with pytest.raises(ServiceError):
        service._handle_elasticsearch_error(Exception("Test error"), "test operation")


@pytest.mark.asyncio
async def test_validate_required_fields():
    """Test the _validate_required_fields method from base class."""
    service = GenomeService()
    
    # Test with valid data
    valid_data = {"field1": "value1", "field2": "value2"}
    required_fields = ["field1", "field2"]
    service._validate_required_fields(valid_data, required_fields)  # Should not raise
    
    # Test with missing field
    invalid_data = {"field1": "value1"}
    with pytest.raises(ServiceError):
        service._validate_required_fields(invalid_data, required_fields)


@pytest.mark.asyncio
async def test_resolve_sort_field():
    """Test the _resolve_sort_field method."""
    service = GenomeService()
    
    # Test field mapping
    assert service._resolve_sort_field("species") == "species_acronym"
    assert service._resolve_sort_field("isolate_name") == "isolate_name.keyword"
    assert service._resolve_sort_field("genome") == "isolate_name.keyword"
    assert service._resolve_sort_field("strain") == "isolate_name.keyword"
    assert service._resolve_sort_field("name") == "isolate_name.keyword"
    
    # Test unknown field (should return as-is)
    assert service._resolve_sort_field("unknown_field") == "unknown_field"


@pytest.mark.asyncio
async def test_convert_to_tsv(mock_strain_hits):
    """Test the convert_to_tsv method."""
    service = GenomeService()
    
    # Convert mock hits to GenomeResponseSchema objects
    genomes = [
        service._convert_hit_to_entity(mock_strain_hits[0]),
        service._convert_hit_to_entity(mock_strain_hits[1])
    ]
    
    tsv_result = service.convert_to_tsv(genomes)
    
    assert isinstance(tsv_result, str)
    assert "isolate_name" in tsv_result
    assert "BU_ATCC8492" in tsv_result
    assert "PV_ATCC8482" in tsv_result
    assert "\t" in tsv_result  # Should contain tab separators
