"""Request-scoped METT release selection and portal read-index resolution."""

from __future__ import annotations

import os
from contextvars import ContextVar, Token
from typing import Optional

from dataportal.elasticsearch.names import (
    CURRENT_TOKEN,
    IndexNameError,
    coerce_family,
    current_alias_name,
    normalize_release,
    release_alias_name,
)


_request_release: ContextVar[Optional[str]] = ContextVar("mett_request_release", default=None)


def set_request_release(release: Optional[str]) -> Token:
    """Bind the release for this request. Pass None to clear to env/default."""
    if release is None or str(release).strip() == "":
        return _request_release.set(None)
    return _request_release.set(normalize_release(release))


def reset_request_release(token: Token) -> None:
    _request_release.reset(token)


def default_release() -> str:
    return normalize_release(os.getenv("METT_RELEASE", CURRENT_TOKEN))


def selected_release() -> str:
    bound = _request_release.get()
    if bound:
        return bound
    return default_release()


def readable_release_versions() -> list[str]:
    """Versions scientists may select, plus the synthetic `current` token."""
    try:
        from dataportal.models.releases import MettRelease

        qs = MettRelease.objects.filter(
            status__in=(
                MettRelease.Status.READY,
                MettRelease.Status.CURRENT,
                MettRelease.Status.ARCHIVED,
                MettRelease.Status.BUILDING,
            )
        ).values_list("version", "status")
        return [row[0] for row in qs]
    except Exception:
        return []


def assert_readable_release(release: str) -> str:
    """Validate a requested version exists and is readable. `current` is always allowed."""
    rel = normalize_release(release)
    if rel == CURRENT_TOKEN:
        return rel
    versions = {v.lower() for v in readable_release_versions()}
    if rel not in versions:
        raise IndexNameError(
            f"Unknown or unreadable METT release '{rel}'. "
            "Choose 'current' or a listed version from GET /releases."
        )
    return rel


def resolve_read_index(family: str, release: Optional[str] = None) -> str:
    """Alias the portal should query for this family.

    `current` → `mett-current-{family}` (set by promote_release).
    `v1` → `mett-v1-{family}`.
    """
    fam = coerce_family(family)
    rel = normalize_release(release) if release is not None else selected_release()
    if rel == CURRENT_TOKEN:
        return current_alias_name(fam)
    return release_alias_name(rel, fam)
