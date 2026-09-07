from __future__ import annotations

from typing import Dict

import pandas as pd


def read_mapping_tsv(path: str) -> Dict[str, str]:
    """TSV with columns: assembly, prefix."""
    df = pd.read_csv(path, sep="\t")
    return dict(zip(df["assembly"], df["prefix"]))
