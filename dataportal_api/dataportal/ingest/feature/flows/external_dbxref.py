"""
Flow for importing external database cross-references into the feature index.

This flow reads TSV files containing mappings from locus_tag to external database IDs
and appends them to the dbxref nested array in the feature documents.
"""

import pandas as pd

from dataportal.ingest.es_repo import bulk_exec, SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS
from dataportal.ingest.feature.flows.base import Flow


class ExternalDBXRef(Flow):
    """
    Import external database cross-references (dbxref) into feature documents.

    Expected TSV format (DIAMOND output or similar):
        Column 1: locus_tag (e.g., BU_ATCC8492_00001)
        Column 2: external_db_id (e.g., 820.ERS852554_01920 for STRING DB)
        Columns 3+: metadata (ignored for dbxref, but preserved in file)

    The flow supports multiple database types by specifying the database name.
    """

    def __init__(self, index_name: str = "feature_index", db_name: str = "STRING"):
        """
        Initialize the ExternalDBXRef flow.

        Args:
            index_name: Target Elasticsearch index name
            db_name: Name of the external database (e.g., "STRING", "UniProt", etc.)
        """
        super().__init__(index_name=index_name)
        self.db_name = db_name

    def run(self, tsv_path: str, chunksize: int = 10000):
        """
        Process TSV file and update feature documents with dbxref entries.

        Args:
            tsv_path: Path to TSV file with mappings
            chunksize: Number of rows to process per batch
        """
        actions = []
        processed_count = 0

        print(f"[ExternalDBXRef] Processing {tsv_path} for database '{self.db_name}'")

        # Read TSV file - assume first column is locus_tag, second is external_db_id
        # Use header=None to handle files without headers
        try:
            df_iterator = pd.read_csv(
                tsv_path,
                sep="\t",
                header=None,
                chunksize=chunksize,
                dtype={0: str, 1: str},  # Ensure locus_tag and external_db_id are strings
            )
        except Exception as e:
            print(f"[ExternalDBXRef] Error reading file {tsv_path}: {e}")
            return

        for chunk in df_iterator:
            for _, row in chunk.iterrows():
                # Column 0: locus_tag (qseqid in DIAMOND output)
                locus_tag = str(row.iloc[0]).strip() if len(row) > 0 else None

                # Column 1: external_db_id (sseqid in DIAMOND output)
                external_db_id = str(row.iloc[1]).strip() if len(row) > 1 else None

                # Skip rows with missing data
                if (
                    not locus_tag
                    or not external_db_id
                    or locus_tag == "nan"
                    or external_db_id == "nan"
                ):
                    continue

                # Create dbxref entry
                dbxref_entry = {"db": self.db_name, "ref": external_db_id}

                # Prepare update action
                action = {
                    "_op_type": "update",
                    "_index": self.index,
                    "_id": locus_tag,
                    "script": {
                        "source": SCRIPT_APPEND_NESTED_DEDUP_BY_KEYS,
                        "params": {
                            "field": "dbxref",
                            "entry": dbxref_entry,
                            "keys": ["db", "ref"],  # Deduplicate by both db and ref
                        },
                    },
                    "upsert": {
                        "feature_id": locus_tag,
                        "feature_type": "gene",
                        "dbxref": [dbxref_entry],
                    },
                }

                actions.append(action)
                processed_count += 1

                # Execute bulk operations in batches
                if len(actions) >= 500:
                    bulk_exec(actions)
                    actions.clear()

        # Process remaining actions
        if actions:
            bulk_exec(actions)
            actions.clear()

        print(
            f"[ExternalDBXRef] Processed {processed_count} mappings for database '{self.db_name}'"
        )
