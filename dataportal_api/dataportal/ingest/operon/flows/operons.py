from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from dataportal.ingest.constants import SPECIES_BY_ACRONYM
from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.gff.parser import GFFParser
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

    def __init__(self, index_name: str = "operon_index", gff_parser: Optional[GFFParser] = None):
        super().__init__(index_name=index_name)
        self._docs: Dict[str, Dict[str, Any]] = {}
        # scratch collectors for resolving taxonomy per operon
        self._scratch: Dict[str, Dict[str, Counter]] = {}  # oid -> {"acronyms": Counter(), "isolates": Counter()}
        self.gff_parser = gff_parser

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

                # gene A/B details (optional columns)
                ga_name = _get(rec, km, "gene_a_name", "gene_a_gene_name", "gene_a_symbol", "name_a", "gene1_name")
                gb_name = _get(rec, km, "gene_b_name", "gene_b_gene_name", "gene_b_symbol", "name_b", "gene2_name")

                ga_uniprot = _get(rec, km, "gene_a_uniprot_id", "uniprot_a", "uniprot_id_a", "gene1_uniprot")
                gb_uniprot = _get(rec, km, "gene_b_uniprot_id", "uniprot_b", "uniprot_id_b", "gene2_uniprot")

                ga_product = _get(rec, km, "gene_a_product", "product_a", "gene1_product", "product_left")
                gb_product = _get(rec, km, "gene_b_product", "product_b", "gene2_product", "product_right")

                ga_isolate = _get(rec, km, "gene_a_isolate_name", "isolate_a", "isolate_left")
                gb_isolate = _get(rec, km, "gene_b_isolate_name", "isolate_b", "isolate_right")

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
                        # gene A
                        "gene_a_locus_tag": None,
                        "gene_a_uniprot_id": None,
                        "gene_a_name": None,
                        "gene_a_product": None,
                        "gene_a_isolate_name": None,
                        # gene B
                        "gene_b_locus_tag": None,
                        "gene_b_uniprot_id": None,
                        "gene_b_name": None,
                        "gene_b_product": None,
                        "gene_b_isolate_name": None,
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

                # set per-gene details without overwriting once present
                if ga and not doc["gene_a_locus_tag"]:
                    doc["gene_a_locus_tag"] = ga
                if gb and not doc["gene_b_locus_tag"]:
                    doc["gene_b_locus_tag"] = gb

                if ga_name and not doc["gene_a_name"]:
                    doc["gene_a_name"] = str(ga_name).strip()
                if gb_name and not doc["gene_b_name"]:
                    doc["gene_b_name"] = str(gb_name).strip()

                if ga_uniprot and not doc["gene_a_uniprot_id"]:
                    doc["gene_a_uniprot_id"] = str(ga_uniprot).strip()
                if gb_uniprot and not doc["gene_b_uniprot_id"]:
                    doc["gene_b_uniprot_id"] = str(gb_uniprot).strip()

                if ga_product and not doc["gene_a_product"]:
                    doc["gene_a_product"] = str(ga_product).strip()
                if gb_product and not doc["gene_b_product"]:
                    doc["gene_b_product"] = str(gb_product).strip()

                # infer isolates per gene from explicit columns or locus tag
                if not doc["gene_a_isolate_name"]:
                    inferred_ga_iso = ga_isolate or parse_isolate_name(ga) if ga else None
                    if inferred_ga_iso:
                        doc["gene_a_isolate_name"] = str(inferred_ga_iso).strip()
                if not doc["gene_b_isolate_name"]:
                    inferred_gb_iso = gb_isolate or parse_isolate_name(gb) if gb else None
                    if inferred_gb_iso:
                        doc["gene_b_isolate_name"] = str(inferred_gb_iso).strip()

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

                # Enrich per-gene details from preloaded GFF if available
                if self.gff_parser:
                    # Gene A
                    if ga and (not doc["gene_a_name"] or not doc["gene_a_product"] or not doc["gene_a_uniprot_id"]):
                        acr_a = parse_species_acronym(ga)
                        iso_a = parse_isolate_name(ga)
                        species_name_a = species_name_from_acronym(acr_a) if acr_a else None
                        if species_name_a and iso_a:
                            unique_species_a = f"{species_name_a}_{iso_a}"
                            gi_a = self.gff_parser.get_gene_info(unique_species_a, ga)
                            if gi_a:
                                if not doc["gene_a_name"] and gi_a.name:
                                    doc["gene_a_name"] = gi_a.name
                                if not doc["gene_a_product"] and gi_a.product:
                                    doc["gene_a_product"] = gi_a.product
                                if not doc["gene_a_uniprot_id"] and gi_a.uniprot_id:
                                    doc["gene_a_uniprot_id"] = gi_a.uniprot_id
                                if not doc["gene_a_isolate_name"] and iso_a:
                                    doc["gene_a_isolate_name"] = iso_a

                    # Gene B
                    if gb and (not doc["gene_b_name"] or not doc["gene_b_product"] or not doc["gene_b_uniprot_id"]):
                        acr_b = parse_species_acronym(gb)
                        iso_b = parse_isolate_name(gb)
                        species_name_b = species_name_from_acronym(acr_b) if acr_b else None
                        if species_name_b and iso_b:
                            unique_species_b = f"{species_name_b}_{iso_b}"
                            gi_b = self.gff_parser.get_gene_info(unique_species_b, gb)
                            if gi_b:
                                if not doc["gene_b_name"] and gi_b.name:
                                    doc["gene_b_name"] = gi_b.name
                                if not doc["gene_b_product"] and gi_b.product:
                                    doc["gene_b_product"] = gi_b.product
                                if not doc["gene_b_uniprot_id"] and gi_b.uniprot_id:
                                    doc["gene_b_uniprot_id"] = gi_b.uniprot_id
                                if not doc["gene_b_isolate_name"] and iso_b:
                                    doc["gene_b_isolate_name"] = iso_b

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



