from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from dataportal.ingest.constants import SPECIES_BY_ACRONYM
from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import canonical_pair_id
from dataportal.ingest.utils import chunks_from_table


# ---------- helpers (module-level) ----------
def _keys_map(cols) -> Dict[str, str]:
    return {str(c).lower().strip(): c for c in cols}


def _get(rec: Dict[str, Any], km: Dict[str, str], *names, default=None):
    for n in names:
        k = km.get(str(n).lower().strip())
        if k is not None:
            return rec.get(k, default)
    return default


def _to_bool(v: Any) -> bool | None:
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("true", "t", "1", "y", "yes"):
        return True
    if s in ("false", "f", "0", "n", "no"):
        return False
    return None


def parse_species_acronym(locus: str) -> str | None:
    if not locus:
        return None
    s = str(locus).strip()
    i = s.find("_")
    return s[:i] if i > 0 else None


def parse_isolate_name(locus: str) -> str | None:
    if not locus:
        return None
    s = str(locus).strip()
    j = s.rfind("_")
    return s[:j] if j > 0 else None


def species_name_from_acronym(acr: str) -> str | None:
    if not acr:
        return None
    return SPECIES_BY_ACRONYM.get(str(acr).strip())


# ---------- flow ----------
class Operons(Flow):
    """
    Build exactly one document per operon_id.
    Rows missing operon_id are ignored.
    No edge storage; we just aggregate per-operon rollups and taxonomy.
    """

    def __init__(self, index_name: str = "operon_index"):
        super().__init__(index_name=index_name)
        self._docs: Dict[str, Dict[str, Any]] = {}
        # scratch collectors for resolving taxonomy per operon
        self._scratch: Dict[str, Dict[str, Counter]] = {}  # oid -> {"acronyms": Counter(), "isolates": Counter()}

    def run(self, path: str, chunksize: int = 5_000) -> None:
        rows = 0
        ignored = 0

        for chunk in chunks_from_table(path, chunksize=chunksize):
            km = _keys_map(chunk.columns)
            for rec in chunk.to_dict(orient="records"):
                rows += 1

                # gene locus tags
                ga = _get(rec, km, "gene_a_locus_tag", "gene1", "gene_a", "left", "locus_a")
                gb = _get(rec, km, "gene_b_locus_tag", "gene2", "gene_b", "right", "locus_b")
                ga = str(ga).strip() if ga else None
                gb = str(gb).strip() if gb else None

                operon_id = _get(rec, km, "operon_id", "operon")
                if operon_id in (None, "", "nan", "NaN"):
                    oid = canonical_pair_id(ga, gb)
                else:
                    oid = str(operon_id).strip()

                # explicit fields (if present)
                explicit_isolate = _get(rec, km, "isolate_name", "isolate")
                explicit_acr = _get(rec, km, "species_acronym", "species_acr", "acr")
                explicit_sci = _get(rec, km, "species_scientific_name", "species", "species_name")

                has_tss = _to_bool(_get(rec, km, "has_tss"))
                has_term = _to_bool(_get(rec, km, "has_terminator"))

                doc = self._docs.get(oid)
                if not doc:
                    doc = {
                        "operon_id": oid,
                        "isolate_name": None,
                        "species_acronym": None,
                        "species_scientific_name": None,
                        "genes": [],
                        "has_tss": False,
                        "has_terminator": False,
                    }
                    self._docs[oid] = doc
                    self._scratch[oid] = {"acronyms": Counter(), "isolates": Counter()}

                # accumulate unique genes
                for g in (ga, gb):
                    if g and g not in doc["genes"]:
                        doc["genes"].append(g)

                # infer from locus tags (per-row)
                for g in (ga, gb):
                    if not g:
                        continue
                    acr = parse_species_acronym(g)
                    iso = parse_isolate_name(g)
                    if acr:
                        self._scratch[oid]["acronyms"][acr] += 1
                    if iso:
                        self._scratch[oid]["isolates"][iso] += 1

                # set rollups
                if has_tss is True:
                    doc["has_tss"] = True
                if has_term is True:
                    doc["has_terminator"] = True

                # opportunistically fill explicit values if provided (don’t overwrite once set)
                if explicit_isolate and not doc["isolate_name"]:
                    doc["isolate_name"] = str(explicit_isolate).strip()
                if explicit_acr and not doc["species_acronym"]:
                    doc["species_acronym"] = str(explicit_acr).strip()
                if explicit_sci and not doc["species_scientific_name"]:
                    doc["species_scientific_name"] = str(explicit_sci).strip()

        # finalize per-operon taxonomy after reading all rows
        for oid, doc in self._docs.items():
            scr = self._scratch.get(oid, {"acronyms": Counter(), "isolates": Counter()})

            # choose most frequent if still unset
            if not doc["species_acronym"] and scr["acronyms"]:
                doc["species_acronym"] = scr["acronyms"].most_common(1)[0][0]

            if not doc["isolate_name"] and scr["isolates"]:
                doc["isolate_name"] = scr["isolates"].most_common(1)[0][0]

            # species scientific name via map if still unset
            if not doc["species_scientific_name"] and doc["species_acronym"]:
                doc["species_scientific_name"] = species_name_from_acronym(doc["species_acronym"])

        print(f"[operons-only] processed rows from {path}: {rows} (ignored w/o operon_id: {ignored})")

    def flush(self) -> None:
        if not self._docs:
            return
        actions: List[Dict[str, Any]] = []
        for oid, src in self._docs.items():
            # finalize gene_count
            src["gene_count"] = len(src.get("genes", []))

            actions.append({
                "_op_type": "index",  # overwrite if already present (fresh imports ok)
                "_index": self.index,
                "_id": oid,  # use bare operon_id as the ES _id
                "_source": src,
            })

            if len(actions) >= 1000:
                bulk_exec(actions)
                actions.clear()

        if actions:
            bulk_exec(actions)

        print(f"[operons-only] indexed docs: {len(self._docs)}")
        # Optional
        # self._docs.clear()
        # self._scratch.clear()



