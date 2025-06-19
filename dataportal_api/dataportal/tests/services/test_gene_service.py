from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from dataportal.schemas import GenePaginationSchema, GeneResponseSchema
from dataportal.services.gene_service import GeneService
from dataportal.utils.exceptions import GeneNotFoundError


class MockESResponse:
    def __init__(self, hits):
        self.hits = self
        self.total = type("Total", (), {"value": len(hits)})()
        self._hits = hits

    def __iter__(self):
        return iter(self._hits)


# Mocked gene hits
mock_gene1 = MagicMock()
mock_gene1.to_dict.return_value = {
    "locus_tag": "BU_ATCC8492_00001",
    "gene_name": "dnaA",
    "alias": ["BACUNI_01739"],
    "product": "Chromosomal replication initiator protein DnaA",
    "start_position": 1,
    "end_position": 1386,
    "seq_id": "contig_1",
    "isolate_name": "BU_ATCC8492",
    "species_scientific_name": "Bacteroides uniformis",
    "species_acronym": "BU",
    "uniprot_id": "A7V2E8",
    "essentiality": "essential",
    "cog_funcats": ["L"],
    "cog_id": "COG0593",
    "kegg": ["ko:K02313"],
    "pfam": ["PF00308", "PF08299", "PF11638"],
    "interpro": [
        "IPR001957",
        "IPR010921",
        "IPR013159",
        "IPR013317",
        "IPR020591",
        "IPR024633",
        "IPR027417",
        "IPR038454",
    ],
    "ec_number": "null",
    "dbxref": [{"db": "COG", "ref": "COG0593"}, {"db": "UniProt", "ref": "A7V2E8"}],
    "eggnog": "411479.BACUNI_01739",
}

mock_gene2 = MagicMock()
mock_gene2.to_dict.return_value = {
    "locus_tag": "PV_ATCC8482_00001",
    "gene_name": "dnaA",
    "alias": ["BVU_0001"],
    "product": "Chromosomal replication initiator protein DnaA",
    "start_position": 1,
    "end_position": 1407,
    "seq_id": "contig_1",
    "isolate_name": "PV_ATCC8482",
    "species_scientific_name": "Phocaeicola vulgatus",
    "species_acronym": "PV",
    "uniprot_id": "A6KWC5",
    "essentiality": "essential",
    "cog_funcats": ["L"],
    "cog_id": "COG0593",
    "kegg": ["ko:K02313"],
    "pfam": ["PF00308", "PF08299", "PF11638"],
    "interpro": [
        "IPR001957",
        "IPR010921",
        "IPR013159",
        "IPR013317",
        "IPR020591",
        "IPR024633",
        "IPR027417",
        "IPR038454",
    ],
    "ec_number": "null",
    "dbxref": [{"db": "COG", "ref": "COG0593"}, {"db": "UniProt", "ref": "A6KWC5"}],
    "eggnog": "435590.BVU_0001",
}

