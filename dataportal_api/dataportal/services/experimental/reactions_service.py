import logging
from typing import Optional, List

from asgiref.sync import sync_to_async
from elasticsearch_dsl import Search

from dataportal.schema.experimental.reactions_schemas import (
    ReactionsWithGeneSchema,
    ReactionDetailSchema,
)
from dataportal.services.base_service import BaseService
from dataportal.utils.constants import INDEX_FEATURES
from dataportal.utils.exceptions import ServiceError, GeneNotFoundError

logger = logging.getLogger(__name__)


class ReactionsService(BaseService[ReactionsWithGeneSchema, str]):
    """Service for retrieving reactions data."""

    def __init__(self):
        super().__init__(INDEX_FEATURES)

    async def get_by_id(self, locus_tag: str) -> Optional[ReactionsWithGeneSchema]:
        """Retrieve reactions data for a gene by locus tag."""
        try:
            result = await sync_to_async(self._fetch_reactions_by_identifier)(locus_tag)
            return result
        except GeneNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error fetching reactions data for {locus_tag}: {e}")
            raise ServiceError(f"Failed to fetch reactions data: {str(e)}")

    async def get_all(self, **kwargs) -> List[ReactionsWithGeneSchema]:
        """Not implemented - use search instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search(self, **kwargs) -> List[ReactionsWithGeneSchema]:
        """Not implemented - use search_with_filters instead."""
        raise NotImplementedError("Use search_with_filters method instead")

    async def search_with_filters(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        reaction_id: Optional[str] = None,
        metabolite: Optional[str] = None,
        substrate: Optional[str] = None,
        product: Optional[str] = None,
    ) -> List[ReactionsWithGeneSchema]:
        """Search for reactions data with filters."""
        try:
            results = await sync_to_async(self._fetch_reactions_by_identifiers)(
                locus_tags=locus_tags or [],
                uniprot_ids=uniprot_ids or [],
                reaction_id=reaction_id,
                metabolite=metabolite,
                substrate=substrate,
                product=product,
            )
            return results
        except Exception as e:
            logger.error(f"Error searching reactions data with filters: {e}")
            raise ServiceError(f"Failed to search reactions data: {str(e)}")

    def _fetch_reactions_by_identifier(self, identifier: str) -> ReactionsWithGeneSchema:
        """Fetch reactions data for a single identifier."""
        s = (
            Search(index=self.index_name)
            .filter("term", feature_type="gene")
            .filter("term", has_reactions=True)
            .query("bool", should=[
                {"term": {"locus_tag.keyword": identifier}},
                {"term": {"uniprot_id": identifier}},
            ])
            .extra(size=1)
        )
        
        response = s.execute()
        
        if not response.hits:
            raise GeneNotFoundError(f"Gene with identifier '{identifier}' not found or has no reactions data")
        
        hit = response.hits[0]
        return self._convert_hit_to_reactions_schema(hit)

    def _fetch_reactions_by_identifiers(
        self,
        locus_tags: Optional[List[str]] = None,
        uniprot_ids: Optional[List[str]] = None,
        reaction_id: Optional[str] = None,
        metabolite: Optional[str] = None,
        substrate: Optional[str] = None,
        product: Optional[str] = None,
    ) -> List[ReactionsWithGeneSchema]:
        """Fetch reactions data for multiple identifiers."""
        locus_tags = locus_tags or []
        uniprot_ids = uniprot_ids or []
        
        s = (
            Search(index=self.index_name)
            .filter("term", feature_type="gene")
            .filter("term", has_reactions=True)
        )
        
        should_conditions = []
        if locus_tags:
            should_conditions.append({"terms": {"locus_tag.keyword": locus_tags}})
        if uniprot_ids:
            should_conditions.append({"terms": {"uniprot_id": uniprot_ids}})
        
        if should_conditions:
            s = s.query("bool", should=should_conditions, minimum_should_match=1)
        
        # Apply filters for reactions
        if reaction_id:
            s = s.filter("term", reactions=reaction_id)
        
        # Apply nested filters for reaction_details
        if any([metabolite, substrate, product]):
            nested_conditions = []
            
            if metabolite:
                nested_conditions.append({"term": {"reaction_details.metabolites": metabolite}})
            if substrate:
                nested_conditions.append({"term": {"reaction_details.substrates": substrate}})
            if product:
                nested_conditions.append({"term": {"reaction_details.products": product}})
            
            if nested_conditions:
                s = s.filter("nested", path="reaction_details", query={
                    "bool": {"must": nested_conditions}
                })
        
        total_identifiers = len(locus_tags) + len(uniprot_ids)
        if total_identifiers > 0:
            s = s.extra(size=min(total_identifiers, 1000))
        else:
            s = s.extra(size=100000)
        
        response = s.execute()
        
        results = []
        for hit in response.hits:
            try:
                schema = self._convert_hit_to_reactions_schema(hit)
                if schema.reactions and len(schema.reactions) > 0:
                    results.append(schema)
                else:
                    logger.warning(f"Gene {schema.locus_tag} has has_reactions=True but empty reactions array")
            except Exception as e:
                logger.warning(f"Error converting hit to schema: {e}")
                continue
        
        return results

    def _convert_hit_to_reactions_schema(self, hit) -> ReactionsWithGeneSchema:
        """Convert Elasticsearch hit to ReactionsWithGeneSchema."""
        hit_dict = hit.to_dict()
        
        gene_data = {
            "locus_tag": hit_dict.get("locus_tag"),
            "gene_name": hit_dict.get("gene_name"),
            "uniprot_id": hit_dict.get("uniprot_id"),
            "product": hit_dict.get("product"),
            "isolate_name": hit_dict.get("isolate_name"),
            "species_scientific_name": hit_dict.get("species_scientific_name"),
            "species_acronym": hit_dict.get("species_acronym"),
        }
        
        reactions_list = hit_dict.get("reactions", [])
        reaction_details_raw = hit_dict.get("reaction_details", [])
        reaction_details_list = []
        
        if reaction_details_raw:
            for entry in reaction_details_raw:
                reaction_details_list.append(ReactionDetailSchema(
                    reaction=entry.get("reaction"),
                    gpr=entry.get("gpr"),
                    substrates=entry.get("substrates", []),
                    products=entry.get("products", []),
                    metabolites=entry.get("metabolites", []),
                ))
        
        return ReactionsWithGeneSchema(
            **gene_data,
            reactions=reactions_list,
            reaction_details=reaction_details_list
        )

