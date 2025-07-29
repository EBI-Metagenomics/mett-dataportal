"""
Download service for PyHMMER results export functionality.
"""

import csv
import io
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DownloadService:
    """Service for generating downloadable content from PyHMMER results."""

    @staticmethod
    def generate_tsv_content(results: List[Dict[str, Any]]) -> str:
        """Generate TSV content from search results."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter="\t")

        # Write header
        writer.writerow(
            [
                "Target",
                "Description",
                "E-value",
                "Score",
                "Bias",
                "Query_Start",
                "Query_End",
                "Target_Start",
                "Target_End",
                "Query_Length",
                "Target_Length",
                "Identity_Pct",
                "Identity_Count",
                "Similarity_Pct",
                "Similarity_Count",
            ]
        )

        # Write data rows
        for hit in results:
            target = hit.get("target", "")
            description = hit.get("description", "")
            evalue = hit.get("evalue", "")
            score = hit.get("score", "")

            domains = hit.get("domains", [])
            if domains:
                domain = domains[0]
                bias = domain.get("bias", "")
                # env_from = domain.get("env_from", "")
                # env_to = domain.get("env_to", "")

                # Get alignment information
                alignment = domain.get("alignment", {})
                if alignment:
                    query_start = alignment.get("hmm_from", "")
                    query_end = alignment.get("hmm_to", "")
                    target_start = alignment.get("target_from", "")
                    target_end = alignment.get("target_to", "")
                    query_length = alignment.get("hmm_length", "")
                    target_length = alignment.get("target_length", "")
                else:
                    query_start = query_end = target_start = target_end = (
                        query_length
                    ) = target_length = ""

                # Get identity/similarity from alignment_display
                alignment_display = domain.get("alignment_display", {})
                if alignment_display:
                    identity = alignment_display.get("identity", [0, 0])
                    similarity = alignment_display.get("similarity", [0, 0])
                    identity_pct = (
                        f"{identity[0] * 100:.1f}" if len(identity) > 0 else "0.0"
                    )
                    identity_count = str(identity[1]) if len(identity) > 1 else "0"
                    similarity_pct = (
                        f"{similarity[0] * 100:.1f}" if len(similarity) > 0 else "0.0"
                    )
                    similarity_count = (
                        str(similarity[1]) if len(similarity) > 1 else "0"
                    )
                else:
                    identity_pct = identity_count = similarity_pct = (
                        similarity_count
                    ) = "0"
            else:
                bias = query_start = query_end = target_start = target_end = (
                    query_length
                ) = target_length = "0"
                identity_pct = identity_count = similarity_pct = similarity_count = "0"

            writer.writerow(
                [
                    target,
                    description,
                    evalue,
                    score,
                    bias,
                    query_start,
                    query_end,
                    target_start,
                    target_end,
                    query_length,
                    target_length,
                    identity_pct,
                    identity_count,
                    similarity_pct,
                    similarity_count,
                ]
            )

        return output.getvalue()
