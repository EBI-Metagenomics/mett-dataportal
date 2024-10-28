from typing import List

from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404

from dataportal.models import Species
from dataportal.schemas import SpeciesSchema


class SpeciesService:

    async def get_all_species(self) -> List[SpeciesSchema]:
        try:
            species = await sync_to_async(list)(Species.objects.all())
            return [SpeciesSchema.model_validate(sp) for sp in species]
        except Exception as e:
            raise Exception(f"Error retrieving all species: {str(e)}")

    async def get_species_by_id(self, species_id: int) -> SpeciesSchema:
        try:
            species = await sync_to_async(lambda: get_object_or_404(Species, id=species_id))()
            return SpeciesSchema.model_validate(species)
        except Exception as e:
            raise Exception(f"Error retrieving species by ID: {str(e)}")
