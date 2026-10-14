"""FASTA helpers for the protein database. Standard library only."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FastaRecord:
    locus_tag: str
    product: str
    sequence: str

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.sequence.encode("ascii")).hexdigest()


def normalize_sequence(raw: str) -> str:
    return re.sub(r"\s+", "", raw).upper()


def parse_fasta(text: str) -> list[FastaRecord]:
    records: list[FastaRecord] = []
    locus = ""
    product = ""
    chunks: list[str] = []

    def flush() -> None:
        if not locus:
            return
        sequence = normalize_sequence("".join(chunks))
        if sequence:
            records.append(
                FastaRecord(locus_tag=locus, product=product, sequence=sequence)
            )

    for line in text.splitlines():
        if line.startswith(">"):
            flush()
            header = line[1:].strip()
            locus, _, product = header.partition(" ")
            product = " ".join(product.split())
            chunks = []
        else:
            chunks.append(line)
    flush()
    return records


def parse_fasta_file(path: Path) -> list[FastaRecord]:
    return parse_fasta(path.read_text())
