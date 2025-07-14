from typing import List

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search

from dataportal.schema.species_schemas import SpeciesSchema
from dataportal.utils.errors import raise_exception


class SpeciesService:
    INDEX_NAME = "species_index"

    async def get_all_species(self) -> List[SpeciesSchema]:
        """Retrieve all species from Elasticsearch."""
        try:
            search = Search(index=self.INDEX_NAME).query("match_all")
            response = await sync_to_async(search.execute)()

            return [SpeciesSchema.model_validate(hit.to_dict()) for hit in response]
        except Exception as e:
            raise_exception(f"Error retrieving all species: {str(e)}")

    async def get_species_by_acronym(self, acronym: str) -> SpeciesSchema:
        """Retrieve a single species by acronym from Elasticsearch."""
        try:
            search = Search(index=self.INDEX_NAME).query("term", acronym=acronym)
            response = await sync_to_async(search.execute)()

            if not response:
                raise_exception(
                    f"Species with acronym {acronym} not found.", status_code=404
                )

            return SpeciesSchema.model_validate(response[0].to_dict())
        except Exception as e:
            raise_exception(f"Error retrieving species by acronym: {str(e)}")
