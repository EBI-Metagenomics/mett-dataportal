"""Default data-generators paths. Override with env vars."""

from __future__ import annotations

import os
from pathlib import Path

DATA_GENERATORS_ROOT = Path(__file__).resolve().parents[1]


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value).expanduser().resolve() if value else default


FAA_OUT = _env_path("FAA_OUT", DATA_GENERATORS_ROOT / "data" / "generated" / "faa")
STRING_INPUT_DIR = _env_path(
    "STRING_INPUT_DIR", DATA_GENERATORS_ROOT / "data" / "inputs" / "stringdb"
)
STRING_OUT = _env_path(
    "STRING_OUT", DATA_GENERATORS_ROOT / "data" / "generated" / "string-mapping"
)
BROWSER_INDEX_OUT = _env_path(
    "BROWSER_INDEX_OUT",
    DATA_GENERATORS_ROOT / "data" / "generated" / "browser-indexes",
)
QC_OUT = _env_path("QC_OUT", DATA_GENERATORS_ROOT / "data" / "generated" / "qc")
GFF_GENE_OUT = _env_path(
    "GFF_GENE_OUT", DATA_GENERATORS_ROOT / "data" / "generated" / "gff-with-genes"
)
