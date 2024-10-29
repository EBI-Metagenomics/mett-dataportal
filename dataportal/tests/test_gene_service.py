from unittest.mock import MagicMock

import pytest

from dataportal.schemas import GeneResponseSchema, GenePaginationSchema
from dataportal.services.gene_service import GeneService


def create_mock_gene():
    mock_gene = MagicMock()
    mock_gene.id = 1
    mock_gene.gene_name = "geneA"
    mock_gene.description = "Sample gene description"
    mock_gene.seq_id = "seq123"
    mock_gene.locus_tag = "LOC123"
    mock_gene.cog = "COG123"
    mock_gene.kegg = "K123"
    mock_gene.pfam = "PF123"
    mock_gene.interpro = "INTERPRO123"
    mock_gene.dbxref = "DBX123"
    mock_gene.ec_number = "EC123"
    mock_gene.product = "Gene Product"
    mock_gene.start_position = 100
    mock_gene.end_position = 200
    mock_gene.annotations = {}

    # Mock the strain
    mock_strain = MagicMock()
    mock_strain.id = 1
    mock_strain.isolate_name = "StrainA"
    mock_strain.assembly_name = "AssemblyA"
    mock_gene.strain = mock_strain

    return mock_gene


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_autocomplete_gene_suggestions(mocker):
    mock_gene = create_mock_gene()
    mocker.patch.object(GeneService, "_fetch_paginated_genes", return_value=([mock_gene], 1))

    gene_service = GeneService()
    results = await gene_service.autocomplete_gene_suggestions(query="geneA", limit=10)

    # Validate
    assert isinstance(results, list)
    assert results[0]["gene_name"] == "geneA"
    assert results[0]["strain_name"] == "StrainA"


@pytest.mark.asyncio
async def test_get_gene_by_id(mocker):
    mock_gene = create_mock_gene()
    mocker.patch("dataportal.services.gene_service.get_object_or_404", return_value=mock_gene)

    gene_service = GeneService()
    result = await gene_service.get_gene_by_id(gene_id=1)

    # Assertions
    assert isinstance(result, GeneResponseSchema)
    assert result.gene_name == "geneA"
    assert result.strain == "StrainA"


@pytest.mark.asyncio
async def test_get_all_genes(mocker):
    mock_gene = create_mock_gene()
    mocker.patch.object(GeneService, "_fetch_paginated_genes", return_value=([mock_gene], 1))

    gene_service = GeneService()
    result = await gene_service.get_all_genes(page=1, per_page=10)

    assert isinstance(result, GenePaginationSchema)
    assert result.results[0].gene_name == "geneA"
    assert result.page_number == 1
    assert result.total_results == 1


@pytest.mark.asyncio
async def test_search_genes(mocker):
    mock_gene = create_mock_gene()
    mocker.patch.object(GeneService, "_fetch_paginated_genes", return_value=([mock_gene], 1))

    gene_service = GeneService()
    result = await gene_service.search_genes(query="geneA", page=1, per_page=10)

    assert isinstance(result, GenePaginationSchema)
    assert result.results[0].gene_name == "geneA"
    assert result.total_results == 1


@pytest.mark.asyncio
async def test_get_genes_by_genome(mocker):
    mock_gene = create_mock_gene()
    mocker.patch.object(GeneService, "_fetch_paginated_genes", return_value=([mock_gene], 1))

    gene_service = GeneService()
    result = await gene_service.get_genes_by_genome(genome_id=1, page=1, per_page=10)

    assert isinstance(result, GenePaginationSchema)
    assert result.results[0].gene_name == "geneA"
    assert result.total_results == 1


@pytest.mark.asyncio
async def test_get_genes_by_multiple_genomes(mocker):
    mock_gene = create_mock_gene()
    mocker.patch.object(GeneService, "_fetch_paginated_genes", return_value=([mock_gene], 1))

    gene_service = GeneService()
    result = await gene_service.get_genes_by_multiple_genomes(genome_ids=[1, 2], page=1, per_page=10)

    # Assertions
    assert isinstance(result, GenePaginationSchema)
    assert result.results[0].gene_name == "geneA"
    assert result.total_results == 1
