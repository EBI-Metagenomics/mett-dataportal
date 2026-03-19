import logging
from typing import Any, Dict, List, Optional

from dataportal.utils.string_client import fetch_string_network

# --- STRING Network Unmapped Filter (reference for debugging) ---
# Edges where either protein (A or B) lacks a locus tag mapping are REMOVED from the
# network response. Rationale: nodes without locus tags cannot be displayed meaningfully
# or merged with local PPI data in the "both" view. Mapping is resolved via:
# 1) feature index (dbxref.db=STRING), 2) PPI index fallback.
# Response includes edges_filtered_unmapped (count) and unmapped_string_ids (list) when
# any edges were filtered. See get_string_network_for_pair() and logs.
from dataportal.utils.constants import STRING_EVIDENCE_CHANNELS
from dataportal.services.service_factory import ServiceFactory
from dataportal.schema.external.string_schemas import (
    StringNetworkRowSchema,
    StringNetworkMetadataSchema,
    StringNetworkNormalizedSchema,
    StringNetworkResponseSchema,
)
from dataportal.schema.interactions.ppi_schemas import (
    PPINetworkNodeSchema,
    PPINetworkEdgeSchema,
    PPINetworkPropertiesSchema,
)

logger = logging.getLogger(__name__)


class StringNetworkService:
    name = "stringdb"

    def __init__(self):
        self._gene_service = ServiceFactory.get_gene_service()
        self._ppi_service = ServiceFactory.get_ppi_service()
        self._species_service = ServiceFactory.get_species_service()

    def _filter_network_by_evidence(
        self, network: List[Dict[str, Any]], evidence_channels: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Filter network rows to only include edges with score > 0 in at least one selected evidence channel.
        If evidence_channels is None or empty, return all rows (no filter).
        """
        if not evidence_channels:
            return network
        channel_to_score = {c[0]: c[1] for c in STRING_EVIDENCE_CHANNELS}
        valid_channels = set(evidence_channels) & set(channel_to_score)
        if not valid_channels:
            return network
        score_fields = [channel_to_score[c] for c in valid_channels]
        result = []
        for row in network:
            for field in score_fields:
                val = row.get(field)
                try:
                    s = float(val) if val is not None else 0.0
                except (ValueError, TypeError):
                    s = 0.0
                if s > 0.01:  # threshold to exclude noise
                    result.append(row)
                    break
        return result

    def _resolve_ids_to_locus(
        self, string_ids: List[str], species_acronym: Optional[str]
    ) -> Dict[str, str]:
        """Resolve STRING IDs to locus tags from feature index cache."""
        if not string_ids:
            return {}
        _, string_to_locus = self._gene_service.get_locus_string_mapping(
            species_acronym=species_acronym,
        )
        return {sid: string_to_locus[sid] for sid in string_ids if sid in string_to_locus}

    async def _resolve_ids_to_locus_with_ppi_fallback(
        self, string_ids: List[str], species_acronym: Optional[str]
    ) -> Dict[str, str]:
        """Resolve STRING IDs to locus tags: feature index first, then PPI index for missing."""
        if not string_ids:
            return {}
        result = self._resolve_ids_to_locus(string_ids, species_acronym)
        missing = [sid for sid in string_ids if sid and sid not in result]
        if missing:
            ppi_mapping = await self._ppi_service.get_string_ids_to_locus_tag(
                string_ids=missing,
                species_acronym=species_acronym,
            )
            result.update(ppi_mapping)
        return result

    async def get_string_network_for_pair(
        self,
        pair_id: Optional[str] = None,
        protein_ids: Optional[List[str]] = None,
        locus_tag: Optional[str] = None,
        species_acronym: Optional[str] = None,
        required_score: Optional[int] = None,
        add_nodes: Optional[int] = None,
        network_type: str = "physical",
        evidence_channels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Fetch STRING DB network data for a single gene (by locus_tag) or a PPI pair.

        Accepts one of:
        - locus_tag + species_acronym: Resolve locus_tag to STRING ID via feature index cache,
          fetch neighborhood of that protein. No pair_id needed.
        - pair_id (optionally + locus_tag): Lookup interaction from PPI index, get STRING IDs.
          With locus_tag, send only that protein to STRING (neighborhood). Without, send both.
        - protein_ids: Direct STRING IDs to query.
        """
        identifiers: List[str] = []
        interaction: Optional[Dict[str, Any]] = None
        resolved_species: Optional[str] = None

        # Path 1: locus_tag + species_acronym only — resolve via feature index, fallback to PPI index
        if locus_tag and species_acronym and not pair_id and not protein_ids:
            locus_tag_norm = locus_tag.strip()
            locus_to_string, string_to_locus = self._gene_service.get_locus_string_mapping(
                species_acronym=species_acronym
            )
            string_id = locus_to_string.get(locus_tag_norm)
            # Fallback: PPI index may have STRING IDs even when feature index does not
            if not string_id:
                string_id = await self._ppi_service.get_string_id_for_locus_tag(
                    locus_tag=locus_tag_norm,
                    species_acronym=species_acronym,
                )
            if not string_id:
                return {
                    "network": [],
                    "network_url": None,
                    "identifiers": [],
                    "species_taxid": None,
                    "focal_locus_tag": locus_tag_norm,
                    "focal_preferred_name": None,
                    "focal_string_id": None,
                    "data_sources": ["stringdb"],
                    "error": f"Gene '{locus_tag_norm}' has no STRING identifier in the feature index or PPI index.",
                }
            identifiers = [string_id]
            resolved_species = species_acronym

        elif pair_id:
            interaction = await self._ppi_service.get_interaction_by_pair_id(pair_id)
            if not interaction:
                return {
                    "interaction": None,
                    "network": [],
                    "network_url": None,
                    "error": f"PPI pair_id '{pair_id}' not found",
                }
            sa = interaction.get("string_protein_a_id")
            sb = interaction.get("string_protein_b_id")
            if not sa and not sb:
                return {
                    "interaction": interaction,
                    "network": [],
                    "network_url": None,
                    "error": "STRING protein IDs not available for this pair (missing string_protein_a_id or string_protein_b_id)",
                }
            # If locus_tag given, send only the STRING ID for that protein (neighborhood of one gene).
            if locus_tag:
                locus_tag_norm = (locus_tag or "").strip()
                a_tag = (interaction.get("protein_a_locus_tag") or "").strip()
                b_tag = (interaction.get("protein_b_locus_tag") or "").strip()
                if locus_tag_norm and (a_tag or b_tag):
                    if locus_tag_norm == a_tag and sa:
                        identifiers = [sa]
                    elif locus_tag_norm == b_tag and sb:
                        identifiers = [sb]
                    else:
                        identifiers = [sa, sb] if sa and sb else ([sa] if sa else [sb])
                else:
                    identifiers = [sa, sb] if (sa and sb) else ([sa] if sa else [sb])
            else:
                identifiers = [sa, sb] if (sa and sb) else ([sa] if sa else [sb])
            resolved_species = interaction.get("species_acronym") or species_acronym
        elif protein_ids:
            identifiers = [p for p in protein_ids if p]
            resolved_species = species_acronym
        else:
            return {
                "interaction": None,
                "network": [],
                "network_url": None,
                "error": "Provide locus_tag+species_acronym, pair_id, or protein_ids",
            }

        if not identifiers:
            return {
                "interaction": interaction,
                "network": [],
                "network_url": None,
                "error": "No valid STRING protein IDs",
            }

        species_taxid = await self._species_service.get_taxonomy_id(resolved_species)
        result = await fetch_string_network(
            identifiers=identifiers,
            species_taxid=species_taxid,
            required_score=float(required_score) if required_score is not None else None,
            add_nodes=add_nodes,
            network_type=network_type,
        )
        result["interaction"] = interaction
        # For locus_tag-only or locus_tag+pair_id with single protein: expose focal gene info
        if locus_tag and len(identifiers) == 1:
            result["focal_locus_tag"] = locus_tag.strip()
            result["focal_string_id"] = identifiers[0]
        else:
            result["focal_locus_tag"] = None
            result["focal_string_id"] = None
        # Filter by evidence channels if specified
        if result.get("network") and evidence_channels:
            result["network"] = self._filter_network_by_evidence(
                result["network"], evidence_channels
            )
        # When we queried a single focal protein (locus_tag), expose its STRING preferred name
        # so the frontend can merge "both" into one graph by normalizing this node to the local id.
        if locus_tag and len(identifiers) == 1 and result.get("network"):
            first_row = result["network"][0]
            sid = identifiers[0]
            sa_id = first_row.get("stringId_A")
            sb_id = first_row.get("stringId_B")
            if sid == sa_id:
                result["focal_preferred_name"] = first_row.get("preferredName_A")
            elif sid == sb_id:
                result["focal_preferred_name"] = first_row.get("preferredName_B")
            else:
                result["focal_preferred_name"] = None
        else:
            result["focal_preferred_name"] = None

        # Resolve STRING IDs to locus tags and embed locus_tag_A/B in each network row.
        if result.get("network"):
            all_string_ids = []
            for row in result["network"]:
                aid = row.get("stringId_A")
                bid = row.get("stringId_B")
                if aid:
                    all_string_ids.append(aid)
                if bid:
                    all_string_ids.append(bid)
            string_id_to_locus = await self._resolve_ids_to_locus_with_ppi_fallback(
                all_string_ids, species_acronym=resolved_species
            )
            if locus_tag and len(identifiers) == 1:
                focal_string_id = identifiers[0]
                string_id_to_locus[focal_string_id] = locus_tag.strip()
            for row in result["network"]:
                aid = row.get("stringId_A")
                bid = row.get("stringId_B")
                row["locus_tag_A"] = string_id_to_locus.get(aid) if aid else None
                row["locus_tag_B"] = string_id_to_locus.get(bid) if bid else None

            # Filter out edges where either protein lacks a locus tag mapping.
            # Nodes without locus tags cannot be meaningfully displayed/merged with local data.
            # See: STRING_NETWORK_UNMAPPED_FILTER in this module.
            original_count = len(result["network"])
            unmapped_ids: set = set()
            filtered_network = []
            for row in result["network"]:
                locus_a = row.get("locus_tag_A")
                locus_b = row.get("locus_tag_B")
                aid = row.get("stringId_A")
                bid = row.get("stringId_B")
                if locus_a and locus_b:
                    filtered_network.append(row)
                else:
                    if not locus_a and aid:
                        unmapped_ids.add(aid)
                    if not locus_b and bid:
                        unmapped_ids.add(bid)
            result["network"] = filtered_network
            removed_count = original_count - len(filtered_network)
            if removed_count > 0:
                unmapped_list = sorted(unmapped_ids)
                logger.info(
                    "STRING network filtering: removed %d edge(s) with unmapped proteins. "
                    "Unmapped STRING IDs (no locus tag in feature/PPI index): %s. "
                    "Reason: edges require both locus_tag_A and locus_tag_B to be displayed.",
                    removed_count,
                    unmapped_list[:20] if len(unmapped_list) > 20 else unmapped_list,
                )
                result["edges_filtered_unmapped"] = removed_count
                result["unmapped_string_ids"] = sorted(unmapped_ids)
        return result

    async def get_network_for_identifiers(
        self,
        identifiers: List[str],
        species_acronym: Optional[str] = None,
        locus_tag: Optional[str] = None,
        required_score: Optional[float] = None,
        network_type: str = "physical",
        interaction: Optional[Dict[str, Any]] = None,
    ) -> StringNetworkResponseSchema:
        species_taxid = await self._species_service.get_taxonomy_id(species_acronym)
        result = await fetch_string_network(
            identifiers=identifiers,
            species_taxid=species_taxid,
            required_score=required_score,
            network_type=network_type,
        )

        rows_raw = result.get("network", []) or []

        # Build mapping STRING id -> locus_tag (feature index + PPI fallback)
        all_ids: List[str] = []
        for row in rows_raw:
            aid = row.get("stringId_A")
            bid = row.get("stringId_B")
            if aid:
                all_ids.append(aid)
            if bid:
                all_ids.append(bid)
        string_id_to_locus = await self._resolve_ids_to_locus_with_ppi_fallback(
            all_ids, species_acronym
        )
        if locus_tag and len(identifiers) == 1:
            string_id_to_locus[identifiers[0]] = locus_tag.strip()

        # Embed locus_tag_A/B and filter rows (same logic as get_string_network_for_pair)
        rows_filtered: List[Dict[str, Any]] = []
        unmapped_ids: set = set()
        for row_dict in rows_raw:
            r = dict(row_dict)
            aid = r.get("stringId_A")
            bid = r.get("stringId_B")
            locus_a = string_id_to_locus.get(aid)
            locus_b = string_id_to_locus.get(bid)
            r["locus_tag_A"] = locus_a
            r["locus_tag_B"] = locus_b
            if locus_a and locus_b:
                rows_filtered.append(r)
            else:
                if not locus_a and aid:
                    unmapped_ids.add(aid)
                if not locus_b and bid:
                    unmapped_ids.add(bid)
        removed_count = len(rows_raw) - len(rows_filtered)
        if removed_count > 0:
            logger.info(
                "STRING network (get_network_for_identifiers): filtered %d edge(s), unmapped IDs: %s",
                removed_count,
                sorted(unmapped_ids)[:20],
            )

        rows = [StringNetworkRowSchema(**r) for r in rows_filtered]

        # Build normalized nodes/edges
        node_map: Dict[str, PPINetworkNodeSchema] = {}
        edges: List[PPINetworkEdgeSchema] = []

        for row in rows:
            a_locus = string_id_to_locus.get(row.stringId_A)
            b_locus = string_id_to_locus.get(row.stringId_B)

            a_id = a_locus or row.stringId_A
            b_id = b_locus or row.stringId_B

            def ensure_node(
                nid: str,
                locus: Optional[str],
                preferred: Optional[str],
                string_id: str,
            ) -> None:
                if nid in node_map:
                    return
                node_map[nid] = PPINetworkNodeSchema(
                    id=nid,
                    locus_tag=locus,
                    label=locus or string_id,
                    name=preferred,
                    # additional fields for UI:
                    string_id=string_id,
                    string_preferred_name=preferred,
                )

            ensure_node(a_id, a_locus, row.preferredName_A, row.stringId_A)
            ensure_node(b_id, b_locus, row.preferredName_B, row.stringId_B)

            weight = row.score or 0.0
            edges.append(
                PPINetworkEdgeSchema(
                    source=a_id,
                    target=b_id,
                    weight=weight,
                    score_type="stringdb",
                    # extra attributes:
                    dataSource="stringdb",  # matches frontend
                )
            )

        nodes = list(node_map.values())
        n_nodes = len(nodes)
        n_edges = len(edges)
        density = (2 * n_edges) / (n_nodes * (n_nodes - 1)) if n_nodes > 1 else 0.0

        properties = PPINetworkPropertiesSchema(
            num_nodes=n_nodes,
            num_edges=n_edges,
            density=density,
            avg_clustering_coefficient=0.0,
            degree_distribution=[],
        )

        normalized = StringNetworkNormalizedSchema(nodes=nodes, edges=edges, properties=properties)

        metadata = StringNetworkMetadataSchema(
            network_url=result.get("network_url"),
            raw_text=result.get("raw_text"),
            identifiers=result.get("identifiers") or identifiers,
            species_taxid=result.get("species_taxid"),
            focal_preferred_name=result.get("focal_preferred_name"),
            data_sources=["stringdb"],
            edges_filtered_unmapped=removed_count if removed_count > 0 else None,
            unmapped_string_ids=sorted(unmapped_ids) if unmapped_ids else None,
        )

        return StringNetworkResponseSchema(
            rows=rows, metadata=metadata, normalized_network=normalized
        )
