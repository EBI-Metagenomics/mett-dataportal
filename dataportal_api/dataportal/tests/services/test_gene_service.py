from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from dataportal.schema.gene_schemas import (
    GenePaginationSchema,
    GeneResponseSchema,
    GeneSearchQuerySchema,
    GeneFacetedSearchQuerySchema,
    GeneAdvancedSearchQuerySchema,
    GeneAutocompleteQuerySchema,
)
from dataportal.services.gene_service import GeneService
from dataportal.utils.exceptions import GeneNotFoundError, ServiceError


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
    "cog_id": ["COG0593"],
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
    "ec_number": None,
    "dbxref": [{"db": "COG", "ref": "COG0593"}, {"db": "UniProt", "ref": "A7V2E8"}],
    "eggnog": "411479.BACUNI_01739",
    "amr": [],
    "has_amr_info": False,
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
    "cog_id": ["COG0593"],
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
    "ec_number": None,
    "dbxref": [{"db": "COG", "ref": "COG0593"}, {"db": "UniProt", "ref": "A6KWC5"}],
    "eggnog": "435590.BVU_0001",
    "amr": [],
    "has_amr_info": False,
}

mock_gene_hits = [mock_gene1, mock_gene2]


def create_mock_search(mock_hits, total_hits=None):
    """Create a mock Search object that handles chaining properly"""
    mock_search = MagicMock()

    # Make all chained methods return the same mock
    mock_search.query.return_value = mock_search
    mock_search.filter.return_value = mock_search
    mock_search.sort.return_value = mock_search
    mock_search.source.return_value = mock_search
    mock_search.__getitem__.return_value = mock_search
    mock_search.extra.return_value = mock_search

    # Mock the execute method
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter(mock_hits)

    # Create proper hits structure
    mock_hits_obj = MagicMock()
    mock_hits_obj.__iter__.return_value = iter(mock_hits)
    mock_hits_obj.__getitem__.side_effect = lambda idx: mock_hits[idx]
    if total_hits is not None:
        mock_hits_obj.total.value = total_hits
    # Make hits falsy if empty
    mock_hits_obj.__bool__.return_value = bool(mock_hits)
    mock_response.hits = mock_hits_obj

    mock_search.execute.return_value = mock_response

    # Mock to_dict method
    mock_search.to_dict.return_value = {"query": {"match": "test"}}

    return mock_search


@pytest.fixture
def gene_service():
    return GeneService()


@patch("dataportal.services.gene_service.GeneFacetedSearch")
@pytest.mark.asyncio
async def test_faceted_search_and_across_groups(mock_gene_faceted_search, gene_service):
    # Mock the GeneFacetedSearch class
    mock_instance = MagicMock()
    mock_gene_faceted_search.return_value = mock_instance

    # Mock the execute method to return our expected response
    mock_response = MagicMock()
    mock_response.aggregations = {
        "pfam_filtered": {"pfam": {"buckets": [{"key": "PF13715", "doc_count": 10}]}},
        "essentiality_filtered": {
            "essentiality": {"buckets": [{"key": "not_essential", "doc_count": 5}]}
        },
        "has_amr_info_filtered": {
            "has_amr_info": {"buckets": [{"key": False, "doc_count": 3}]}
        },
    }
    mock_response.hits.total.value = 10
    mock_instance.execute.return_value = mock_response

    # Create faceted search query schema
    params = GeneFacetedSearchQuerySchema(
        species_acronym="BU_ATCC8492",
        isolates="BU_ATCC8492",
        essentiality="not_essential",
        pfam="PF13715",
        pfam_operator="OR",
        limit=10,
    )

    response = await gene_service.get_faceted_search(params)

    assert "total_hits" in response
    assert response["total_hits"] > 0
    assert "pfam" in response
    pfam_facet = response["pfam"]
    assert any(entry["selected"] for entry in pfam_facet)
    assert all(isinstance(entry["count"], int) for entry in pfam_facet)

    # Additional checks to ensure AND across groups is enforced
    essentiality_facet = response["essentiality"]
    amr_facet = response["has_amr_info"] if "has_amr_info" in response else []

    assert all(entry["count"] <= response["total_hits"] for entry in essentiality_facet)
    if amr_facet:
        assert all(entry["count"] <= response["total_hits"] for entry in amr_facet)


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


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
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


# --- AUTOCOMPLETE TESTS ---
@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_autocomplete_gene_suggestions(mock_search_class):
    # Use the helper function to create a proper mock
    mock_search = create_mock_search(mock_gene_hits)
    mock_search_class.return_value = mock_search

    service = GeneService()
    params = GeneAutocompleteQuerySchema(query="dnaA", limit=10)
    result = await service.autocomplete_gene_suggestions(params)
    assert len(result) == 2
    assert all("dnaA" in gene["gene_name"] for gene in result)


