#!/usr/bin/env python3
"""Plan, stage, merge, and index the METT protein database.

  python run.py plan --batch all --jobs sources.tsv
  python run.py stage --faa isolate.faa --isolate BU_ATCC8492 --species BU --type-strain --out BU_ATCC8492.jsonl
  python run.py merge --chunks ./chunks --species-csv ../../data/reference/species.csv --out ../../data/generated/protein-db
  python run.py index --faa ../../data/generated/protein-db/mett_proteins.faa --members ../../data/generated/protein-db/members.tsv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from index_db import build_sqlite, build_ssi
from merge import load_chunks, write_catalog, write_database
from plan import BATCHES, FAA_TEMPLATE, plan_batches, read_manifest, write_sources
from stage import stage_isolate

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SPECIES = SCRIPT_DIR.parents[1] / "data" / "reference" / "species.csv"
DEFAULT_OUT = SCRIPT_DIR.parents[1] / "data" / "generated" / "protein-db"


def _batch_names(value: str) -> list[str]:
    if value == "all":
        return list(BATCHES)
    names = [part.strip() for part in value.split(",") if part.strip()]
    unknown = [name for name in names if name not in BATCHES]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"Unknown batch {', '.join(unknown)}. Choose from: all, {', '.join(BATCHES)}"
        )
    return names


def command_plan(args: argparse.Namespace) -> None:
    if args.manifest:
        rows = read_manifest(args.manifest)
    else:
        roots = {}
        maps = {}
        if args.hd_root:
            roots["hd"] = args.hd_root
        if args.hm_root:
            roots["20hm"] = args.hm_root
        if args.hd_map:
            maps["hd"] = args.hd_map
        if args.hm_map:
            maps["20hm"] = args.hm_map
        rows = plan_batches(
            _batch_names(args.batch),
            species_csv=args.species_csv,
            roots=roots or None,
            maps=maps or None,
            template=args.faa_template,
            skip_missing=args.skip_missing,
        )
    write_sources(rows, args.jobs)
    print(f"Wrote {len(rows)} isolates to {args.jobs}")


def command_stage(args: argparse.Namespace) -> None:
    count = stage_isolate(
        args.faa,
        isolate=args.isolate,
        species=args.species,
        is_type=args.type_strain,
        collection=args.collection,
        out=args.out,
    )
    print(f"Staged {count} proteins from {args.isolate}")


def command_merge(args: argparse.Namespace) -> None:
    members = load_chunks(args.chunks)
    if not members:
        raise SystemExit(f"No JSONL chunks in {args.chunks}")
    faa_path, members_path = write_database(members, args.out)
    catalog_path = args.out / "catalog.json"
    write_catalog(members_path, args.species_csv, catalog_path)
    print(f"Wrote {faa_path}")
    print(f"Wrote {members_path}")
    print(f"Wrote {catalog_path}")


def command_index(args: argparse.Namespace) -> None:
    sqlite_path = args.out / "members.sqlite"
    build_sqlite(args.members, sqlite_path)
    print(f"Wrote {sqlite_path}")
    if build_ssi(args.faa):
        print(f"Wrote {args.faa}.ssi")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="Write sources.tsv")
    plan.add_argument(
        "--batch", default="all", help="hd, 20hm, all, or a comma-separated list"
    )
    plan.add_argument("--species-csv", type=Path, default=DEFAULT_SPECIES)
    plan.add_argument("--hd-root", default="")
    plan.add_argument("--hm-root", default="")
    plan.add_argument("--hd-map", type=Path)
    plan.add_argument("--hm-map", type=Path)
    plan.add_argument("--faa-template", default=FAA_TEMPLATE)
    plan.add_argument(
        "--manifest", type=Path, help="Use this TSV instead of the batch profiles"
    )
    plan.add_argument("--skip-missing", action="store_true")
    plan.add_argument("--jobs", type=Path, required=True)
    plan.set_defaults(func=command_plan)

    stage = commands.add_parser("stage", help="Convert one FAA to JSONL")
    stage.add_argument("--faa", type=Path, required=True)
    stage.add_argument("--isolate", required=True)
    stage.add_argument("--species", required=True)
    stage.add_argument("--type-strain", action="store_true")
    stage.add_argument("--collection", default="")
    stage.add_argument("--out", type=Path, required=True)
    stage.set_defaults(func=command_stage)

    merge = commands.add_parser(
        "merge", help="Deduplicate chunks into mett_proteins.faa"
    )
    merge.add_argument("--chunks", type=Path, required=True)
    merge.add_argument("--species-csv", type=Path, default=DEFAULT_SPECIES)
    merge.add_argument("--out", type=Path, default=DEFAULT_OUT)
    merge.set_defaults(func=command_merge)

    index = commands.add_parser("index", help="Build members.sqlite and the SSI file")
    index.add_argument("--faa", type=Path, required=True)
    index.add_argument("--members", type=Path, required=True)
    index.add_argument("--out", type=Path, default=DEFAULT_OUT)
    index.set_defaults(func=command_index)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
