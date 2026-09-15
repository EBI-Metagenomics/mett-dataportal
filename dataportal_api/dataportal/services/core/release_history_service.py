"""Multi-index presence of a strain or gene across readable METT releases."""

from __future__ import annotations

import logging

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Q, Search

from dataportal.elasticsearch.history import (
    alias_names,
    dedupe_appearances,
    map_index_name_to_release,
    readable_aliases_for_family,
)
from dataportal.elasticsearch.names import FAMILY_FEATURES, FAMILY_STRAINS
from dataportal.schema.core.release_history_schemas import (
    GeneReleaseAppearanceSchema,
    GeneReleaseHistorySchema,
    GenomeReleaseAppearanceSchema,
    GenomeReleaseHistorySchema,
)
from dataportal.services.core.genome_service import _annotation_schema
from dataportal.utils.exceptions import ServiceError

logger = logging.getLogger(__name__)


class ReleaseHistoryService:
    async def get_genome_history(self, isolate_name: str) -> GenomeReleaseHistorySchema:
        try:
            rows = await sync_to_async(readable_aliases_for_family)(FAMILY_STRAINS)
            appearances = await sync_to_async(self._search_strain_appearances)(isolate_name, rows)
            return GenomeReleaseHistorySchema(
                isolate_name=isolate_name,
                appearances=appearances,
            )
        except ServiceError:
            raise
        except Exception as exc:
            logger.error("Genome release history failed for %s: %s", isolate_name, exc)
            raise ServiceError(f"Failed to fetch genome release history: {exc}") from exc

    async def get_gene_history(self, locus_tag: str) -> GeneReleaseHistorySchema:
        try:
            rows = await sync_to_async(readable_aliases_for_family)(FAMILY_FEATURES)
            appearances = await sync_to_async(self._search_gene_appearances)(locus_tag, rows)
            return GeneReleaseHistorySchema(locus_tag=locus_tag, appearances=appearances)
        except ServiceError:
            raise
        except Exception as exc:
            logger.error("Gene release history failed for %s: %s", locus_tag, exc)
            raise ServiceError(f"Failed to fetch gene release history: {exc}") from exc

    def _search_strain_appearances(
        self, isolate_name: str, rows
    ) -> list[GenomeReleaseAppearanceSchema]:
        indexes = alias_names(rows)
        if not indexes:
            return []
        search = Search(index=indexes).query(
            Q(
                "bool",
                should=[
                    Q("term", _id=isolate_name),
                    Q("term", **{"isolate_name.keyword": isolate_name}),
                ],
                minimum_should_match=1,
            )
        )[:50]
        response = search.execute()
        raw: list[dict] = []
        for hit in response:
            mapped = map_index_name_to_release(getattr(hit.meta, "index", ""), rows, FAMILY_STRAINS)
            if not mapped:
                continue
            source = hit.to_dict()
            raw.append(
                {
                    "version": mapped.version,
                    "status": mapped.status,
                    "is_current": mapped.is_current,
                    "annotation": _annotation_schema(source.get("annotation")),
                }
            )
        return [GenomeReleaseAppearanceSchema(**row) for row in dedupe_appearances(raw)]

    def _search_gene_appearances(self, locus_tag: str, rows) -> list[GeneReleaseAppearanceSchema]:
        indexes = alias_names(rows)
        if not indexes:
            return []
        search = (
            Search(index=indexes)
            .filter("term", **{"locus_tag.keyword": locus_tag})
            .filter("term", feature_type="gene")
        )[:50]
        response = search.execute()
        raw: list[dict] = []
        for hit in response:
            mapped = map_index_name_to_release(
                getattr(hit.meta, "index", ""), rows, FAMILY_FEATURES
            )
            if not mapped:
                continue
            source = hit.to_dict()
            raw.append(
                {
                    "version": mapped.version,
                    "status": mapped.status,
                    "is_current": mapped.is_current,
                    "isolate_name": source.get("isolate_name"),
                }
            )
        annotations = self._strain_annotations_by_version(
            {row["isolate_name"] for row in raw if row.get("isolate_name")}
        )
        for row in raw:
            isolate = row.get("isolate_name")
            if isolate:
                row["annotation"] = annotations.get((row["version"], isolate))
        return [GeneReleaseAppearanceSchema(**row) for row in dedupe_appearances(raw)]

    def _strain_annotations_by_version(
        self, isolate_names: set[str]
    ) -> dict[tuple[str, str], object]:
        if not isolate_names:
            return {}
        strain_rows = readable_aliases_for_family(FAMILY_STRAINS)
        indexes = alias_names(strain_rows)
        if not indexes:
            return {}
        isolates = list(isolate_names)
        size = min(200, max(50, len(isolates) * max(len(strain_rows), 1)))
        search = Search(index=indexes).query(
            Q(
                "bool",
                should=[
                    Q("ids", values=isolates),
                    Q("terms", **{"isolate_name.keyword": isolates}),
                ],
                minimum_should_match=1,
            )
        )[:size]
        found: dict[tuple[str, str], object] = {}
        for hit in search.execute():
            mapped = map_index_name_to_release(
                getattr(hit.meta, "index", ""), strain_rows, FAMILY_STRAINS
            )
            if not mapped:
                continue
            source = hit.to_dict()
            isolate = source.get("isolate_name") or getattr(hit.meta, "id", None)
            if not isolate:
                continue
            found[(mapped.version, isolate)] = _annotation_schema(source.get("annotation"))
        return found
