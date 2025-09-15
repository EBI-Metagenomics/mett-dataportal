from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Type

from elasticsearch_dsl import Document, Index, connections

DEFAULT_VERSION_FMT = "%Y.%m.%d"


@dataclass(frozen=True)
class IndexConfig:
    """Configuration for a single ES index family (one Document model)."""
    model: Type[Document]
    base_name: str  # e.g. "strain_index"
    settings: Optional[dict]  # mapping/analysis settings copied from model.Index.settings


class IndexNameBuilder:
    """Builds concrete index names like <base>-<version>."""

    def __init__(self, base_name: str, version_fmt: str = DEFAULT_VERSION_FMT) -> None:
        self.base = base_name
        self.version_fmt = version_fmt

    def build(self, version: Optional[str] = None) -> str:
        if version is None:
            version = datetime.utcnow().strftime(self.version_fmt)
        return f"{self.base}-{version}"


class ModelIndexManager:
    """Manage one index family (all versions) for a single Document model."""

    def __init__(self, config: IndexConfig) -> None:
        self.config = config
        self._namer = IndexNameBuilder(config.base_name)

    # ---------- Naming ----------

    def concrete_name(self, version: Optional[str] = None) -> str:
        return self._namer.build(version)

    # ---------- Existence / lifecycle ----------

    def exists(self, name: str) -> bool:
        return Index(name).exists()

    def create(self, name: str) -> str:
        """Create a concrete index with model mapping/settings if it doesn't exist."""
        idx = Index(name)
        if self.config.settings:
            idx.settings(**self.config.settings)
        idx.document(self.config.model)
        if not idx.exists():
            idx.create()
        return name

    def delete(self, name: str) -> None:
        idx = Index(name)
        if idx.exists():
            idx.delete()

    # ---------- Discovery ----------

    def list_versions(self) -> List[str]:
        """List all concrete indices for this family, sorted ascending."""
        client = connections.get_connection()
        res = client.indices.get(index=f"{self.config.base_name}-*")
        return sorted(res.keys())


class ProjectIndexManager:
    """Coordinates multiple Document models (index families)."""

    def __init__(self, models: List[Type[Document]]) -> None:
        self._managers: Dict[str, ModelIndexManager] = {}
        for m in models:
            base = m.Index.name  # treat this as the base name
            settings = getattr(m.Index, "settings", None)
            cfg = IndexConfig(model=m, base_name=base, settings=settings)
            self._managers[base] = ModelIndexManager(cfg)

    @property
    def managers(self) -> Dict[str, ModelIndexManager]:
        return self._managers

    def create_all(
            self,
            version: Optional[str] = None,
            if_exists: str = "skip",  # "skip" | "recreate" | "fail"
    ) -> Dict[str, str]:
        """
        Create concrete indexes for all models.
        Returns { base_name: concrete_name }.
        """
        results: Dict[str, str] = {}
        for base, mgr in self._managers.items():
            concrete = mgr.concrete_name(version)
            if mgr.exists(concrete):
                if if_exists == "recreate":
                    mgr.delete(concrete)
                    mgr.create(concrete)
                elif if_exists == "fail":
                    raise RuntimeError(f"Index already exists: {concrete}")
                # else: skip
            else:
                mgr.create(concrete)
            results[base] = concrete
        return results
