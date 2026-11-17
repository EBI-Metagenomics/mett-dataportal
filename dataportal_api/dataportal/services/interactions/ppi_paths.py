"""Shortest METT interaction paths between a small set of genes.

This module does not change neighborhood or expansion search. It loads only
edges that touch the selected genes, then keeps one shortest path per pair.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, Iterable, List, Optional, Sequence

import networkx as nx

from dataportal.schema.interactions.ppi_path_schemas import (
    PPIDisconnectedPairSchema,
    PPIPathNodeSchema,
    PPIPathSchema,
    PPIPathsDataSchema,
)
from dataportal.schema.interactions.ppi_schemas import PPINetworkEdgeSchema
from dataportal.services.interactions.ppi_service import PPIService
from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)

MAX_PATH_STEPS = 2
MAX_EDGES_PER_GENE = 100
MAX_BRIDGE_EDGES = 5000


@dataclass
class PathSeed:
    protein_id: str
    locus_tag: str
    name: Optional[str] = None
    product: Optional[str] = None


@dataclass
class PathEdgeRecord:
    source: str
    target: str
    score: float
    source_locus_tag: Optional[str] = None
    target_locus_tag: Optional[str] = None
    source_name: Optional[str] = None
    target_name: Optional[str] = None
    source_product: Optional[str] = None
    target_product: Optional[str] = None
    pair_id: Optional[str] = None
    consensus_score: Optional[float] = None
    raw_consensus_score: Optional[float] = None
    n_evidence_types: Optional[int] = None
    n_networks_total: Optional[int] = None
    evidence_scores: Optional[dict] = None
    network_counts: Optional[dict] = None
    extra: dict = field(default_factory=dict)


def _distance(score: float) -> float:
    if score > 0:
        return 1.0 / (score + 0.001)
    return 1000.0


def _meta_for(record: PathEdgeRecord, protein_id: str) -> dict:
    if protein_id == record.source:
        return {
            "locus_tag": record.source_locus_tag,
            "name": record.source_name,
            "product": record.source_product,
        }
    return {
        "locus_tag": record.target_locus_tag,
        "name": record.target_name,
        "product": record.target_product,
    }


def _fill_meta(target: dict, incoming: dict) -> None:
    for key, value in incoming.items():
        if value and not target.get(key):
            target[key] = value


def proteins_beyond_seeds(seeds: Sequence[PathSeed], edges: Iterable[PathEdgeRecord]) -> List[str]:
    """Protein ids that appear on seed edges and are not themselves seeds."""
    seed_ids = {seed.protein_id for seed in seeds}
    found: List[str] = []
    seen = set(seed_ids)
    for record in edges:
        for protein_id in (record.source, record.target):
            if protein_id and protein_id not in seen:
                seen.add(protein_id)
                found.append(protein_id)
    return found


def paths_from_edges(
    seeds: Sequence[PathSeed],
    edges: Iterable[PathEdgeRecord],
    max_steps: int = MAX_PATH_STEPS,
) -> PPIPathsDataSchema:
    """One shortest path per seed pair, using only the supplied edges."""
    seed_ids = [seed.protein_id for seed in seeds]
    seed_id_set = set(seed_ids)
    locus_by_id = {seed.protein_id: seed.locus_tag for seed in seeds}
    meta: Dict[str, dict] = {
        seed.protein_id: {"locus_tag": seed.locus_tag, "name": seed.name, "product": seed.product}
        for seed in seeds
    }

    best: Dict[frozenset, PathEdgeRecord] = {}
    graph = nx.Graph()
    graph.add_nodes_from(seed_ids)
    for record in edges:
        if record.source == record.target:
            continue
        _fill_meta(meta.setdefault(record.source, {}), _meta_for(record, record.source))
        _fill_meta(meta.setdefault(record.target, {}), _meta_for(record, record.target))
        key = frozenset((record.source, record.target))
        current = best.get(key)
        if current is None or record.score > current.score:
            best[key] = record

    for record in best.values():
        graph.add_edge(record.source, record.target, weight=_distance(record.score))

    kept_paths: List[List[str]] = []
    disconnected: List[PPIDisconnectedPairSchema] = []
    used_edges: set[frozenset] = set()

    for left, right in combinations(seed_ids, 2):
        try:
            path = nx.shortest_path(graph, left, right, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path = None
        if not path or len(path) - 1 > max_steps:
            disconnected.append(
                PPIDisconnectedPairSchema(
                    locus_tag_a=locus_by_id.get(left, left),
                    locus_tag_b=locus_by_id.get(right, right),
                )
            )
            continue
        kept_paths.append(path)
        for start, end in zip(path, path[1:]):
            used_edges.add(frozenset((start, end)))

    intermediate_ids = []
    seen_intermediate = set()
    for path in kept_paths:
        for protein_id in path[1:-1]:
            if protein_id in seed_id_set or protein_id in seen_intermediate:
                continue
            seen_intermediate.add(protein_id)
            intermediate_ids.append(protein_id)

    def node(protein_id: str, role: str) -> PPIPathNodeSchema:
        info = meta.get(protein_id, {})
        return PPIPathNodeSchema(
            id=protein_id,
            locus_tag=info.get("locus_tag"),
            name=info.get("name"),
            product=info.get("product"),
            role=role,
        )

    path_edges = []
    for key in used_edges:
        record = best[key]
        path_edges.append(
            PPINetworkEdgeSchema(
                source=record.source,
                target=record.target,
                weight=record.score,
                pair_id=record.pair_id,
                consensus_score=record.consensus_score,
                raw_consensus_score=record.raw_consensus_score,
                n_evidence_types=record.n_evidence_types,
                n_networks_total=record.n_networks_total,
                evidence_scores=record.evidence_scores,
                network_counts=record.network_counts,
            )
        )

    return PPIPathsDataSchema(
        seeds=[node(seed.protein_id, "seed") for seed in seeds],
        intermediates=[node(protein_id, "intermediate") for protein_id in intermediate_ids],
        edges=path_edges,
        paths=[
            PPIPathSchema(
                protein_ids=path,
                locus_tags=[
                    meta.get(protein_id, {}).get("locus_tag") or protein_id for protein_id in path
                ],
            )
            for path in kept_paths
        ],
        disconnected_pairs=disconnected,
    )


class PPIPathService:
    """Load a capped METT neighborhood around the seeds and return shortest paths."""

    def __init__(self, ppi_service: Optional[PPIService] = None):
        self._ppi = ppi_service or PPIService()

    async def find_paths(
        self,
        locus_tags: Sequence[str],
        species_acronym: Optional[str],
        score_type: str,
        score_threshold: float,
    ) -> PPIPathsDataSchema:
        seeds = []
        seen_proteins = set()
        for locus_tag in locus_tags:
            protein_id = await self._ppi.resolve_locus_tag_to_protein_id(
                locus_tag=locus_tag,
                species_acronym=species_acronym,
            )
            if protein_id in seen_proteins:
                raise ServiceError(f"Locus tags resolve to the same protein: {locus_tag}")
            seen_proteins.add(protein_id)
            seeds.append(PathSeed(protein_id=protein_id, locus_tag=locus_tag))

        seed_edges: List[PathEdgeRecord] = []
        for seed in seeds:
            seed_edges.extend(
                await self._edges_touching(
                    seed.protein_id,
                    species_acronym=species_acronym,
                    score_type=score_type,
                    score_threshold=score_threshold,
                )
            )
        # A two-step path A–X–B is missed when X–B is not among B's strongest edges.
        # X is already a strong partner of A, so also load edges from those partners
        # back to the selected genes.
        neighbors = proteins_beyond_seeds(seeds, seed_edges)
        bridge_edges = await self._edges_between(
            neighbors,
            [seed.protein_id for seed in seeds],
            species_acronym=species_acronym,
            score_type=score_type,
            score_threshold=score_threshold,
        )
        return paths_from_edges(seeds, [*seed_edges, *bridge_edges], max_steps=MAX_PATH_STEPS)

    async def _edges_touching(
        self,
        protein_id: str,
        species_acronym: Optional[str],
        score_type: str,
        score_threshold: float,
    ) -> List[PathEdgeRecord]:
        score_field = self._ppi._validate_and_normalize_score_field(score_type)
        search = self._ppi._build_base_search(
            species_acronym=species_acronym,
            isolate_name=None,
            score_type=score_type,
            score_threshold=score_threshold,
        )
        search = search.filter("terms", participants=[protein_id])
        search = search.sort({score_field: {"order": "desc"}})
        source = self._ppi._get_standard_source_fields(include_scores=True)
        if score_field not in source:
            source = list(source) + [score_field]
        search = search.source(source)
        search = search[:MAX_EDGES_PER_GENE]
        response = await self._ppi._execute_search(search)
        return self._records_from_hits(response, score_field)

    async def _edges_between(
        self,
        left_ids: Sequence[str],
        right_ids: Sequence[str],
        species_acronym: Optional[str],
        score_type: str,
        score_threshold: float,
    ) -> List[PathEdgeRecord]:
        """Edges that join one protein from each side, above the score threshold."""
        left = [protein_id for protein_id in dict.fromkeys(left_ids) if protein_id]
        right = [protein_id for protein_id in dict.fromkeys(right_ids) if protein_id]
        if not left or not right:
            return []
        score_field = self._ppi._validate_and_normalize_score_field(score_type)
        search = self._ppi._build_base_search(
            species_acronym=species_acronym,
            isolate_name=None,
            score_type=score_type,
            score_threshold=score_threshold,
        )
        search = search.filter("terms", participants=left)
        search = search.filter("terms", participants=right)
        search = search.sort({score_field: {"order": "desc"}})
        source = self._ppi._get_standard_source_fields(include_scores=True)
        if score_field not in source:
            source = list(source) + [score_field]
        search = search.source(source)
        search = search[:MAX_BRIDGE_EDGES]
        response = await self._ppi._execute_search(search)
        return self._records_from_hits(response, score_field)

    def _records_from_hits(self, response, score_field: str) -> List[PathEdgeRecord]:
        records: List[PathEdgeRecord] = []
        for hit in response.hits:
            score = self._ppi._optional_float(hit, score_field) or 0.0
            records.append(
                PathEdgeRecord(
                    source=hit.protein_a,
                    target=hit.protein_b,
                    score=score,
                    source_locus_tag=getattr(hit, "protein_a_locus_tag", None),
                    target_locus_tag=getattr(hit, "protein_b_locus_tag", None),
                    source_name=getattr(hit, "protein_a_name", None),
                    target_name=getattr(hit, "protein_b_name", None),
                    source_product=getattr(hit, "protein_a_product", None),
                    target_product=getattr(hit, "protein_b_product", None),
                    pair_id=getattr(hit, "pair_id", None),
                    consensus_score=self._ppi._optional_float(hit, "consensus_score"),
                    raw_consensus_score=self._ppi._optional_float(hit, "raw_consensus_score"),
                    n_evidence_types=self._ppi._optional_int(hit, "n_evidence_types"),
                    n_networks_total=self._ppi._optional_int(hit, "n_networks_total"),
                    evidence_scores=self._ppi._extract_evidence_scores(hit) or None,
                    network_counts=self._ppi._extract_network_counts(hit) or None,
                )
            )
        return records
