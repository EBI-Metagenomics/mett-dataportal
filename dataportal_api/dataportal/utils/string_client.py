"""
STRING DB API client for fetching protein interaction network data.

https://string-db.org/cgi/help?subpage=api

Base URLs are configurable via environment variables:
  STRING_DB_API_BASE  - API root (default: https://string-db.org/api)
  STRING_DB_WEB_BASE  - Web UI root for network links (default: https://string-db.org)
"""

import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import httpx

logger = logging.getLogger(__name__)

STRING_API_BASE = os.environ.get("STRING_DB_API_BASE", "https://string-db.org/api").rstrip("/")
STRING_WEB_BASE = os.environ.get("STRING_DB_WEB_BASE", "https://string-db.org").rstrip("/")
CALLER_IDENTITY = "mett-dataportal"

# NCBI taxonomy IDs for METT species
SPECIES_TAXID = {
    "bu": 820,  # Bacteroides uniformis
    "pv": 435590,  # Phocaeicola vulgatus
}


def _species_to_taxid(species_acronym: Optional[str]) -> int:
    """Map species acronym to STRING taxonomy ID."""
    if not species_acronym:
        return 820  # default BU
    acr = species_acronym.strip().lower()
    return SPECIES_TAXID.get(acr, 820)


async def fetch_string_network(
    identifiers: List[str],
    species_acronym: Optional[str] = None,
    species_taxid: Optional[int] = None,
    required_score: Optional[float] = None,
    network_type: str = "physical",
) -> Dict[str, Any]:
    """
    Fetch interaction network from STRING DB API.

    Args:
        identifiers: STRING protein IDs (e.g. ["820.ERS852554_01920", "820.ERS852554_01919"])
        species_acronym: Species filter (BU, PV) - used to infer taxid if species_taxid not set
        species_taxid: STRING taxonomy ID (820 for BU, 435590 for PV)
        required_score: Minimum score threshold (0-1000)
        network_type: "physical" or "functional"

    Returns:
        Dict with "network" (list of edges), "network_url" (link to STRING page), "raw_text" (TSV body)
    """
    if not identifiers:
        return {
            "network": [],
            "network_url": None,
            "raw_text": None,
            "error": "No identifiers provided",
        }

    ids_str = "\r".join(identifiers)  # STRING expects newline or carriage return
    taxid = species_taxid or _species_to_taxid(species_acronym)

    params = {
        "identifiers": ids_str,
        "species": taxid,
        "caller_identity": CALLER_IDENTITY,
        "network_type": network_type,
    }
    if required_score is not None:
        params["required_score"] = int(required_score)

    url = f"{STRING_API_BASE}/tsv/network"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            text = resp.text
    except httpx.HTTPStatusError as e:
        logger.warning(
            "STRING API request failed: %s %s response=%s body=%s",
            type(e).__name__,
            e,
            e.response.status_code if e.response is not None else None,
            (e.response.text[:200] if e.response is not None else None) or "",
        )
        return {"network": [], "network_url": None, "raw_text": None, "error": str(e)}
    except httpx.HTTPError as e:
        logger.warning("STRING API request failed: %s %s", type(e).__name__, e, exc_info=True)
        return {"network": [], "network_url": None, "raw_text": None, "error": str(e)}

    # Parse TSV (header + rows)
    lines = text.strip().split("\n")
    network_url = build_string_network_url(
        identifiers, species_acronym=None, species_taxid=taxid, network_type=network_type
    )
    if len(lines) < 2:
        return {
            "network": [],
            "network_url": network_url,
            "raw_text": text,
            "identifiers": identifiers,
            "species_taxid": taxid,
        }

    header = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) >= len(header):
            rows.append(dict(zip(header, parts)))

    return {
        "network": rows,
        "network_url": network_url,
        "raw_text": text,
        "identifiers": identifiers,
        "species_taxid": taxid,
    }


def build_string_network_url(
    identifiers: List[str],
    species_acronym: Optional[str] = None,
    species_taxid: Optional[int] = None,
    network_type: str = "physical",
) -> str:
    """Build a URL to the STRING network page for given protein IDs."""
    if not identifiers:
        return ""
    taxid = species_taxid or _species_to_taxid(species_acronym)
    ids_str = "\r".join(identifiers)
    params = urlencode(
        {
            "identifier": ids_str,
            "species": taxid,
            "caller_identity": CALLER_IDENTITY,
            "network_type": network_type,
        }
    )
    return f"{STRING_WEB_BASE}/cgi/network?{params}"
