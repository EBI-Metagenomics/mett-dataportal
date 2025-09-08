from collections import defaultdict
from typing import Dict, Any, List

from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import chunks_from_table


def _keys_map(d: Dict[str, Any]) -> Dict[str, str]:
    """Map lowercase/stripped -> original column keys to allow case-insensitive access."""
    return {str(k).lower().strip(): k for k in d.keys()}


def _get(d: Dict[str, Any], km: Dict[str, str], *names, default=None):
    for n in names:
        k = km.get(str(n).lower().strip())
        if k is not None:
            return d.get(k, default)
    return default


class Reactions(Flow):
    """
    Imports:
      1) Gene→Reaction
      2) Metabolite edges
      3) Reaction→GPR

    Expected columns (case-insensitive):
      Gene→Reaction:      Gene | gene | locus_tag | GeneID   AND  Reaction | reaction | rxn
      Metabolite edges:   Substrates | substrates | subs | left, Reaction | reaction | rxn, Products | products | prods | right
      Reaction→GPR:       Reaction | reaction | rxn, GPR | gpr | rule
    """

    def run(self, gene_rx_path: str, met_rx_path: str, rx_gpr_path: str, chunksize: int = 50_000) -> None:
        # 1) load metabolite edges
        rx_edges = self._load_edges(met_rx_path)

        # 2) load GPR
        rx_gpr = self._load_gpr(rx_gpr_path)

        # 3) stream gene→reaction
        actions: List[Dict[str, Any]] = []
        total_rows = 0
        total_actions = 0

        first_cols_printed = False
        for chunk in chunks_from_table(gene_rx_path, chunksize=chunksize):
            # diagnostics: show columns once
            if not first_cols_printed:
                print(f"[reactions] Gene→Reaction columns: {list(chunk.columns)}")
                first_cols_printed = True

            for rec in chunk.to_dict(orient="records"):
                total_rows += 1
                km = _keys_map(rec)
                gene = _get(rec, km, "Gene", "gene", "locus_tag", "GeneID")
                rx = _get(rec, km, "Reaction", "reaction", "rxn")
                if not gene or not rx:
                    continue
                gene = str(gene).strip()
                rx = str(rx).strip()
                if not gene or not rx:
                    continue

                # reactions (string array)
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": gene,
                    "script": {
                        "source": """
if (ctx._source.reactions == null) { ctx._source.reactions = []; }
if (!ctx._source.reactions.contains(params.r)) { ctx._source.reactions.add(params.r); }
ctx._source.has_reactions = true;
""",
                        "params": {"r": rx},
                    },
                    "upsert": {"feature_id": gene, "feature_type": "gene", "reactions": [rx], "has_reactions": True},
                    "scripted_upsert": True,
                })

                # reaction_details (nested, dedup by reaction)
                entry = {
                    "reaction": rx,
                    "gpr": rx_gpr.get(rx),
                    "substrates": rx_edges.get(rx, {}).get("substrates", []),
                    "products": rx_edges.get(rx, {}).get("products", []),
                    "metabolites": sorted(set(
                        rx_edges.get(rx, {}).get("substrates", []) +
                        rx_edges.get(rx, {}).get("products", [])
                    )),
                }
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": gene,
                    "script": {
                        "source": SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS + "\nctx._source.has_reactions = true;",
                        "params": {"field": "reaction_details", "entry": entry, "keys": ["reaction"]},
                    },
                    "upsert": {"feature_id": gene, "feature_type": "gene", "reaction_details": [entry],
                               "has_reactions": True},
                    "scripted_upsert": True,
                })

                if len(actions) >= 1000:
                    bulk_exec(actions);
                    total_actions += len(actions);
                    actions.clear()

        if actions:
            bulk_exec(actions);
            total_actions += len(actions);
            actions.clear()

        print(f"[reactions] processed rows: {total_rows}, ES actions: {total_actions}")

    # ---------- helpers ----------

    def _load_edges(self, met_rx_path: str) -> Dict[str, Dict[str, List[str]]]:
        rx = defaultdict(lambda: {"substrates": [], "products": []})
        total = 0
        first_cols_printed = False
        for chunk in chunks_from_table(met_rx_path, chunksize=100_000):
            if not first_cols_printed:
                print(f"[reactions] Metabolite edges columns: {list(chunk.columns)}")
                first_cols_printed = True

            for rec in chunk.to_dict(orient="records"):
                total += 1
                km = _keys_map(rec)
                r = _get(rec, km, "Reaction", "reaction", "rxn")
                subs = _get(rec, km, "Substrates", "substrates", "subs", "left")
                prods = _get(rec, km, "Products", "products", "prods", "right")
                if not r:
                    continue
                r = str(r).strip()
                subs_list = str(subs).split() if subs not in (None, "", "nan", "NaN") else []
                prods_list = str(prods).split() if prods not in (None, "", "nan", "NaN") else []
                rx[r]["substrates"] = sorted(set(rx[r]["substrates"] + subs_list))
                rx[r]["products"] = sorted(set(rx[r]["products"] + prods_list))
        print(f"[reactions] loaded edges rows: {total}, reactions covered: {len(rx)}")
        return rx

    def _load_gpr(self, rx_gpr_path: str) -> Dict[str, str]:
        d: Dict[str, str] = {}
        total = 0
        first_cols_printed = False
        for chunk in chunks_from_table(rx_gpr_path, chunksize=100_000):
            if not first_cols_printed:
                print(f"[reactions] GPR columns: {list(chunk.columns)}")
                first_cols_printed = True

            for rec in chunk.to_dict(orient="records"):
                total += 1
                km = _keys_map(rec)
                r = _get(rec, km, "Reaction", "reaction", "rxn")
                gpr = _get(rec, km, "GPR", "gpr", "rule")
                if not r:
                    continue
                d[str(r).strip()] = (str(gpr).strip() if gpr not in (None, "", "nan", "NaN") else None)
        print(f"[reactions] loaded gpr rows: {total}, reactions with gpr: {len(d)}")
        return d
