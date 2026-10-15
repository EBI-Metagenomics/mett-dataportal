"""Filesystem locations for the protein database and the older per-combination files."""

from __future__ import annotations

from django.conf import settings

from .constants import (
    DEFAULT_ISOLATE_SPECIES,
    ISOLATE_DB_SUFFIX,
    LEGACY_FAA_FILES,
    SPECIES_PREFIX,
)


def legacy_database_path(database_id: str) -> str | None:
    filename = LEGACY_FAA_FILES.get(database_id)
    if filename is None:
        return None
    return settings.PYHMMER_FAA_BASE_PATH + filename


def isolate_database_path(isolate_name: str) -> str:
    species_dir = DEFAULT_ISOLATE_SPECIES
    for prefix, species in SPECIES_PREFIX:
        if isolate_name.startswith(prefix):
            species_dir = species
            break
    return (
        f"{settings.PYHMMER_ISOLATES_BASE_PATH}{species_dir}/" f"{isolate_name}{ISOLATE_DB_SUFFIX}"
    )
