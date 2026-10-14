"""Turn one isolate FAA into a JSONL chunk for the merge step."""

from __future__ import annotations

import json
from pathlib import Path

from fasta import parse_fasta_file


def stage_isolate(
    faa: Path,
    *,
    isolate: str,
    species: str,
    is_type: bool,
    collection: str,
    out: Path,
) -> int:
    records = parse_fasta_file(faa)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    {
                        "sha256": record.sha256,
                        "locus_tag": record.locus_tag,
                        "species": species,
                        "isolate": isolate,
                        "is_type": is_type,
                        "product": record.product,
                        "sequence": record.sequence,
                        "collection": collection,
                    },
                    separators=(",", ":"),
                )
            )
            handle.write("\n")
    return len(records)
