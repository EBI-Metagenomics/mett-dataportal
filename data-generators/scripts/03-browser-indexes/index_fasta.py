#!/usr/bin/env python3
"""Build JBrowse FASTA indexes for one assembly.

Writes, next to each other in --out:

  {name}.gz
  {name}.gz.fai
  {name}.gz.gzi

The gene viewer loads those three files. `.gzi` comes from `bgzip -i`
(or `bgzip -r` when the input is already bgzipped).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def require_tools(names: list[str]) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        raise SystemExit(
            "Missing required tools on PATH: "
            + ", ".join(missing)
            + ". Install htslib (bgzip, tabix) and samtools."
        )


def index_fasta(fasta: Path, out_dir: Path) -> list[Path]:
    require_tools(["bgzip", "samtools"])
    if not fasta.is_file():
        raise FileNotFoundError(fasta)
    out_dir.mkdir(parents=True, exist_ok=True)

    src = fasta.resolve()
    if src.name.endswith(".gz"):
        gz = out_dir / src.name
        if src != gz.resolve():
            shutil.copyfile(src, gz)
        gzi = Path(str(gz) + ".gzi")
        if not gzi.is_file() or gzi.stat().st_size == 0:
            subprocess.run(["bgzip", "-r", "-f", str(gz)], check=True)
    else:
        plain = out_dir / src.name
        if src != plain.resolve():
            shutil.copyfile(src, plain)
        subprocess.run(["bgzip", "-i", "-f", str(plain)], check=True)
        gz = Path(str(plain) + ".gz")

    subprocess.run(["samtools", "faidx", str(gz)], check=True)
    produced = [gz, Path(str(gz) + ".fai"), Path(str(gz) + ".gzi")]
    missing = [
        path for path in produced if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise SystemExit(
            "FASTA indexing did not produce: " + ", ".join(map(str, missing))
        )
    return produced


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fasta",
        type=Path,
        required=True,
        help="Assembly FASTA (.fa, .fna, .fasta, or .gz)",
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="Directory for the indexed FASTA"
    )
    args = parser.parse_args(argv)
    produced = index_fasta(args.fasta, args.out)
    for path in produced:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
