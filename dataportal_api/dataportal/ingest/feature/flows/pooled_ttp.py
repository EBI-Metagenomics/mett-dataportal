import pandas as pd
import os

from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS, SCRIPT_APPEND_AND_SET_FLAG
from dataportal.ingest.feature.flows.base import Flow
from dataportal.ingest.utils import pick
from dataportal.models import FeatureDocument


class PooledTTP(Flow):
    """
    Ingest pooled TTP (Thermal Proteome Profiling) data into the feature index.
    
    CSV columns expected:
      locus_tag, compound, score, pval, padj, hit_calling, notes, assay
    """

    def __init__(self, index_name: str = "feature_index", pool_metadata_path: str = None):
        super().__init__(index_name=index_name)
        self.pool_metadata = self._load_pool_metadata(pool_metadata_path)

    def _load_pool_metadata(self, pool_metadata_path: str = None):
        """Load pool metadata mapping compound -> (poolA, poolB)"""
        if not pool_metadata_path or not os.path.exists(pool_metadata_path):
            print("Warning: No pool metadata file provided or file not found")
            return {}
        
        try:
            df = pd.read_csv(pool_metadata_path)
            pool_mapping = {}
            for _, row in df.iterrows():
                compound = str(row.get("compound", "")).strip()
                poolA = str(row.get("poolA", "")).strip()
                poolB = str(row.get("poolB", "")).strip()
                if compound and compound != "nan":
                    pool_mapping[compound] = {
                        "poolA": poolA if poolA != "nan" else None,
                        "poolB": poolB if poolB != "nan" else None
                    }
            print(f"Loaded pool metadata for {len(pool_mapping)} compounds")
            return pool_mapping
        except Exception as e:
            print(f"Error loading pool metadata: {e}")
            return {}

    def run(self, csv_path):
        """
        Ingest pooled TTP data from CSV file.
        
        Args:
            csv_path: Path to the pooled TTP CSV file
        """
        actions = []
        processed_count = 0
        
        print(f"Starting ingestion of pooled TTP data from: {csv_path}")
        
        for chunk in pd.read_csv(csv_path, chunksize=10000):
            for rec in chunk.to_dict(orient="records"):
                # Extract locus_tag (primary identifier)
                locus_tag = str(rec.get("locus_tag", "")).strip()
                if not locus_tag:
                    continue
                
                # Extract compound information
                compound = str(rec.get("compound", "")).strip()
                if not compound:
                    continue
                
                # Extract TTP score (thermal stability score)
                ttp_score = rec.get("score")
                try:
                    ttp_score = float(ttp_score) if ttp_score not in (None, "", "NA") else None
                except (ValueError, TypeError):
                    ttp_score = None
                
                # Extract FDR (false discovery rate) from padj column
                fdr = rec.get("padj")
                try:
                    fdr = float(fdr) if fdr not in (None, "", "NA") else None
                except (ValueError, TypeError):
                    fdr = None
                
                # Extract hit calling information
                hit_calling_raw = rec.get("hit_calling")
                hit_calling = False
                if hit_calling_raw is not None and str(hit_calling_raw).strip() not in ("", "NA"):
                    hit_str = str(hit_calling_raw).strip().lower()
                    hit_calling = hit_str in ("hit", "true", "1", "yes", "destabilised_strong", "destabilised_weak")
                
                # Extract notes and assay information
                notes = str(rec.get("notes", "")).strip()
                if notes in ("", "NA"):
                    notes = None
                
                assay = str(rec.get("assay", "")).strip()
                if assay in ("", "NA"):
                    assay = None
                
                # Get pool information from metadata
                pool_info = self.pool_metadata.get(compound, {})
                poolA = pool_info.get("poolA")
                poolB = pool_info.get("poolB")
                
                # Create the protein compound entry
                entry = {
                    "compound": compound,
                    "ttp_score": ttp_score,
                    "fdr": fdr,
                    "hit_calling": hit_calling,
                    "experimental_condition": None,  # Keep blank as requested
                    "notes": notes,
                    "assay": assay,
                    "poolA": poolA,
                    "poolB": poolB,
                }
                
                # Prepare the bulk action for Elasticsearch
                action = {
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": locus_tag,
                    "script": {
                        "source": SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS + "\n" + SCRIPT_APPEND_AND_SET_FLAG,
                        "params": {
                            "field": "protein_compound", 
                            "entry": entry, 
                            "keys": ["compound"],
                            "flag_field": "has_proteomics"
                        },
                    },
                    "upsert": {
                        "feature_id": locus_tag, 
                        "feature_type": "gene", 
                        "protein_compound": [entry],
                        "has_proteomics": True
                    },
                }
                
                actions.append(action)
                processed_count += 1
                
                # Execute bulk operations in batches
                if len(actions) >= 500:
                    bulk_exec(actions)
                    print(f"Processed {processed_count} records...")
                    actions.clear()
        
        # Execute any remaining actions
        if actions:
            bulk_exec(actions)
            print(f"Processed {processed_count} records...")
        
        print(f"Completed ingestion of {processed_count} pooled TTP records")
        return processed_count
