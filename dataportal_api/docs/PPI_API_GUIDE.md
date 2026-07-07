# PPI API Guide

This document explains the four PPI (Protein–Protein Interaction) endpoints and recommends which to use for the Data Portal Network View.

---

## Endpoint comparison

| Endpoint | Method | Purpose | Returns | Best for |
|----------|--------|---------|---------|----------|
| **`/ppi/neighborhood`** | GET | **Top N interactors** by graph distance (Dijkstra on PPI graph). | `protein_id`, `neighbors[]`, `network_data` (nodes + edges). | **UI: “Top N interactors”** – one gene + its closest N neighbors. |
| **`/ppi/network/{score_type}`** | GET | **Network** filtered by score threshold (and optional locus). | `nodes[]`, `edges[]`, optional `properties`. | **UI: “Score threshold”** – same gene-centric view, but by score cutoff. |
| **`/ppi/neighbors`** | GET | **All raw neighbors** for one protein (no graph, no limit). | `protein_id`, `interactions[]`, `unique_neighbors[]`. | **Jupyter / export** – full list of partners, no layout. |
| **`/ppi/interactions`** | GET | **Search** over all PPI rows with filters (paginated). | Paginated list of interaction records. | **Search UI / reports** – find interactions by species, score, evidence, etc. |

---

## 1. `/ppi/neighborhood`

- **Query:** `locus_tag` (or `protein_id`), `n` (1–50), optional `species_acronym`, optional `score_type` (default `ds_score`), optional `score_threshold` (default 0).
- **Logic:** Resolves locus → protein_id. Only interactions with **score ≥ score_threshold** (for the chosen **score_type**) are considered. Among those, the graph is built with edge weight = that score; **Dijkstra** (distance = 1/score) picks the **top N** nearest neighbors. So “top N” = top N by the chosen score, among interactions above the threshold.
- **Use when:** You want “show me this gene and its **N closest** interactors by [score type], above [threshold]” (e.g. “Top 10 by ds_score above 0.5” in the UI).

---

## 2. `/ppi/network/{score_type}`

- **Query:** `score_type`, `score_threshold`, optional `species_acronym`, `isolate_name`, `locus_tag`, `include_properties`.
- **Logic:** Builds a network from **all** PPIs that pass the score threshold (and optional species/isolate). If `locus_tag` is set, filters to interactions that involve that gene (neighborhood by score).
- **Use when:** You want “show me this gene and everyone above a **score threshold**” (e.g. “Score threshold: 0.8”). Also used for expansion (“Show interactions” on a node) and for network properties.

---

## 3. `/ppi/neighbors`

- **Query:** `locus_tag` (or `protein_id`), optional `species_acronym`.
- **Logic:** Returns **all** interaction rows where the protein participates, plus a deduplicated list of neighbor proteins (no graph, no N limit).
- **Use when:** You need the **raw list** of partners (e.g. for notebooks or export), not a laid-out graph.

---

## 4. `/ppi/interactions`

- **Query:** Many optional filters (species, isolate, score_type, score_threshold, protein_id, locus_tag, evidence flags, pagination).
- **Logic:** **Search** over the PPI index with filters; returns paginated interaction records.
- **Use when:** You need **search** (e.g. “all PPIs for species X above threshold Y”) or tables/reports, not the Network View graph.

---

## Recommendation for the Data Portal Network View

- Use **two** endpoints for the two UI modes:
  1. **“Limit by: Top N interactors”** → **`/ppi/neighborhood`** with `n` and optional `species_acronym`.
  2. **“Limit by: Score threshold”** → **`/ppi/network/{score_type}`** with `score_threshold`, `locus_tag`, and optional `species_acronym` / `isolate_name`.

- Keep **`/ppi/neighbors`** and **`/ppi/interactions`** for:
  - **Neighbors:** Jupyter, exports, or future “download partners” features.
  - **Interactions:** Search, filters, and paginated tables.

### Optional API consolidation

If you want a **single** “neighborhood” API for the UI, you could:

- Add a **unified** endpoint, e.g. `GET /ppi/neighborhood-view`, with:
  - `locus_tag` (required)
  - Either **`top_n`** (1–50) **or** **`score_type` + `score_threshold`** (mutually exclusive).
  - Optional `species_acronym`, `isolate_name`.

