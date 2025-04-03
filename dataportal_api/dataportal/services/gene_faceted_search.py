import json
import logging

from elasticsearch_dsl import FacetedSearch, TermsFacet

from dataportal.utils.constants import (
    GENE_ESSENTIALITY,
    DEFAULT_FACET_LIMIT,
    ES_FIELD_PFAM, ES_FIELD_INTERPRO,
    ES_FIELD_KEGG, ES_FIELD_COG_ID,
    ES_FIELD_ISOLATE_NAME,
    ES_FIELD_SPECIES_ACRONYM,
)

logger = logging.getLogger(__name__)


class GeneFacetedSearch(FacetedSearch):
    fields = [ES_FIELD_SPECIES_ACRONYM, GENE_ESSENTIALITY, ES_FIELD_COG_ID,
              ES_FIELD_KEGG, 'go_term', ES_FIELD_PFAM, ES_FIELD_INTERPRO, ES_FIELD_ISOLATE_NAME]

    def __init__(self, query='', filters=None, species_acronym=None, essentiality=None,
                 isolates=None, cog_id=None, kegg=None, go_term=None, pfam=None, interpro=None,
                 limit: int = DEFAULT_FACET_LIMIT):
        self.species_acronym = species_acronym
        self.essentiality = essentiality
        self.isolates = isolates
        self.cog_id = cog_id
        self.kegg = kegg
        self.go_term = go_term
        self.pfam = pfam
        self.interpro = interpro

        self.facets = {
            GENE_ESSENTIALITY: TermsFacet(field=GENE_ESSENTIALITY, size=limit),
            ES_FIELD_PFAM: TermsFacet(field=ES_FIELD_PFAM, size=limit),
            ES_FIELD_INTERPRO: TermsFacet(field=ES_FIELD_INTERPRO, size=limit),
            ES_FIELD_KEGG: TermsFacet(field=ES_FIELD_KEGG, size=limit),
            ES_FIELD_COG_ID: TermsFacet(field=ES_FIELD_COG_ID, size=limit)
        }

        super().__init__(query=query, filters=filters or {})

    def build_search(self):
        s = super().build_search()

        if self.species_acronym:
            s = s.filter('term', species_acronym=self.species_acronym)
        if self.essentiality:
            s = s.filter('terms', essentiality=[self.essentiality])
        if self.cog_id:
            cog_id_values = self.cog_id if isinstance(self.cog_id, list) else [self.cog_id]
            s = s.filter('terms', cog_id=[k for k in cog_id_values])
        if self.kegg:
            kegg_values = self.kegg if isinstance(self.kegg, list) else [self.kegg]
            s = s.filter('terms', kegg=[k.lower() for k in kegg_values])
        if self.go_term:
            go_values = self.go_term if isinstance(self.go_term, list) else [self.go_term]
            s = s.filter('terms', go_term=[g.lower() for g in go_values])
        if self.pfam:
            pfam_values = self.pfam if isinstance(self.pfam, list) else [self.pfam]
            s = s.filter('terms', pfam=pfam_values)
        if self.interpro:
            interpro_values = self.interpro if isinstance(self.interpro, list) else [self.interpro]
            s = s.filter('terms', interpro=interpro_values)
        if self.isolates and isinstance(self.isolates, list) and any(self.isolates):
            s = s.filter('terms', isolate_name=self.isolates)

        # logger.info(f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}")
        return s
