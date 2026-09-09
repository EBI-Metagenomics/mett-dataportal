import pandas as pd
from dataportal.ingest.flow import Flow
from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_AND_SET_FLAG
from dataportal.ingest.utils import (
    pick,
    canonical_ig_id_from_neighbors,
    parse_ig_neighbors,
    extract_isolate_from_locus_tag,
    get_species_metadata_from_isolate,
    ig_neighbor_fields,
)
from dataportal.utils.constants import INDEX_FEATURES, INDEX_FEATURE_EXPERIMENTS


class Fitness(Flow):
    """
    CSV flexible columns:
      - prefer: locus_tag, experimental_condition, media, contrast, lfc, fdr, number_of_barcodes
      - fallback: 'Name' for locus_tag, 'LFC'/'FDR' for values
    """

    def __init__(
        self,
        index_name: str = INDEX_FEATURE_EXPERIMENTS,
        feature_flag_index: str | None = INDEX_FEATURES,
    ):
        super().__init__(index_name=index_name, feature_flag_index=feature_flag_index)
        self._species_cache = {}

    def run(self, csv_path):
        actions = []
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for rec in chunk.to_dict(orient="records"):
                fid = str(pick(rec, "locus_tag", "Name", default="") or "").strip()
                if not fid:
                    continue

                # Determine feature type and normalize ID for intergenic regions
                left = right = None
                if fid.startswith("IG-between-"):
                    feature_type = "IG"
                    left, right = parse_ig_neighbors(fid)
                    if left and right:
                        fid = canonical_ig_id_from_neighbors(left, right) or fid
                else:
                    feature_type = "gene"

                # Extract number of barcodes if available
                num_barcodes = rec.get("number_of_barcodes")
                if num_barcodes is not None:
                    try:
                        num_barcodes = int(num_barcodes)
                    except (ValueError, TypeError):
                        num_barcodes = None

                entry = {
                    "experimental_condition": pick(rec, "experimental_condition", "contrast"),
                    "media": rec.get("media"),
                    "contrast": rec.get("contrast"),
                    "lfc": (
                        float(rec.get("lfc", rec.get("LFC")))
                        if pick(rec, "lfc", "LFC") is not None
                        else None
                    ),
                    "fdr": (
                        float(rec.get("fdr", rec.get("FDR")))
                        if pick(rec, "fdr", "FDR") is not None
                        else None
                    ),
                    "number_of_barcodes": num_barcodes,
                }

                # Build upsert data
                upsert_data = {
                    "feature_id": fid,
                    "feature_type": feature_type,
                    "locus_tag": fid,
                    "fitness": [entry],
                    "has_fitness": True,
                }

                script_params = {
                    "field": "fitness",
                    "entry": entry,
                    "flag_field": "has_fitness",
                }

                if feature_type == "IG":
                    isolate_name = extract_isolate_from_locus_tag(fid)
                    if isolate_name:
                        species_metadata = get_species_metadata_from_isolate(
                            isolate_name, self._species_cache
                        )
                        upsert_data.update(species_metadata)
                    neighbors = ig_neighbor_fields(fid, left, right)
                    upsert_data.update(neighbors)
                    script_params.update(neighbors)

                actions.append(
                    {
                        "_op_type": "update",
                        "_index": self.index,
                        "_id": fid,
                        "script": {
                            "source": SCRIPT_APPEND_AND_SET_FLAG,
                            "params": script_params,
                        },
                        "upsert": upsert_data,
                    }
                )
                self.add_feature_flag(actions, fid, "has_fitness")
                if len(actions) >= 500:
                    bulk_exec(actions)
                    actions.clear()
        if actions:
            bulk_exec(actions)
