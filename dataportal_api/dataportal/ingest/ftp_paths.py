"""Configurable FTP layouts for FASTA / GFF ingest.

Annotation and assembly trees differ by species batch. Defaults match the
published METT v1 layout; 20hm (and later) batches override the root and,
when needed, the directory template.
"""

from __future__ import annotations

import re
from argparse import ArgumentParser
from typing import Iterable, Mapping, Optional, Sequence

DEFAULT_GFF_DIR_TEMPLATE = "{base}/{isolate}/functional_annotation/merged_gff"
DEFAULT_FAA_PATH_TEMPLATE = (
    "{base}/{isolate}/functional_annotation/prokka/{isolate}.faa"
)
DEFAULT_FASTA_EXTENSIONS: tuple[str, ...] = (".fa", ".fna", ".fasta")


def parse_fasta_extensions(value: Optional[str]) -> tuple[str, ...]:
    if value is None or not str(value).strip():
        return DEFAULT_FASTA_EXTENSIONS
    parts = [p.strip() for p in str(value).replace(";", ",").split(",") if p.strip()]
    return tuple(p if p.startswith(".") else f".{p}" for p in parts)


def is_fasta_filename(
    name: str, extensions: Sequence[str] = DEFAULT_FASTA_EXTENSIONS
) -> bool:
    lower = (name or "").lower()
    return any(lower.endswith(ext.lower()) for ext in extensions)


def strip_fasta_extension(
    name: str, extensions: Sequence[str] = DEFAULT_FASTA_EXTENSIONS
) -> str:
    lower = (name or "").lower()
    for ext in sorted(extensions, key=len, reverse=True):
        if lower.endswith(ext.lower()):
            return name[: -len(ext)]
    return name


def format_ftp_path(template: str, **kwargs: object) -> str:
    """Fill `{base}`, `{isolate}`, and any extra placeholders; collapse slashes."""
    raw_base = kwargs.get("base")
    leading = str(raw_base or "").startswith("/")

    values: dict[str, str] = {}
    for key, raw in kwargs.items():
        text = "" if raw is None else str(raw).strip().replace("\\", "/")
        values[key] = "/".join(p for p in text.split("/") if p)

    class _Safe(dict):
        def __missing__(self, key: str) -> str:
            return ""

    rendered = (template or "").format_map(_Safe(values))
    rendered = re.sub(r"/+", "/", rendered.replace("\\", "/"))
    if leading and rendered and not rendered.startswith("/"):
        rendered = "/" + rendered
    return rendered.rstrip("/")


def template_has_isolate(template: str) -> bool:
    return "{isolate}" in (template or "")


def add_gff_dir_template_argument(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--gff-dir-template",
        default=DEFAULT_GFF_DIR_TEMPLATE,
        help=(
            "GFF directory on FTP. Placeholders: {base} (annotation root), {isolate}. "
            f"Default: {DEFAULT_GFF_DIR_TEMPLATE}"
        ),
    )


def add_faa_path_template_argument(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--faa-path-template",
        default=DEFAULT_FAA_PATH_TEMPLATE,
        help=(
            "Protein FASTA on FTP. Placeholders: {base}, {isolate}. "
            f"Default: {DEFAULT_FAA_PATH_TEMPLATE}"
        ),
    )


def add_fasta_extensions_argument(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--fasta-extensions",
        default=",".join(DEFAULT_FASTA_EXTENSIONS),
        help=(
            "Comma-separated assembly filename suffixes to ingest "
            f"(default: {','.join(DEFAULT_FASTA_EXTENSIONS)})."
        ),
    )


def mapping_lookup(
    mapping: Mapping[str, str],
    filename: str,
    extensions: Iterable[str] = DEFAULT_FASTA_EXTENSIONS,
) -> Optional[str]:
    """Resolve isolate from an assembly filename, with or without a FASTA suffix."""
    if filename in mapping:
        return mapping[filename]
    stem = strip_fasta_extension(filename, tuple(extensions))
    if stem in mapping:
        return mapping[stem]
    for ext in extensions:
        keyed = f"{stem}{ext}"
        if keyed in mapping:
            return mapping[keyed]
    return None
