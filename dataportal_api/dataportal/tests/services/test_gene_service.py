from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from dataportal.schemas import GenePaginationSchema, GeneResponseSchema
from dataportal.services.gene_service import GeneService
from dataportal.utils.constants import ES_FIELD_GENE_NAME
from dataportal.utils.exceptions import GeneNotFoundError

class MockESResponse:
    def __init__(self, hits):
        self.hits = type("Hits", (), {"total": type("Total", (), {"value": len(hits)})})()
        self._hits = hits

    def __iter__(self):
        return iter(self._hits)

# Mocked gene hits
mock_gene1 = MagicMock()
mock_gene1.to_dict.return_value = {
    "locus_tag": "BU_ATCC8492_00001",
    "gene_name": "dnaA",
    "alias": [
        "BACUNI_01739"
    ],
    "product": "Chromosomal replication initiator protein DnaA",
    "start_position": 1,
    "end_position": 1386,
    "seq_id": "contig_1",
    "isolate_name": "BU_ATCC8492",
    "species_scientific_name": "Bacteroides uniformis",
    "species_acronym": "BU",
    "uniprot_id": "A7V2E8",
    "essentiality": "essential",
    "cog_funcats": [
        "L"
    ],
    "cog_id": "COG0593",
    "kegg": [
        "ko:K02313"
    ],
    "pfam": [
        "PF00308",
        "PF08299",
        "PF11638"
    ],
    "interpro": [
        "IPR001957",
        "IPR010921",
        "IPR013159",
        "IPR013317",
        "IPR020591",
        "IPR024633",
        "IPR027417",
        "IPR038454"
    ],
    "ec_number": "null",
    "dbxref": [
        {
            "db": "COG",
            "ref": "COG0593"
        },
        {
            "db": "UniProt",
            "ref": "A7V2E8"
        }
    ],
    "eggnog": "411479.BACUNI_01739"
}

mock_gene2 = MagicMock()
mock_gene2.to_dict.return_value = {
    "locus_tag": "PV_ATCC8482_00001",
    "gene_name": "dnaA",
    "alias": [
        "BVU_0001"
    ],
    "product": "Chromosomal replication initiator protein DnaA",
    "start_position": 1,
    "end_position": 1407,
    "seq_id": "contig_1",
    "isolate_name": "PV_ATCC8482",
    "species_scientific_name": "Phocaeicola vulgatus",
    "species_acronym": "PV",
    "uniprot_id": "A6KWC5",
    "essentiality": "essential",
    "cog_funcats": [
        "L"
    ],
    "cog_id": "COG0593",
    "kegg": [
        "ko:K02313"
    ],
    "pfam": [
        "PF00308",
        "PF08299",
        "PF11638"
    ],
    "interpro": [
        "IPR001957",
        "IPR010921",
        "IPR013159",
        "IPR013317",
        "IPR020591",
        "IPR024633",
        "IPR027417",
        "IPR038454"
    ],
    "ec_number": "null",
    "dbxref": [
        {
            "db": "COG",
            "ref": "COG0593"
        },
        {
            "db": "UniProt",
            "ref": "A6KWC5"
        }
    ],
    "eggnog": "435590.BVU_0001"
}

mock_gene_hits = [mock_gene1, mock_gene2]


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_gene_by_locus_tag(mock_sync_to_async):
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_gene_hits[0]))

    service = GeneService()
    result = await service.get_gene_by_locus_tag("BU_ATCC8492_00001")

    assert isinstance(result, GeneResponseSchema)
    assert result.gene_name == "dnaA"


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_gene_by_invalid_locus_tag(mock_sync_to_async):
    mock_sync_to_async.side_effect = Exception("Gene not found")

    service = GeneService()
    with pytest.raises(GeneNotFoundError):
        await service.get_gene_by_locus_tag("999")


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_all_genes(mock_sync_to_async):
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter(mock_gene_hits)
    mock_response.hits.total.value = 2
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_gene_hits))

    service = GeneService()
    result = await service.get_all_genes()

    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 2


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_search_genes(mock_sync_to_async):
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter(mock_gene_hits[:2])
    mock_response.hits.total.value = 2
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_gene_hits))

    service = GeneService()
    result = await service.search_genes(query="gene")

    assert len(result.results) == 2
    assert all("gene" in gene.gene_name for gene in result.results)


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_genes_by_genome(mock_sync_to_async):
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter(mock_gene_hits)
    mock_response.hits.total.value = 2
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_gene_hits))

    service = GeneService()
    result = await service.get_genes_by_genome(isolate_name="BU_ATCC8492")

    assert len(result.results) == 2
    assert all(g.strain_id == 101 for g in result.results)


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_genes_by_multiple_genomes_and_string(mock_sync_to_async):
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter(mock_gene_hits)
    mock_response.hits.total.value = 2
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_gene_hits))

    service = GeneService()
    result = await service.get_genes_by_multiple_genomes_and_string(isolates="BU_ATCC8492,PV_ATCC8482")

    assert len(result.results) == 2
    assert all(g.strain_id in [101, 102] for g in result.results)


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_autocomplete_gene_suggestions(mock_sync_to_async):
    mock_sync_to_async.return_value = AsyncMock(return_value=MockESResponse(mock_gene_hits))

    service = GeneService()
    result = await service.autocomplete_gene_suggestions(query="gene")

    assert len(result) == 2
    assert all("gene" in gene[ES_FIELD_GENE_NAME] for gene in result)
