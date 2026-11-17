"""Path search behaviour, without Elasticsearch."""

import pytest
from pydantic import ValidationError

from dataportal.schema.interactions.ppi_path_schemas import PPIPathsQuerySchema
from dataportal.services.interactions.ppi_paths import (
    PPIPathService,
    PathEdgeRecord,
    PathSeed,
    paths_from_edges,
    proteins_beyond_seeds,
)


def _edge(
    source: str, target: str, score: float, source_locus: str, target_locus: str
) -> PathEdgeRecord:
    return PathEdgeRecord(
        source=source,
        target=target,
        score=score,
        source_locus_tag=source_locus,
        target_locus_tag=target_locus,
    )


def test_direct_edge_is_the_path():
    seeds = [PathSeed("P1", "BU_A"), PathSeed("P2", "BU_B")]
    result = paths_from_edges(seeds, [_edge("P1", "P2", 0.9, "BU_A", "BU_B")])
    assert [edge.source for edge in result.edges] == ["P1"]
    assert result.edges[0].target == "P2"
    assert result.intermediates == []
    assert result.disconnected_pairs == []
    assert result.paths[0].locus_tags == ["BU_A", "BU_B"]


def test_two_step_path_includes_the_intermediate():
    seeds = [PathSeed("P1", "BU_A"), PathSeed("P2", "BU_B")]
    edges = [
        _edge("P1", "PX", 0.8, "BU_A", "BU_X"),
        _edge("PX", "P2", 0.7, "BU_X", "BU_B"),
    ]
    result = paths_from_edges(seeds, edges)
    assert [node.locus_tag for node in result.intermediates] == ["BU_X"]
    assert result.paths[0].locus_tags == ["BU_A", "BU_X", "BU_B"]
    assert len(result.edges) == 2
    assert result.disconnected_pairs == []


def test_disconnected_pair_is_listed_without_dropping_the_other_path():
    seeds = [PathSeed("P1", "BU_A"), PathSeed("P2", "BU_B"), PathSeed("P3", "BU_C")]
    result = paths_from_edges(seeds, [_edge("P1", "P2", 0.5, "BU_A", "BU_B")])
    assert len(result.edges) == 1
    pairs = {(item.locus_tag_a, item.locus_tag_b) for item in result.disconnected_pairs}
    assert pairs == {("BU_A", "BU_C"), ("BU_B", "BU_C")}


def test_no_paths_returns_no_edges():
    seeds = [PathSeed("P1", "BU_A"), PathSeed("P2", "BU_B")]
    result = paths_from_edges(seeds, [])
    assert result.edges == []
    assert result.paths == []
    assert result.intermediates == []
    assert len(result.seeds) == 2
    assert len(result.disconnected_pairs) == 1


def test_neighbors_are_the_partners_on_seed_edges():
    seeds = [PathSeed("P1", "PV_A"), PathSeed("P2", "PV_B")]
    edges = [
        _edge("P1", "PX", 0.4, "PV_A", "PV_X"),
        _edge("P1", "P2", 0.2, "PV_A", "PV_B"),
    ]
    assert proteins_beyond_seeds(seeds, edges) == ["PX"]


@pytest.mark.asyncio
async def test_two_step_path_is_found_when_the_second_edge_is_not_on_the_other_seed():
    """00621-01387 is on the first gene, but 01387-02115 is not among the second gene's top edges."""

    class FakePPI:
        async def resolve_locus_tag_to_protein_id(self, locus_tag, species_acronym=None):
            return {"PV_A": "P1", "PV_B": "P2"}[locus_tag]

    class Stub(PPIPathService):
        async def _edges_touching(self, protein_id, species_acronym, score_type, score_threshold):
            if protein_id == "P1":
                return [_edge("P1", "PX", 0.4, "PV_A", "PV_X")]
            return []

        async def _edges_between(
            self, left_ids, right_ids, species_acronym, score_type, score_threshold
        ):
            assert left_ids == ["PX"]
            assert "P2" in right_ids
            return [_edge("PX", "P2", 0.35, "PV_X", "PV_B")]

    result = await Stub(FakePPI()).find_paths(["PV_A", "PV_B"], "PV", "consensus_score", 0.0)
    assert [node.locus_tag for node in result.intermediates] == ["PV_X"]
    assert result.paths[0].locus_tags == ["PV_A", "PV_X", "PV_B"]
    assert result.disconnected_pairs == []


def test_schema_rejects_sets_outside_two_to_five():
    with pytest.raises(ValidationError):
        PPIPathsQuerySchema(locus_tags=["BU_A"])
    with pytest.raises(ValidationError):
        PPIPathsQuerySchema(locus_tags=["A", "B", "C", "D", "E", "F"])


def test_schema_rejects_duplicate_locus_tags():
    with pytest.raises(ValidationError):
        PPIPathsQuerySchema(locus_tags=["BU_A", "BU_A"])
