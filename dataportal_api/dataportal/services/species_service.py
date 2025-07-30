from dataportal.schema.species_schemas import SpeciesSchema
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import ES_INDEX_SPECIES
from dataportal.utils.errors import raise_exception


class SpeciesService(BaseService[SpeciesSchema, dict]):
    """Service for managing species data operations."""

    def __init__(self):
        super().__init__(ES_INDEX_SPECIES)

    async def get_by_id(self, id: str) -> SpeciesSchema | None:
        """Retrieve a single species by ID (acronym)."""
        try:
            search = self._create_search().query("term", acronym=id)
            response = await self._execute_search(search)

            if not response:
                return None

            return SpeciesSchema.model_validate(response[0].to_dict())
        except Exception as e:
            self._handle_elasticsearch_error(e, f"get_by_id for species {id}")

    async def get_all(self, **kwargs) -> list[SpeciesSchema]:
        """Retrieve all species from Elasticsearch."""
        try:
            search = self._create_search().query("match_all")
            response = await self._execute_search(search)

            return [self._convert_hit_to_entity(hit) for hit in response]
        except Exception as e:
            self._handle_elasticsearch_error(e, "get_all species")

    async def search(self, query: dict) -> list[SpeciesSchema]:
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

    async def get_all_species(self) -> list[SpeciesSchema]:
        return await self.get_all()
