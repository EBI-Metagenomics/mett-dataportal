from unittest.mock import MagicMock, PropertyMock

import pytest

from dataportal.schemas import GenomePaginationSchema, SearchGenomeSchema
from dataportal.services.genome_service import GenomeService


def create_mock_strain1():
    mock_strain = MagicMock(spec=SearchGenomeSchema)
    mock_strain.id = 4
    mock_strain.isolate_name = "BU_909"
    mock_strain.assembly_name = "BU_909_NT5401.1"
    mock_strain.assembly_accession = "A123456"
    mock_strain.fasta_file = "BU_909_NT5401.1.fasta"
    mock_strain.gff_file = "BU_909_annotations.gff"

    # Mock species
    mock_strain.species = MagicMock()
    mock_strain.species.scientific_name = "Bacteroides uniformis"
    mock_strain.species.common_name = "Bacteroides"

    # Mock contigs
    mock_contig = MagicMock()
    type(mock_contig).seq_id = PropertyMock(return_value="contig1")
    type(mock_contig).length = PropertyMock(return_value=1000)
    mock_strain.contigs = MagicMock()
    mock_strain.contigs.all.return_value = [mock_contig]

    return mock_strain


def create_mock_strain2():
    mock_strain = MagicMock(spec=SearchGenomeSchema)
    mock_strain.id = 62
    mock_strain.isolate_name = "PV_ATCC8482"
    mock_strain.assembly_name = "PV_ATCC8482DSM1447_NT5001.1"
    mock_strain.assembly_accession = "A876544"
    mock_strain.fasta_file = "PV_ATCC8482DSM1447_NT5001.1.fa"
    mock_strain.gff_file = "PV_ATCC8482_annotations.gff"

    # Mock species
    mock_strain.species = MagicMock()
    mock_strain.species.scientific_name = "Phocaeicola vulgatus"
    mock_strain.species.common_name = "Bacteroides vulgatus"

    mock_contig = MagicMock()
    type(mock_contig).seq_id = PropertyMock(return_value="contig1")
    type(mock_contig).length = PropertyMock(return_value=1000)
    mock_strain.contigs = MagicMock()
    mock_strain.contigs.all.return_value = [mock_contig]

    return mock_strain


@pytest.mark.asyncio
async def test_get_type_strains(mocker):
    mock_strain_1 = create_mock_strain1()
    mock_strain_2 = create_mock_strain2()
    mocker.patch("dataportal.models.Strain.objects.filter", return_value=[mock_strain_1, mock_strain_2])

    genome_service = GenomeService()
    result = await genome_service.get_type_strains()
    assert isinstance(result, list)
    assert result[0].isolate_name == "BU_909"


@pytest.mark.asyncio
async def test_search_genomes_by_string(mocker):
    mock_strain = create_mock_strain1()
    mocker.patch.object(GenomeService, "_fetch_paginated_strains", return_value=([mock_strain], 1))

    genome_service = GenomeService()
    result = await genome_service.search_genomes_by_string("Strain", page=1, per_page=10)

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 1


@pytest.mark.asyncio
async def test_get_genomes_by_species(mocker):
    mock_strain = create_mock_strain1()
    mocker.patch.object(GenomeService, "_fetch_paginated_strains", return_value=([mock_strain], 1))

    genome_service = GenomeService()
    result = await genome_service.get_genomes_by_species(species_id=1, page=1, per_page=10)

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 1


@pytest.mark.asyncio
async def test_search_genomes_by_species_and_string(mocker):
    mock_strain = create_mock_strain1()
    mocker.patch.object(GenomeService, "_fetch_paginated_strains", return_value=([mock_strain], 1))

    genome_service = GenomeService()
    result = await genome_service.search_genomes_by_species_and_string(species_id=1, query="Strain", page=1,
                                                                       per_page=10)

    assert isinstance(result, GenomePaginationSchema)
    assert result.total_results == 1


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_get_genome_by_id(mocker):
    mock_strain = create_mock_strain1()
    mock_get = mocker.patch("dataportal.models.Strain.objects.select_related")
    mock_get.return_value.get.return_value = mock_strain

    genome_service = GenomeService()
    result = await genome_service.get_genome_by_id(genome_id=1)

    assert result.isolate_name == "BU_909"
