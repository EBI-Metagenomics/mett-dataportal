"""Strain annotation provenance applied during import_strains."""

from __future__ import annotations

from typing import Optional


def parse_isolate_allowlist(
    isolates: Optional[str] = None,
    isolates_file: Optional[str] = None,
) -> Optional[set[str]]:
    """Comma-separated names and/or a file (one name per line or comma-separated).

    Returns None when neither source is given (import every isolate).
    """
    names: list[str] = []
    if isolates:
        names.extend(_split_isolate_tokens(isolates))
    if isolates_file:
        with open(isolates_file, encoding="utf-8") as handle:
            names.extend(_split_isolate_tokens(handle.read()))
    cleaned = {token for token in names if token}
    return cleaned or None


def _split_isolate_tokens(text: str) -> list[str]:
    parts: list[str] = []
    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for token in line.split(","):
            name = token.strip()
            if name:
                parts.append(name)
    return parts


def isolate_allowed(isolate_name: str, allowlist: Optional[set[str]], *aliases: str) -> bool:
    if allowlist is None:
        return True
    candidates = {isolate_name, *aliases}
    return any(candidate in allowlist for candidate in candidates if candidate)


def build_annotation_payload(
    pipeline: Optional[str] = None,
    pipeline_version: Optional[str] = None,
    processing_reference: Optional[str] = None,
    processing_document_url: Optional[str] = None,
) -> Optional[dict]:
    """Return an annotation dict when any flag is set; otherwise None (leave existing)."""
    values = {
        "pipeline": _clean(pipeline),
        "pipeline_version": _clean(pipeline_version),
        "processing_reference": _clean(processing_reference),
        "processing_document_url": _clean(processing_document_url),
    }
    if not any(values.values()):
        return None
    return values


def apply_annotation(doc, payload: Optional[dict]) -> None:
    if not payload:
        return
    doc.annotation = payload


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
