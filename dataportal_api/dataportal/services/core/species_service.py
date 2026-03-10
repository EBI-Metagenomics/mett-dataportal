import logging
from typing import Dict, List, Optional

from asgiref.sync import sync_to_async

from dataportal.models.species import SpeciesDocument
from dataportal.schema.core.species_schemas import SpeciesSchema
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import INDEX_SPECIES
from dataportal.utils.errors import raise_exception
from dataportal.utils.exceptions import SpeciesNotFoundError
from dataportal.utils.species_registry import update_species_enabled

logger = logging.getLogger(__name__)


class SpeciesService(BaseService[SpeciesSchema, dict]):
    """Service for managing species data operations."""

    def __init__(self):
        super().__init__(INDEX_SPECIES)
        # Instance cache: species acronym (lower) -> NCBI taxonomy ID
        self._acronym_to_taxid: Dict[str, int] = {}
        self._default_taxid: Optional[int] = None

    async def get_taxonomy_id(self, species_acronym: Optional[str] = None) -> int:
        """
        Resolve species acronym to NCBI taxonomy ID.
        Uses instance cache; fetches from ES on cache miss.
        When species_acronym is None or lookup fails, returns first enabled species's taxonomy_id.
        """
        if species_acronym:
            acr = species_acronym.strip().lower()
            if acr in self._acronym_to_taxid:
                return self._acronym_to_taxid[acr]
            try:
                species = await self.get_species_by_acronym(species_acronym.strip().upper())
                taxid = species.taxonomy_id
                self._acronym_to_taxid[acr] = taxid
                return taxid
            except Exception as e:
                logger.warning(
                    "Could not resolve species '%s' to taxonomy_id, using default: %s",
                    species_acronym,
                    e,
                )
        # No species or lookup failed: use first enabled species as default
        if self._default_taxid is None:
            all_species = await self.get_all()
            if all_species:
                self._default_taxid = all_species[0].taxonomy_id
                logger.debug("Default taxonomy_id set to %s", self._default_taxid)
            else:
                raise ValueError(
                    "No species in database; cannot determine taxonomy ID. "
                    "Please add species data or provide species_acronym."
                )
        return self._default_taxid

    async def get_by_id(self, id: str) -> Optional[SpeciesSchema]:
        """Retrieve a single species by ID (acronym)."""
        try:
            search = self._create_search().query("term", acronym=id).filter("term", enabled=True)
            response = await self._execute_search(search)

            if not response:
                return None

            return SpeciesSchema.model_validate(response[0].to_dict())
        except Exception as e:
            self._handle_elasticsearch_error(e, f"get_by_id for species {id}")

    async def get_all(self, **kwargs) -> List[SpeciesSchema]:
        """Retrieve all enabled species from Elasticsearch."""
        try:
            search = self._create_search().query("match_all").filter("term", enabled=True)
            response = await self._execute_search(search)

            return [self._convert_hit_to_entity(hit) for hit in response]
        except Exception as e:
            self._handle_elasticsearch_error(e, "get_all species")

    async def search(self, query: dict) -> List[SpeciesSchema]:
        """Search species based on query parameters."""
        try:
            search = self._create_search()

            # Apply search filters if provided
            if query.get("acronym"):
                search = search.query("term", acronym=query["acronym"])
            elif query.get("scientific_name"):
                search = search.query("match", scientific_name=query["scientific_name"])
            else:
                search = search.query("match_all")

            # Always filter to only enabled species
            search = search.filter("term", enabled=True)

            response = await self._execute_search(search)
            return [self._convert_hit_to_entity(hit) for hit in response]
        except Exception as e:
            self._handle_elasticsearch_error(e, "search species")

    async def get_species_by_acronym(self, acronym: str) -> SpeciesSchema:
        """Retrieve a single species by acronym from Elasticsearch."""
        species = await self.get_by_id(acronym)
        if not species:
            raise_exception(f"Species with acronym {acronym} not found.")
        return species

    def _convert_hit_to_entity(self, hit) -> SpeciesSchema:
        return SpeciesSchema.model_validate(hit.to_dict())

    async def get_all_species(self) -> List[SpeciesSchema]:
        return await self.get_all()

    def _set_species_enabled_sync(self, acronym: str, enabled: bool) -> SpeciesSchema:
        """Sync implementation: get species doc by id, set enabled, save. Raises if not found."""
        normalized = acronym.strip().upper()
        try:
            doc = SpeciesDocument.get(id=normalized)
        except Exception as e:
            logger.warning("Species document not found for acronym=%s: %s", normalized, e)
            raise SpeciesNotFoundError(species_acronym=normalized, message="Species not found")
        doc.enabled = enabled
        doc.save()
        return SpeciesSchema(
            scientific_name=doc.scientific_name,
            common_name=doc.common_name,
            acronym=doc.acronym,
            taxonomy_id=doc.taxonomy_id,
            enabled=doc.enabled,
        )

    async def set_species_enabled(self, acronym: str, enabled: bool) -> SpeciesSchema:
        """
        Enable or disable a species by acronym. Updates Elasticsearch and the in-memory registry.
        Raises SpeciesNotFoundError if the species does not exist.
        """
        result = await sync_to_async(self._set_species_enabled_sync)(acronym, enabled)
        update_species_enabled(acronym, enabled)
        return result