@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_autocomplete_gene_suggestions_with_filters(mock_search_class):
    mock_gene = MagicMock()
    mock_gene.to_dict.return_value = {
        "locus_tag": "BU_ATCC8492_00001",
        "gene_name": "pr",
        "isolate_name": "BU_ATCC8492",
        "essentiality": "essential_liquid",
        "interpro": ["IPR035952"],
    }

    # Use the helper function to create a proper mock
    mock_search = create_mock_search([mock_gene])
    mock_search_class.return_value = mock_search

    service = GeneService()
    params = GeneAutocompleteQuerySchema(
        query="pr",
        species_acronym="BU",
        isolates="BU_ATCC8492",
        filter="essentiality:essential_liquid;interpro:IPR035952",
        limit=10,
    )
    result = await service.autocomplete_gene_suggestions(params)
    assert len(result) == 1
    assert result[0]["gene_name"] == "pr"
    assert result[0]["essentiality"] == "essential_liquid"
    assert "IPR035952" in result[0]["interpro"]


# --- SEARCH GENES TESTS ---
@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_search_genes(mock_search_class):
    # Use the helper function to create a proper mock
    mock_search = create_mock_search(mock_gene_hits, total_hits=2)
    mock_search_class.return_value = mock_search

    service = GeneService()
    params = GeneSearchQuerySchema(
        query="dnaA", page=1, per_page=10, sort_field="locus_tag", sort_order="asc"
    )
    result = await service.search_genes(params)
    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 2


@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_search_genes_with_multiple_filters(mock_search_class):
    # Use the helper function to create a proper mock
    mock_search = create_mock_search([mock_gene1], total_hits=1)
    mock_search_class.return_value = mock_search

    service = GeneService()
    params = GeneSearchQuerySchema(query="", page=1, per_page=10)
    result = await service.search_genes(params)
    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 1
    assert result.results[0].isolate_name == "BU_ATCC8492"


@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_search_genes_with_essentiality(mock_search_class):
    mock_essential_gene = MagicMock()
    mock_essential_gene.to_dict.return_value = {
        "locus_tag": "BU_ATCC8492_00001",
        "gene_name": "dnaA",
        "isolate_name": "BU_ATCC8492",
        "essentiality": "essential",
        "species_acronym": "BU",
    }

    # Use the helper function to create a proper mock
    mock_search = create_mock_search([mock_essential_gene], total_hits=1)
    mock_search_class.return_value = mock_search

    service = GeneService()
    params = GeneSearchQuerySchema(query="dna", page=1, per_page=10)
    result = await service.search_genes(params)
    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 1
    assert result.results[0].essentiality == "essential"
    assert result.results[0].isolate_name == "BU_ATCC8492"


@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_get_genes_by_multiple_genomes_and_string(mock_search_class):
    # Use the helper function to create a proper mock
    mock_search = create_mock_search(mock_gene_hits, total_hits=2)
    mock_search_class.return_value = mock_search

    service = GeneService()
    params = GeneAdvancedSearchQuerySchema(
        isolates="BU_ATCC8492,PV_ATCC8482",
        species_acronym="BU",
        query="dnaA",
        filter="essentiality:essential",
        filter_operators="essentiality:AND",
        page=1,
        per_page=10,
        sort_field="locus_tag",
        sort_order="asc",
    )
    result = await service.get_genes_by_multiple_genomes_and_string(params)
    assert isinstance(result, GenePaginationSchema)
    assert len(result.results) == 2
    assert result.total_results == 2


# --- PROTEIN SEQUENCE TESTS ---
@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_get_gene_protein_seq(mock_search_class):
    # Mock protein sequence response with all required fields
    class Hit:
        locus_tag = "BU_2243B_00003"
        protein_sequence = "MAKRRRKYKY"

        def to_dict(self):
            return {
                "locus_tag": self.locus_tag,
                "protein_sequence": self.protein_sequence,
            }

    # Use the helper function to create a proper mock
    mock_search = create_mock_search([Hit()])
    mock_search_class.return_value = mock_search

    service = GeneService()
    result = await service.get_gene_protein_seq("BU_2243B_00003")
    assert result.protein_sequence == "MAKRRRKYKY"
    assert result.locus_tag == "BU_2243B_00003"


@patch("dataportal.services.gene_service.Search")
@pytest.mark.asyncio
async def test_get_gene_protein_seq_not_found(mock_search_class):
    # Use the helper function to create a proper mock with empty results
    mock_search = create_mock_search([])
    mock_search_class.return_value = mock_search

    service = GeneService()
    with pytest.raises(GeneNotFoundError):
        await service.get_gene_protein_seq("INVALID_LOCUS_TAG")


