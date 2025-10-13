"""
Mutant growth data ingestion flow for FeatureDocument.

This module handles importing mutant growth data (doubling times, plate positions, etc.)
into the mutant_growth nested field of FeatureDocument.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pandas as pd

from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.es_repo import bulk_exec
from dataportal.ingest.utils import extract_isolate_from_locus_tag, get_species_metadata_from_isolate


# Script to append with deduplication and set flag
SCRIPT_DEDUP_AND_FLAG = """
if (ctx._source[params.field] == null) { ctx._source[params.field] = []; }
boolean exists = false;
for (item in ctx._source[params.field]) {
  boolean same = true;
  for (k in params.keys) {
    if (item[k] == null && params.entry[k] == null) { continue; }
    if (item[k] != params.entry[k]) { same = false; break; }
  }
  if (same) { exists = true; break; }
}
if (!exists) { ctx._source[params.field].add(params.entry); }
ctx._source[params.flag_field] = true;
"""


@dataclass
class MutantGrowthFlow(Flow):
    """
    Flow for importing mutant growth data into FeatureDocument.
    
    CSV expected columns:
    - locus_tag: Gene identifier (e.g., PV_ATCC8482_04295)
    - doubling_time: Doubling time in hours (core numeric readout)
    - isdoublepicked: Boolean flag (TRUE/FALSE) - mutant picked twice if only single available
    - brep: Biological replicate identifier (brep_1, brep_2, etc.)
    - Plate384: Plate number in 384-well array (1-16)
    - Well384: Well position (A17, C16, etc.)
    - Percent_from_start: Transposon insertion position (0-1)
    """

    def __init__(
        self,
        index_name: str = "feature_index",
        media: Optional[str] = None,
        experimental_condition: Optional[str] = None,
    ):
        """
        Initialize the mutant growth flow.
        
        Args:
            index_name: Elasticsearch index name (default: feature_index)
            media: Media type for the experiment (optional)
            experimental_condition: Experimental condition context (optional)
        """
        super().__init__(index_name)
        self.media = media
        self.experimental_condition = experimental_condition
        self._species_cache = {}  # Cache for species lookups

    def run(self, csv_path: str) -> None:
        """
        Process mutant growth CSV and index to Elasticsearch.
        
        Args:
            csv_path: Path to CSV file with mutant growth data
        """
        actions = []
        
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for rec in chunk.to_dict(orient="records"):
                locus_tag = str(rec.get("locus_tag", "")).strip()
                if not locus_tag:
                    continue

                # Determine feature type
                feature_type = "IG" if locus_tag.startswith("IG:") or locus_tag.startswith("IG-") else "gene"

                # Extract and validate doubling_time
                doubling_time = rec.get("doubling_time")
                if doubling_time is None or pd.isna(doubling_time):
                    continue
                    
                try:
                    doubling_time = float(doubling_time)
                except (ValueError, TypeError):
                    continue

                # Extract boolean flag
                isdoublepicked = rec.get("isdoublepicked")
                if isinstance(isdoublepicked, str):
                    isdoublepicked = isdoublepicked.upper() == "TRUE"
                elif pd.isna(isdoublepicked):
                    isdoublepicked = False

                # Extract biological replicate
                brep = rec.get("brep", "").strip()
                if not brep:
                    continue

                # Extract plate and well information
                plate384 = rec.get("Plate384")
                well384 = str(rec.get("Well384", "")).strip()
                
                # Handle plate384 conversion
                plate_number = None
                if plate384 is not None and not pd.isna(plate384):
                    try:
                        plate_number = int(plate384)
                    except (ValueError, TypeError):
                        pass

                # Extract percent_from_start
                percent_from_start = rec.get("Percent_from_start")
                if percent_from_start is not None and not pd.isna(percent_from_start):
                    try:
                        percent_from_start = float(percent_from_start)
                    except (ValueError, TypeError):
                        percent_from_start = None
                else:
                    percent_from_start = None

                # Create mutant growth entry
                entry = {
                    "doubling_time": doubling_time,
                    "isdoublepicked": isdoublepicked,
                    "brep": brep,
                }
                
                # Add media and experimental_condition if provided
                if self.media is not None:
                    entry["media"] = self.media
                if self.experimental_condition is not None:
                    entry["experimental_condition"] = self.experimental_condition
                
                # Add optional fields if available
                if plate_number is not None:
                    entry["plate384"] = plate_number
                if well384:
                    entry["well384"] = well384
                if percent_from_start is not None:
                    entry["percent_from_start"] = percent_from_start

                # Build upsert data
                upsert_data = {
                    "feature_id": locus_tag,
                    "feature_type": feature_type,
                    "mutant_growth": [entry],
                    "has_mutant_growth": True,
                }
                
                # Add genome/species metadata for IG features
                if feature_type == "IG":
                    isolate_name = extract_isolate_from_locus_tag(locus_tag)
                    if isolate_name:
                        species_metadata = get_species_metadata_from_isolate(isolate_name, self._species_cache)
                        upsert_data.update(species_metadata)

                # Define dedup keys: media + experimental_condition + brep uniquely identify an entry
                dedup_keys = ["brep"]
                if self.media is not None:
                    dedup_keys.append("media")
                if self.experimental_condition is not None:
                    dedup_keys.append("experimental_condition")

                # Create bulk action with deduplication and flag setting
                actions.append({
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": locus_tag,
                    "script": {
                        "source": SCRIPT_DEDUP_AND_FLAG,
                        "params": {
                            "field": "mutant_growth",
                            "entry": entry,
                            "keys": dedup_keys,
                            "flag_field": "has_mutant_growth",
                        },
                    },
                    "scripted_upsert": True,
                    "upsert": upsert_data,
                })

                # Bulk index when batch is ready
                if len(actions) >= 500:
                    bulk_exec(actions)
                    actions.clear()

        # Process remaining actions
        if actions:
            bulk_exec(actions)
            bulk_exec(actions)