- Implementation: call the same logic as `/neighborhood` when `top_n` is set; otherwise call the same logic as `/network/{score_type}` with `locus_tag` and `score_threshold`. Response shape can be the same (`network_data` + optional `properties`).

That way the frontend always calls one endpoint for the graph, and you can deprecate or keep the existing `/neighborhood` and `/network` as thin wrappers if needed.

---

## STRING DB integration and environment variables

The **`/ppi/string-network`** endpoint fetches interaction data from the STRING DB API. The backend calls STRING; the React app only calls our backend.

### Backend (Python)

Configure STRING base URLs with environment variables so you can point to a different mirror or override defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `STRING_DB_API_BASE` | `https://string-db.org/api` | STRING API root (used for `/tsv/network`). |
| `STRING_DB_WEB_BASE` | `https://string-db.org` | STRING web UI root (used for `network_url` links). |

Example (e.g. in `.env` or your process manager):

```bash
export STRING_DB_API_BASE="https://string-db.org/api"
export STRING_DB_WEB_BASE="https://string-db.org"
```

If you see 500 errors on `/ppi/string-network`, check that the backend can reach `STRING_DB_API_BASE` (network, proxy, firewall) and that these env vars are set if you use a custom STRING instance.

### React app (Vite)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Backend API base; all PPI and STRING requests go through this. |
| `VITE_STRING_DB_WEB_BASE` | `https://string-db.org` | STRING web base for “View on STRING”–style links in the UI. |

---

## STRING `/ppi/string-network` response structure

The response wraps the STRING API result and adds locus-tag mapping and metadata.

### Top-level

| Field | Description |
|-------|-------------|
| `status` | `"success"` or error indicator. |
| `message` | Human-readable message. |
| `timestamp` | ISO timestamp. |
| `data` | The actual payload (see below). |

### `data`

| Field | Description |
|-------|-------------|
| **`network`** | Array of interaction rows from STRING. Each row describes one edge (protein A – protein B) and its scores. |
| **`network_url`** | Link to view this network on the STRING website. |
| **`identifiers`** | STRING protein ID(s) that were sent to STRING (e.g. the focal gene only when `locus_tag` is used). |
| **`species_taxid`** | NCBI taxonomy ID (e.g. 820 for *Bacteroides uniformis*). |
| **`interaction`** | The PPI pair from our database that was used to resolve STRING IDs (optional). |
| **`focal_preferred_name`** | STRING preferred name of the protein we queried (when requesting by locus). |
| **`data_sources`** | e.g. `["stringdb"]`. |
| **`edges_filtered_unmapped`** | *(When present)* Number of edges removed because one or both proteins had no locus tag mapping. |
| **`unmapped_string_ids`** | *(When present)* STRING IDs that could not be mapped to locus tags. See `string_network_service.py` (STRING_NETWORK_UNMAPPED_FILTER). |

### `network[]` row fields

Each row in `network` corresponds to one STRING interaction. Only edges where both proteins have locus tag mappings are included.

| Field | Description |
|-------|-------------|
| **`stringId_A`**, **`stringId_B`** | STRING protein IDs (format `taxon.protein_id`, e.g. `820.ERS852554_01920`). |
| **`preferredName_A`**, **`preferredName_B`** | STRING’s gene/protein names (e.g. `dnaA`, `dnaN_1`, `polA`). |
| **`locus_tag_A`**, **`locus_tag_B`** | Locus tags when mapped. Edges with unmapped proteins are filtered out. |
| **`ncbiTaxonId`** | NCBI taxonomy ID for the species. |
| **`score`** | Combined interaction score (0–1). |
| **`nscore`** | Neighborhood (genomic context). |
| **`fscore`** | Gene fusion. |
| **`pscore`** | Phylogenetic co-occurrence. |
| **`ascore`** | Co-expression. |
| **`escore`** | Experimental evidence. |
| **`dscore`** | Database annotations. |
| **`tscore`** | Text mining. |

**Filtering:** Edges where either protein lacks a locus tag mapping are removed. Check `edges_filtered_unmapped` and `unmapped_string_ids` when edges are excluded. See `string_network_service.py` (STRING_NETWORK_UNMAPPED_FILTER) for rationale.