# --- FACETED SEARCH OPERATOR TEST ---
@patch("dataportal.services.gene_service.GeneFacetedSearch")
@pytest.mark.asyncio
async def test_get_faceted_search_with_multiple_filters(mock_gene_faceted_search):
    # Mock the GeneFacetedSearch class
    mock_instance = MagicMock()
    mock_gene_faceted_search.return_value = mock_instance
    # Mock the execute method to return our expected response
    mock_response = MagicMock()
    mock_response.aggregations = {
        "pfam_filtered": {"pfam": {"buckets": [{"key": "pf00294", "doc_count": 10}]}},
        "interpro_filtered": {
            "interpro": {"buckets": [{"key": "ipr011611", "doc_count": 5}]}
        },
        "kegg_filtered": {"kegg": {"buckets": [{"key": "ko:K02313", "doc_count": 3}]}},
        "cog_id_filtered": {
            "cog_id": {"buckets": [{"key": "COG0593", "doc_count": 2}]}
        },
        "cog_funcats_filtered": {
            "cog_funcats": {"buckets": [{"key": "L", "doc_count": 1}]}
        },
        "essentiality_filtered": {
            "essentiality": {"buckets": [{"key": "essential", "doc_count": 8}]}
        },
        "has_amr_info_filtered": {
            "has_amr_info": {"buckets": [{"key": True, "doc_count": 4}]}
        },
    }
    mock_response.hits.total.value = 3
    mock_instance.execute.return_value = mock_response

    service = GeneService()
    params = GeneFacetedSearchQuerySchema(
        species_acronym="BU",
        limit=5,
        interpro="ipr011611",
        pfam="pf00294",
        pfam_operator="AND",
        interpro_operator="AND",
    )
    result = await service.get_faceted_search(params)
    assert result["pfam"][0]["selected"] is True
    assert result["interpro"][0]["selected"] is True
    assert result["total_hits"] == 3
    assert result["operators"]["pfam"] == "AND"
    assert result["operators"]["interpro"] == "AND"


# New tests for ABC methods
@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_by_id_success(mock_sync_to_async):
    """Test the ABC get_by_id method."""
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = mock_gene1.to_dict.return_value
    mock_sync_to_async.return_value = AsyncMock(return_value=mock_doc)

    service = GeneService()
    result = await service.get_by_id("BU_ATCC8492_00001")

    assert result is not None
    assert isinstance(result, GeneResponseSchema)
    assert result.gene_name == "dnaA"
    assert result.locus_tag == "BU_ATCC8492_00001"


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_sync_to_async):
    """Test the ABC get_by_id method when gene not found."""
    mock_sync_to_async.side_effect = GeneNotFoundError("Gene not found")

    service = GeneService()
    result = await service.get_by_id("INVALID")

    assert result is None


@pytest.mark.asyncio
@patch("dataportal.services.gene_service.sync_to_async")
async def test_get_by_id_exception(mock_sync_to_async):
    """Test the ABC get_by_id method when exception occurs."""
    service = GeneService()

    # Mock the get_gene_by_locus_tag method to raise an exception
    with patch.object(
        service,
        "get_gene_by_locus_tag",
        side_effect=Exception("Database connection failed"),
    ):
        with pytest.raises(ServiceError):
            await service.get_by_id("BU_ATCC8492_00001")


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_all_abc_method(mock_sync_to_async):
    """Test the ABC get_all method."""
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter(mock_gene_hits)
    mock_response.hits.total.value = 2
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_gene_hits)
    )

    service = GeneService()
    result = await service.get_all()

    assert len(result) == 2
    assert isinstance(result[0], GeneResponseSchema)
    assert result[0].gene_name == "dnaA"
    assert result[1].gene_name == "dnaA"


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_all_abc_method_with_filters(mock_sync_to_async):
    """Test the ABC get_all method with filters."""
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter([mock_gene1])
    mock_response.hits.total.value = 1
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse([mock_gene1])
    )

    service = GeneService()
    result = await service.get_all(species_acronym="BU")

    assert len(result) == 1
    assert isinstance(result[0], GeneResponseSchema)
    assert result[0].species_acronym == "BU"


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_get_all_abc_method_exception(mock_sync_to_async):
    """Test the ABC get_all method when exception occurs."""
    mock_sync_to_async.side_effect = Exception("Database connection failed")

    service = GeneService()
    with pytest.raises(ServiceError):
        await service.get_all()


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_abc_method(mock_sync_to_async):
    """Test the ABC search method."""
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter([mock_gene1])
    mock_response.hits.total.value = 1
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse([mock_gene1])
    )

    service = GeneService()
    result = await service.search({"query": "dnaA"})

    assert len(result) == 1
    assert isinstance(result[0], GeneResponseSchema)
    assert result[0].gene_name == "dnaA"


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_abc_method_with_pagination(mock_sync_to_async):
    """Test the ABC search method with pagination."""
    mock_response = MagicMock()
    mock_response.__iter__.return_value = iter(mock_gene_hits)
    mock_response.hits.total.value = 2
    mock_sync_to_async.return_value = AsyncMock(
        return_value=MockESResponse(mock_gene_hits)
    )

    service = GeneService()
    result = await service.search(
        {
            "query": "dnaA",
            "page": 1,
            "per_page": 10,
            "sort_field": "locus_tag",
            "sort_order": "asc",
        }
    )

    assert len(result) == 2
    assert isinstance(result[0], GeneResponseSchema)


