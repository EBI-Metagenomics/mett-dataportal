#!/usr/bin/env python3
"""Build JBrowse GFF indexes for one annotations file.

Drops the embedded ##FASTA section, sorts with `jbrowse sort-gff`, then writes:

  {name}.gz
  {name}.gz.tbi
  trix/{name}.gz.ix
  trix/{name}.gz.ixx
  trix/{name}.gz_meta.json

`name` is the source GFF filename (`AR_VPI0990_annotations.gff`), which is
what the gene viewer requests.
"""

from __future__ import annotations

import argparse
import json
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
            + ". Install htslib (bgzip, tabix) and the jbrowse CLI."
        )


def trim_gff_text(text: str) -> str:
    """Keep annotation records and drop an embedded FASTA section."""
    kept: list[str] = []
    for line in text.splitlines(keepends=True):
        if line.startswith("##FASTA"):
            break
        kept.append(line if line.endswith("\n") else line + "\n")
    if not any(line.strip() and not line.startswith("#") for line in kept):
        raise ValueError("GFF has no feature rows after removing ##FASTA")
    return "".join(kept)


def rewrite_local_paths(node: object, index_base_url: str | None) -> None:
    """Turn JBrowse LocalPathLocation entries into URIs the browser can fetch."""
    if isinstance(node, dict):
        if node.get("locationType") == "LocalPathLocation" and "localPath" in node:
            local = str(node.pop("localPath")).replace("\\", "/")
            name = local.rsplit("/", 1)[-1]
            relative = f"trix/{name}" if "/trix/" in f"/{local}" else name
            if index_base_url:
                node["uri"] = index_base_url.rstrip("/") + "/" + relative
            else:
                node["uri"] = relative
            node["locationType"] = "UriLocation"
        for value in node.values():
            rewrite_local_paths(value, index_base_url)
    elif isinstance(node, list):
        for item in node:
            rewrite_local_paths(item, index_base_url)


def normalize_trix(out_dir: Path, gz_name: str) -> list[Path]:
    """Rename text-index products to the filenames the gene viewer requests."""
    trix = out_dir / "trix"
    if not trix.is_dir():
        raise SystemExit(f"jbrowse text-index did not create {trix}")
    expected = [
        trix / f"{gz_name}.ix",
        trix / f"{gz_name}.ixx",
        trix / f"{gz_name}_meta.json",
    ]
    suffixes = (".ix", ".ixx", "_meta.json")
    for dest, suffix in zip(expected, suffixes):
        if dest.is_file() and dest.stat().st_size > 0:
            continue
        matches = [
            path
            for path in trix.iterdir()
            if path.is_file() and path.name.endswith(suffix) and path != dest
        ]
        if len(matches) == 1:
            matches[0].replace(dest)
        if not dest.is_file() or dest.stat().st_size == 0:
            raise SystemExit(f"Missing text index {dest}")
    meta = expected[2]
    payload = json.loads(meta.read_text())
    rewrite_local_paths(payload, None)
    meta.write_text(json.dumps(payload, indent=2) + "\n")
    return expected


def apply_index_base_url(meta_path: Path, index_base_url: str) -> None:
    payload = json.loads(meta_path.read_text())

    def prefix(node: object) -> None:
        if isinstance(node, dict):
            uri = node.get("uri")
            if isinstance(uri, str) and uri.startswith("trix/"):
                node["uri"] = index_base_url.rstrip("/") + "/" + uri
            for value in node.values():
                prefix(value)
        elif isinstance(node, list):
            for item in node:
                prefix(item)

    prefix(payload)
    meta_path.write_text(json.dumps(payload, indent=2) + "\n")


def index_gff(
    gff: Path,
    out_dir: Path,
    *,
    file_id: str | None = None,
    index_base_url: str | None = None,
) -> list[Path]:
    require_tools(["bgzip", "tabix", "jbrowse"])
    if not gff.is_file():
        raise FileNotFoundError(gff)
    out_dir.mkdir(parents=True, exist_ok=True)

    trimmed = out_dir / f".{gff.name}.trimmed"
    sorted_gff = out_dir / gff.name
    trimmed.write_text(trim_gff_text(gff.read_text()))
    try:
        with sorted_gff.open("w") as handle:
            subprocess.run(
                ["jbrowse", "sort-gff", str(trimmed)], check=True, stdout=handle
            )
    finally:
        trimmed.unlink(missing_ok=True)

    subprocess.run(["bgzip", "-f", str(sorted_gff)], check=True)
    gz = out_dir / f"{gff.name}.gz"
    subprocess.run(["tabix", "-f", "-p", "gff", str(gz)], check=True)

    command = ["jbrowse", "text-index", "--file", str(gz), "--out", str(out_dir)]
    if file_id:
        command.extend(["--fileId", file_id])
    subprocess.run(command, check=True)

    trix_files = normalize_trix(out_dir, gz.name)
    if index_base_url:
        apply_index_base_url(trix_files[2], index_base_url)

    produced = [gz, Path(str(gz) + ".tbi"), *trix_files]
    missing = [
        path for path in produced if not path.is_file() or path.stat().st_size == 0
    ]
    if missing:
        raise SystemExit(
            "GFF indexing did not produce: " + ", ".join(map(str, missing))
        )
    return produced


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gff", type=Path, required=True, help="Annotations GFF")
    parser.add_argument(
        "--out", type=Path, required=True, help="Directory for the indexed GFF"
    )
    parser.add_argument(
        "--file-id",
        help="text-index file id (default: GFF filename without .gff)",
    )
    parser.add_argument(
        "--index-base-url",
        help="Absolute URL prefix written into trix meta URIs (optional)",
    )
    args = parser.parse_args(argv)
    file_id = args.file_id
    if not file_id:
        file_id = (
            args.gff.name[:-4] if args.gff.name.endswith(".gff") else args.gff.stem
        )
    produced = index_gff(
        args.gff,
        args.out,
        file_id=file_id,
        index_base_url=args.index_base_url,
    )
    for path in produced:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
