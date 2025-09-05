import csv
from collections import defaultdict

from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS
from dataportal.ingest.feature.flows.base import Flow
from dataportal.models import FeatureDocument


class Reactions(Flow):
    """
    Needs three CSVs:
      - Gene→Reaction: headers Gene,Reaction
      - Metabolite edges: headers Substrates,Reaction,Products  (substrates/products space-separated)
      - GPR per reaction: headers Reaction,GPR
    """

    def __init__(self, index_name: str = "feature_index"):
        super().__init__(index_name=index_name)

    def run(self, gene_rx_csv, met_rx_csv, gpr_csv):
        rx_edges = self._load_edges(met_rx_csv)
        rx_gpr = self._load_gpr(gpr_csv)

        actions = []
        with open(gene_rx_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row["Gene"].strip()
                rx = row["Reaction"].strip()
                if not fid or not rx:
                    continue

                # simple reactions list (dedup in script)
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": """
if (ctx._source.reactions == null) { ctx._source.reactions = []; }
if (!ctx._source.reactions.contains(params.r)) { ctx._source.reactions.add(params.r); }
ctx._source.has_reactions = true;
""",
                        "params": {"r": rx},
                    },
                    "upsert": {"feature_id": fid, "feature_type": "gene", "reactions": [rx], "has_reactions": True},
                })

                # reaction_details (dedup by reaction)
                entry = {
                    "reaction": rx,
                    "gpr": rx_gpr.get(rx),
                    "substrates": rx_edges.get(rx, {}).get("substrates", []),
                    "products": rx_edges.get(rx, {}).get("products", []),
                    "metabolites": sorted(
                        set(rx_edges.get(rx, {}).get("substrates", []) + rx_edges.get(rx, {}).get("products", []))),
                }
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": fid,
                    "script": {
                        "source": SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS,
                        "params": {"field": "reaction_details", "entry": entry, "keys": ["reaction"]},
                    },
                    "upsert": {"feature_id": fid, "feature_type": "gene", "reaction_details": [entry],
                               "has_reactions": True},
                })

                if len(actions) >= 500:
                    bulk_exec(actions);
                    actions.clear()

        if actions:
            bulk_exec(actions)

    def _load_edges(self, met_rx_csv):
        rx = defaultdict(lambda: {"substrates": [], "products": []})
        with open(met_rx_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                r = row["Reaction"].strip()
                subs = row["Substrates"].split()
                prods = row["Products"].split()
                rx[r]["substrates"] = sorted(set(rx[r]["substrates"] + subs))
                rx[r]["products"] = sorted(set(rx[r]["products"] + prods))
        return rx

    def _load_gpr(self, gpr_csv):
        d = {}
        with open(gpr_csv, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                d[row["Reaction"].strip()] = row["GPR"].strip()
        return d
