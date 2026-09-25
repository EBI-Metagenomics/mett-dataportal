#!/usr/bin/env python3
"""Plan or build JBrowse indexes from a mapping TSV and two input roots.

`plan` writes a TSV of one FASTA or GFF per row. Nextflow runs that once,
then indexes each file in its own task. `run` does both steps locally.

  python run.py plan \\
    --map-tsv ../../data/reference/gff-assembly-prefixes-20hm.tsv \\
    --fasta-dir /pub/databases/metagenomics/temp/mett/20hm/v1/assemblies \\
    --gff-base /pub/databases/metagenomics/temp/mett/20hm/v1/annotations \\
    --jobs jobs.tsv

  python run.py run \\
    --map-tsv ../../data/reference/gff-assembly-prefixes-20hm.tsv \\
    --fasta-dir /pub/databases/metagenomics/temp/mett/20hm/v1/assemblies \\
    --gff-base /pub/databases/metagenomics/temp/mett/20hm/v1/annotations \\
    --out ../../data/generated/browser-indexes
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from index_fasta import index_fasta
from index_gff import index_gff
from jobs import DEFAULT_GFF_DIR_TEMPLATE, parse_isolates, plan_jobs, write_jobs

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = SCRIPT_DIR.parents[1] / "data" / "generated" / "browser-indexes"


def add_input_args(parser: argparse.ArgumentParser, *, jobs_file: bool) -> None:
    parser.add_argument(
        "--map-tsv", type=Path, required=True, help="TSV with columns prefix, assembly"
    )
    parser.add_argument(
        "--fasta-dir",
        type=Path,
        help="Directory of assembly FASTA files (required for FASTA indexes)",
    )
    parser.add_argument(
        "--gff-base", type=Path, help="Annotation root (required for GFF indexes)"
    )
    parser.add_argument(
        "--gff-dir-template",
        default=DEFAULT_GFF_DIR_TEMPLATE,
        help=f"GFF directory. Placeholders: {{base}}, {{isolate}}. Default: {DEFAULT_GFF_DIR_TEMPLATE}",
    )
    parser.add_argument(
        "--release", default="v1", help="Output release folder (default: v1)"
    )
    parser.add_argument(
        "--only",
        choices=("all", "fasta", "gff"),
        default="all",
        help="Index FASTA, GFF, or both",
    )
    parser.add_argument(
        "--isolates",
        action="append",
        default=[],
        help="Isolate names to include (repeat or comma-separate). Default: every mapped isolate",
    )
    parser.add_argument(
        "--isolates-file", type=Path, help="File of isolate names to include"
    )
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Skip mapped isolates whose FASTA or GFF is not on disk",
    )
    if jobs_file:
        parser.add_argument(
            "--jobs", type=Path, required=True, help="Where to write the job TSV"
        )


def _jobs_from_args(args: argparse.Namespace) -> list[dict[str, str]]:
    return plan_jobs(
        map_tsv=args.map_tsv,
        fasta_dir=args.fasta_dir,
        gff_base=args.gff_base,
        release=args.release,
        gff_dir_template=args.gff_dir_template,
        isolates=parse_isolates(args.isolates, args.isolates_file),
        only=args.only,
        skip_missing=args.skip_missing,
    )


def command_plan(args: argparse.Namespace) -> int:
    jobs = _jobs_from_args(args)
    write_jobs(jobs, args.jobs)
    print(f"Wrote {len(jobs)} jobs to {args.jobs}")
    return 0


def publish_dir(out: Path, job: dict[str, str]) -> Path:
    if job["kind"] == "fasta":
        return out / job["release"] / job["species"] / "fasta" / job["assembly_folder"]
    return out / job["release"] / job["species"] / "gff3" / job["isolate"]


def command_run(args: argparse.Namespace) -> int:
    jobs = _jobs_from_args(args)
    for job in jobs:
        dest = publish_dir(args.out, job)
        src = Path(job["src"])
        if job["kind"] == "fasta":
            print(f"Indexing FASTA {src.name} -> {dest}")
            index_fasta(src, dest)
        else:
            print(f"Indexing GFF {src.name} -> {dest}")
            file_id = src.name[:-4] if src.name.endswith(".gff") else src.stem
            index_gff(src, dest, file_id=file_id, index_base_url=args.index_base_url)
    print(f"Indexed {len(jobs)} files under {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Write a TSV of files to index")
    add_input_args(plan, jobs_file=True)
    plan.set_defaults(func=command_plan)

    run = sub.add_parser("run", help="Index every mapped FASTA and GFF locally")
    add_input_args(run, jobs_file=False)
    run.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output root (default: {DEFAULT_OUT})",
    )
    run.add_argument(
        "--index-base-url",
        help="Absolute URL prefix written into GFF trix meta URIs (optional)",
    )
    run.set_defaults(func=command_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
