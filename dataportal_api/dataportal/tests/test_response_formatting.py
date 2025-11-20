from django.http import HttpResponse

from dataportal.schema.response_schemas import SuccessResponseSchema
from dataportal.utils.response_wrappers import wrap_success_response
from dataportal.utils.serialization import serialize_to_tsv


def test_serialize_to_tsv_flatten_list_of_dicts():
    data = [
        {"foo": 1, "bar": "alpha"},
        {"foo": 2, "baz": "beta"},
    ]

    tsv = serialize_to_tsv(data)
    lines = [line for line in tsv.strip().split("\n") if line]

    assert lines[0] == "foo\tbar\tbaz"
    assert lines[1] == "1\talpha\t"
    assert lines[2] == "2\t\tbeta"


def test_wrap_success_response_returns_tsv_when_requested():
    class DummyRequest:
        GET = {"format": "tsv"}

    @wrap_success_response
    def sample_view(request):
        return [{"foo": 1, "bar": "alpha"}]

    response = sample_view(DummyRequest())

    assert isinstance(response, HttpResponse)
    assert response["Content-Type"] == "text/tab-separated-values"
    assert response.content.decode().startswith("foo")


def test_wrap_success_response_returns_schema_by_default():
    class DummyRequest:
        GET = {}

    @wrap_success_response
    def sample_view(request):
        return {"foo": "bar"}

    response = sample_view(DummyRequest())

    assert isinstance(response, SuccessResponseSchema)
    assert response.data == {"foo": "bar"}


def test_serialize_to_tsv_denormalizes_nested_arrays():
    """Test that nested arrays of objects are expanded into separate rows."""
    data = [
        {
            "gene": "gene_A",
            "locus_tag": "A_001",
            "mutant_growth": [
                {"doubling_time": 1.2, "media": "caecal"},
                {"doubling_time": 1.5, "media": "minimal"},
            ],
        }
    ]

    tsv = serialize_to_tsv(data)
    lines = [line for line in tsv.strip().split("\n") if line]

    # Should have header + 2 data rows (one per mutant_growth entry)
    assert len(lines) == 3
    assert "gene" in lines[0]
    assert "locus_tag" in lines[0]
    assert "doubling_time" in lines[0]
    assert "media" in lines[0]
    assert "mutant_growth" not in lines[0]  # Original array field should be removed

    # Check first expanded row
    row1_fields = lines[1].split("\t")
    assert "gene_A" in row1_fields
    assert "A_001" in row1_fields
    assert "1.2" in row1_fields or "1.2" in row1_fields
    assert "caecal" in row1_fields

    # Check second expanded row
    row2_fields = lines[2].split("\t")
    assert "gene_A" in row2_fields
    assert "A_001" in row2_fields
    assert "1.5" in row2_fields or "1.5" in row2_fields
    assert "minimal" in row2_fields


def test_serialize_to_tsv_handles_multiple_nested_arrays():
    """Test that multiple nested arrays create a cartesian product."""
    data = [
        {
            "gene": "gene_A",
            "array1": [{"x": 1}, {"x": 2}],
            "array2": [{"y": "a"}, {"y": "b"}],
        }
    ]

    tsv = serialize_to_tsv(data)
    lines = [line for line in tsv.strip().split("\n") if line]

    # Should have header + 4 data rows (2x2 cartesian product)
    assert len(lines) == 5
    assert "gene" in lines[0]
    assert "x" in lines[0]
    assert "y" in lines[0]
    assert "array1" not in lines[0]
    assert "array2" not in lines[0]


def test_serialize_to_tsv_handles_records_without_arrays():
    """Test that records without nested arrays work as before."""
    data = [
        {"gene": "A", "value": 1},
        {"gene": "B", "value": 2},
    ]

    tsv = serialize_to_tsv(data)
    lines = [line for line in tsv.strip().split("\n") if line]

    assert len(lines) == 3  # header + 2 rows
    assert lines[0] == "gene\tvalue"
    assert "A" in lines[1]
    assert "B" in lines[2]