@patch("dataportal.services.gene_service.sync_to_async")
@pytest.mark.asyncio
async def test_search_abc_method_exception(mock_sync_to_async):
    """Test the ABC search method when exception occurs."""
    mock_sync_to_async.side_effect = Exception("Database connection failed")

    service = GeneService()
    with pytest.raises(ServiceError):
        await service.search({"query": "test"})


@pytest.mark.asyncio
async def test_convert_hit_to_entity():
    """Test the _convert_hit_to_entity method."""
    service = GeneService()

    result = service._convert_hit_to_entity(mock_gene1)

    assert isinstance(result, GeneResponseSchema)
    assert result.gene_name == "dnaA"
    assert result.locus_tag == "BU_ATCC8492_00001"


@pytest.mark.asyncio
async def test_create_search():
    """Test the _create_search method from base class."""
    service = GeneService()

    search = service._create_search()

    # Verify it's a Search object with correct index
    assert hasattr(search, "index")
    # The actual index name should match what's defined in the service
    assert service.index_name == "gene_index"


@pytest.mark.asyncio
async def test_handle_elasticsearch_error():
    """Test the _handle_elasticsearch_error method from base class."""
    service = GeneService()

    with pytest.raises(ServiceError):
        service._handle_elasticsearch_error(Exception("Test error"), "test operation")


@pytest.mark.asyncio
async def test_validate_required_fields():
    """Test the _validate_required_fields method from base class."""
    service = GeneService()

    # Test with valid data
    valid_data = {"field1": "value1", "field2": "value2"}
    required_fields = ["field1", "field2"]
    service._validate_required_fields(valid_data, required_fields)  # Should not raise

    # Test with missing field
    invalid_data = {"field1": "value1"}
    with pytest.raises(ServiceError):
        service._validate_required_fields(invalid_data, required_fields)


@pytest.mark.asyncio
async def test_parse_filters():
    """Test the _parse_filters method."""
    service = GeneService()

    # Test valid filter string
    filter_str = "essentiality:essential,not_essential;pfam:PF00308,PF08299"
    result = service._parse_filters(filter_str)

    assert result["essentiality"] == ["essential", "not_essential"]
    assert result["pfam"] == ["PF00308", "PF08299"]

    # Test empty filter string
    assert service._parse_filters("") == {}
    assert service._parse_filters(None) == {}

    # Test invalid filter string
    with pytest.raises(ServiceError):
        service._parse_filters("invalid_filter_format")


@pytest.mark.asyncio
async def test_parse_filter_operators():
    """Test the _parse_filter_operators method."""
    service = GeneService()

    # Test valid operators string
    operators_str = "essentiality:AND;pfam:OR"
    result = service._parse_filter_operators(operators_str)

    assert result["essentiality"] == "AND"
    assert result["pfam"] == "OR"

    # Test empty operators string
    assert service._parse_filter_operators("") == {}
    assert service._parse_filter_operators(None) == {}

    # Test invalid operators string
    with pytest.raises(ServiceError):
        service._parse_filter_operators("invalid_operators_format")


@pytest.mark.asyncio
async def test_convert_to_tsv():
    """Test the convert_to_tsv method."""
    service = GeneService()

    # Convert mock genes to GeneResponseSchema objects
    genes = [
        service._convert_hit_to_entity(mock_gene1),
        service._convert_hit_to_entity(mock_gene2),
    ]

    tsv_result = service.convert_to_tsv(genes)

    assert isinstance(tsv_result, str)
    assert "isolate_name" in tsv_result
    assert "gene_name" in tsv_result
    assert "BU_ATCC8492" in tsv_result
    assert "PV_ATCC8482" in tsv_result
    assert "dnaA" in tsv_result
    assert "\t" in tsv_result  # Should contain tab separators
