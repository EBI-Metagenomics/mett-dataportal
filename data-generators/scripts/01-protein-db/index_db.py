"""Build the membership index search uses to avoid scanning the FASTA."""

from __future__ import annotations

import csv
import shutil
import sqlite3
import subprocess
from pathlib import Path


def build_sqlite(members_tsv: Path, sqlite_path: Path) -> None:
    if sqlite_path.exists():
        sqlite_path.unlink()
    connection = sqlite3.connect(sqlite_path)
    try:
        connection.executescript(
            """
            CREATE TABLE sequences (
                seq_id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                product TEXT NOT NULL
            );
            CREATE TABLE members (
                seq_id TEXT NOT NULL,
                species TEXT NOT NULL,
                isolate TEXT NOT NULL,
                locus_tag TEXT NOT NULL,
                is_type INTEGER NOT NULL,
                PRIMARY KEY (seq_id, locus_tag)
            );
            CREATE INDEX idx_members_species ON members(species);
            CREATE INDEX idx_members_isolate ON members(isolate);
            CREATE INDEX idx_members_type ON members(is_type);
            """
        )
        with members_tsv.open(newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                connection.execute(
                    """
                    INSERT INTO sequences (seq_id, sha256, product)
                    VALUES (?, ?, ?)
                    ON CONFLICT(seq_id) DO NOTHING
                    """,
                    (row["seq_id"], row["sha256"], row["product"]),
                )
                connection.execute(
                    """
                    INSERT INTO members (seq_id, species, isolate, locus_tag, is_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["seq_id"],
                        row["species"],
                        row["isolate"],
                        row["locus_tag"],
                        int(row["is_type"]),
                    ),
                )
        connection.commit()
    finally:
        connection.close()


def build_ssi(faa_path: Path) -> bool:
    """Write ``<faa>.ssi`` when esl-sfetch is on PATH. Search can scan without it."""
    executable = shutil.which("esl-sfetch")
    if not executable:
        print("esl-sfetch not on PATH; skipping SSI index")
        return False
    subprocess.run([executable, "--index", str(faa_path)], check=True)
    return True
