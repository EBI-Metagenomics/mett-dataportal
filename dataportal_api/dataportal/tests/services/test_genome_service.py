from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from dataportal.schemas import GenomePaginationSchema, GenomeResponseSchema
from dataportal.services.genome_service import GenomeService
from dataportal.utils.constants import STRAIN_FIELD_ISOLATE_NAME


class MockESResponse:
    def __init__(self, hits):
        self.hits = type("Hits", (), {"total": type("Total", (), {"value": len(hits)})})()
        self._hits = hits

    def __iter__(self):
        return iter(self._hits)


@pytest.fixture
def mock_strain_hits():
    hit1 = MagicMock()
    hit1.to_dict.return_value = {
        "id": 1,
        "isolate_name": "BU_001",
        "assembly_name": "ASM001",
        "type_strain": True,
        "fasta_file": "file1.fna",
        "gff_file": "file1.gff",
        "fasta_url": "http://example.com/file1.fna",
        "gff_url": "http://example.com/file1.gff",
        "species_scientific_name": "Bacteroides uniformis",
        "species_acronym": "BU"
    }

    hit2 = MagicMock()
    hit2.to_dict.return_value = {
        "id": 2,
        "isolate_name": "BU_002",
        "assembly_name": "ASM002",
        "type_strain": True,
        "fasta_file": "file2.fna",
        "gff_file": "file2.gff",
        "fasta_url": "http://example.com/file2.fna",
        "gff_url": "http://example.com/file2.gff",
        "species_scientific_name": "Bacteroides uniformis",
        "species_acronym": "BU"
    }

    return [hit1, hit2]


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_type_strains(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_strain_hits))

    service = GenomeService()
    result = await service.get_type_strains()

    assert len(result) == 2
    assert isinstance(result[0], GenomeResponseSchema)
    assert result[0].isolate_name == "BU_001"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_genomes_by_species(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_strain_hits))

    service = GenomeService()
    result = await service.get_genomes_by_species(species_acronym="BU")

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 2
    assert result.results[0].isolate_name.startswith("BU")


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_genome_by_strain_name(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_strain_hits[0])

    service = GenomeService()
    result = await service.get_genome_by_strain_name("BU_001")

    assert result.isolate_name == "BU_001"
    assert result.species_scientific_name == "Bacteroides uniformis"


@patch("dataportal.services.genome_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_strains(mock_sync_to_async, mock_strain_hits):
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_strain_hits))

    service = GenomeService()
    result = await service.search_strains(query="BU")

    assert len(result) == 2
    assert result[0][STRAIN_FIELD_ISOLATE_NAME].startswith("BU")
