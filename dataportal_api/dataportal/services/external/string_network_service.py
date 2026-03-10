import logging
from typing import Any, Dict, List, Optional

from dataportal.utils.string_client import fetch_string_network
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

    def _resolve_ids_to_locus(
        self, string_ids: List[str], species_acronym: Optional[str]
    ) -> Dict[str, str]:
        if not string_ids:
            return {}
        _, string_to_locus = self._gene_service.get_locus_string_mapping(
            species_acronym=species_acronym,
        )
        return {sid: string_to_locus[sid] for sid in string_ids if sid in string_to_locus}

    async def get_string_network_for_pair(
        self,
        pair_id: Optional[str] = None,
        protein_ids: Optional[List[str]] = None,
        locus_tag: Optional[str] = None,
        species_acronym: Optional[str] = None,
        required_score: Optional[int] = None,
        network_type: str = "physical",
    ) -> Dict[str, Any]:
        """
        Fetch STRING DB network data for a PPI pair or a single protein.

        Either pair_id (lookup from ES) or protein_ids (direct STRING IDs) must be provided.
        When pair_id is used with locus_tag, only the STRING ID for that protein is sent to STRING,
        so STRING returns the neighborhood of that one gene (interactors of the selected protein).
        Without locus_tag, both proteins in the pair are sent and STRING returns the combined subnetwork.
        """
        identifiers: List[str] = []
        interaction: Optional[Dict[str, Any]] = None
        resolved_species: Optional[str] = None

        if pair_id:
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
                "error": "Either pair_id or protein_ids must be provided",
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
            network_type=network_type,
        )
        result["interaction"] = interaction
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

        # Resolve STRING preferred names to locus tags so the frontend can show locus tags consistently.
        preferred_name_to_locus: Dict[str, str] = {}
        if result.get("network"):
            all_string_ids = []
            for row in result["network"]:
                aid = row.get("stringId_A")
                bid = row.get("stringId_B")
                if aid:
                    all_string_ids.append(aid)
                if bid:
                    all_string_ids.append(bid)
            string_id_to_locus = self._resolve_ids_to_locus(
                all_string_ids, species_acronym=resolved_species
            )
            # Always add the focal protein's mapping from the interaction (locus_tag ↔ string_id)
            # so the searched node merges in "both" view even when the feature-index cache missed it.
            if locus_tag and len(identifiers) == 1:
                focal_string_id = identifiers[0]
                string_id_to_locus[focal_string_id] = locus_tag.strip()
            for row in result["network"]:
                aid = row.get("stringId_A")
                bid = row.get("stringId_B")
                pna = row.get("preferredName_A")
                pnb = row.get("preferredName_B")
                if pna and aid and aid in string_id_to_locus:
                    preferred_name_to_locus[str(pna)] = string_id_to_locus[aid]
                if pnb and bid and bid in string_id_to_locus:
                    preferred_name_to_locus[str(pnb)] = string_id_to_locus[bid]
        result["preferred_name_to_locus_tag"] = preferred_name_to_locus
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
        rows = [StringNetworkRowSchema(**row) for row in rows_raw]

        # Build mapping STRING id -> locus_tag using feature index
        all_ids: List[str] = []
        for row in rows:
            all_ids.append(row.stringId_A)
            all_ids.append(row.stringId_B)
        string_id_to_locus = self._resolve_ids_to_locus(all_ids, species_acronym)

        # Safety net: if we queried a single focal id with locus_tag, enforce that mapping
        if locus_tag and len(identifiers) == 1:
            string_id_to_locus[identifiers[0]] = locus_tag.strip()

        preferred_name_to_locus: Dict[str, str] = {}
        for row in rows:
            if row.preferredName_A and row.stringId_A in string_id_to_locus:
                preferred_name_to_locus[row.preferredName_A] = string_id_to_locus[row.stringId_A]
            if row.preferredName_B and row.stringId_B in string_id_to_locus:
                preferred_name_to_locus[row.preferredName_B] = string_id_to_locus[row.stringId_B]

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
            preferred_name_to_locus_tag=preferred_name_to_locus,
            data_sources=["stringdb"],
        )

        return StringNetworkResponseSchema(
            rows=rows, metadata=metadata, normalized_network=normalized
        )