mock_gene_hits = [mock_gene1, mock_gene2]


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_gene_by_locus_tag(mock_sync_to_async):
    # Return a single mocked Elasticsearch hit (like Django ORM .get())
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = mock_gene1.to_dict.return_value
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_doc)

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
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_gene_hits)
    )

    service = GeneService()
    result = await service.get_all_genes()

    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 2


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_autocomplete_gene_suggestions(mock_sync_to_async):
    # Mock the Search object's execute method
    mock_search = MagicMock()
    mock_search.__iter__.return_value = iter(mock_gene_hits)
    mock_search.hits.total.value = 2
    # mock_search.execute.return_value = MockESResponse(mock_gene_hits)
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_search)

    service = GeneService()
    result = await service.autocomplete_gene_suggestions(query="dnaA")

    assert len(result) == 2
    assert all("dnaA" in gene["gene_name"] for gene in result)


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_autocomplete_gene_suggestions_with_filters(mock_sync_to_async):
    # Mock gene with specific filters
    mock_gene = MagicMock()
    mock_gene.to_dict.return_value = {
        "locus_tag": "BU_ATCC8492_00001",
        "gene_name": "pr",
        "isolate_name": "BU_ATCC8492",
        "essentiality": "essential_liquid",
        "interpro": ["IPR035952"],
    }

    # Mock the Search object's execute method
    mock_search = MagicMock()
    mock_search.execute.return_value = MockESResponse([mock_gene])
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_search)

    service = GeneService()
    result = await service.autocomplete_gene_suggestions(
        query="pr",
        species_acronym="BU",
        isolates=["BU_ATCC8492"],
        filter="essentiality:essential_liquid;interpro:IPR035952",
    )

    assert len(result) == 1
    assert result[0]["gene_name"] == "pr"
    assert result[0]["essentiality"] == "essential_liquid"
    assert "IPR035952" in result[0]["interpro"]


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_faceted_search(mock_sync_to_async):
    # Mock the faceted search response
    mock_facets = {
        "pfam": [{"value": "pf13715", "count": 10, "selected": True}],
        "interpro": [{"value": "ipr011611", "count": 5, "selected": False}],
        "kegg": [{"value": "ko:K02313", "count": 3, "selected": False}],
        "cog_id": [{"value": "COG0593", "count": 2, "selected": False}],
        "cog_funcats": [{"value": "L", "count": 1, "selected": False}],
        "essentiality": [{"value": "essential", "count": 8, "selected": False}],
        "has_amr_info": [{"value": True, "count": 4, "selected": False}],
        "total_hits": 10,
        "operators": {"pfam": "AND", "interpro": "OR"},
    }

    # Mock the GeneFacetedSearch's execute method
    mock_faceted_search = MagicMock()
    mock_faceted_search.execute.return_value = MagicMock(
        facets=MagicMock(
            pfam=[("pf13715", 10)],
            interpro=[("ipr011611", 5)],
            kegg=[("ko:K02313", 3)],
            cog_id=[("COG0593", 2)],
            cog_funcats=[("L", 1)],
            essentiality=[("essential", 8)],
            has_amr_info=[(True, 4)],
        ),
        hits=MagicMock(total=MagicMock(value=10)),
    )
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_faceted_search)

    service = GeneService()
    result = await service.get_faceted_search(
        species_acronym="BU", limit=10, pfam="pf13715"
    )

    assert result["pfam"][0]["selected"] is True
    assert result["total_hits"] == 10
    assert "operators" in result


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_search_genes(mock_sync_to_async):
    # Mock the Search object's execute method
    mock_search = MagicMock()
    mock_search.execute.return_value = MockESResponse(mock_gene_hits)
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_search)

    service = GeneService()
    result = await service.search_genes(
        query="dnaA",
        isolate_name="BU_ATCC8492",
        filter="essentiality:essential",
        page=1,
        per_page=10,
        sort_field="locus_tag",
        sort_order="asc",
    )

    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 2
    assert all(g.isolate_name == "BU_ATCC8492" for g in result.results)


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_search_genes_with_multiple_filters(mock_sync_to_async):
    # Mock the Search object's execute method
    mock_search = MagicMock()
    mock_search.execute.return_value = MockESResponse([mock_gene1])
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_search)

    service = GeneService()
    result = await service.search_genes(
        query="",
        isolate_name="BU_ATCC8492",
        filter="pfam:pf13715;essentiality:not_essential",
        page=1,
        per_page=10,
    )

    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 1
    assert result.results[0].isolate_name == "BU_ATCC8492"


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_gene_protein_seq(mock_sync_to_async):
    # Mock protein sequence response
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {
        "locus_tag": "BU_2243B_00003",
        "protein_sequence": "MAKRRRKYKY",
    }
    mock_search = MagicMock()
    mock_search.execute.return_value = MockESResponse([mock_doc])
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_search)

    service = GeneService()
    result = await service.get_gene_protein_seq("BU_2243B_00003")

    assert result.protein_sequence == "MAKRRRKYKY"
    assert result.locus_tag == "BU_2243B_00003"


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_gene_protein_seq_not_found(mock_sync_to_async):
    # Mock empty response
    mock_search = MagicMock()
    mock_search.execute.return_value = MockESResponse([])
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_search)

    service = GeneService()
    with pytest.raises(GeneNotFoundError):
        await service.get_gene_protein_seq("INVALID_LOCUS_TAG")


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_faceted_search_with_multiple_filters(mock_sync_to_async):
    # Mock the GeneFacetedSearch's execute method
    mock_faceted_search = MagicMock()
    mock_faceted_search.execute.return_value = MagicMock(
        facets=MagicMock(
            pfam=[("pf00294", 10)],
            interpro=[("ipr011611", 5)],
            kegg=[("ko:K02313", 3)],
            cog_id=[("COG0593", 2)],
            cog_funcats=[("L", 1)],
            essentiality=[("essential", 8)],
            has_amr_info=[(True, 4)],
        ),
        hits=MagicMock(total=MagicMock(value=3)),
    )
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_faceted_search)

    service = GeneService()
    result = await service.get_faceted_search(
        species_acronym="BU", limit=5, interpro="ipr011611", pfam="pf00294"
    )

    assert result["pfam"][0]["selected"] is True
    assert result["interpro"][0]["selected"] is True
    assert result["total_hits"] == 3
    assert result["operators"]["pfam"] == "AND"
    assert result["operators"]["interpro"] == "OR"


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_search_genes_with_essentiality(mock_sync_to_async):
    # Create mock gene with essentiality data
    mock_essential_gene = MagicMock()
    mock_essential_gene.to_dict.return_value = {
        "locus_tag": "BU_ATCC8492_00001",
        "gene_name": "dnaA",
        "isolate_name": "BU_ATCC8492",
        "essentiality": "essential",
        "species_acronym": "BU",
    }

    # Mock the Search object's execute method
    mock_search = MagicMock()
    mock_search.execute.return_value = MockESResponse([mock_essential_gene])
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_search)

    service = GeneService()
    result = await service.search_genes(
        query="dna",
        isolate_name="BU_ATCC8492",
        filter="essentiality:essential",
        page=1,
        per_page=10,
    )

    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 1
    assert result.results[0].essentiality == "essential"
    assert result.results[0].isolate_name == "BU_ATCC8492"
