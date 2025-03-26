import json
import logging

from elasticsearch_dsl import FacetedSearch, TermsFacet, Q

from dataportal.utils.constants import DEFAULT_FACET_LIMIT

logger = logging.getLogger(__name__)


class GeneFacetedSearch(FacetedSearch):
    index = 'gene_index'
    fields = ['species_acronym', 'essentiality', 'cog_id', 'kegg', 'go_term', 'pfam', 'interpro', 'isolate_name']

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
            'pfam': TermsFacet(field='pfam', size=limit),
            'interpro': TermsFacet(field='interpro', size=limit),
            'kegg': TermsFacet(field='kegg', size=limit),
            'cog_id': TermsFacet(field='cog_id', size=limit),
            'essentiality': TermsFacet(field='essentiality', size=limit)
        }

        super().__init__(query=query, filters=filters or {})

    def build_search(self):
        s = super().build_search()

        if self.species_acronym:
            s = s.filter('term', species_acronym=self.species_acronym)
        if self.essentiality:
            s = s.filter('terms', essentiality=[self.essentiality])
        if self.cog_id:
            s = s.filter('terms', cog_id=[self.cog_id])
        if self.kegg:
            s = s.filter('prefix', kegg=self.kegg.lower())
        if self.go_term:
            s = s.filter('prefix', go_term=self.go_term.lower())
        if self.pfam:
            s = s.filter('prefix', pfam=self.pfam.lower())
        if self.interpro:
            s = s.filter('prefix', interpro=self.interpro.lower())
        if self.isolates and isinstance(self.isolates, list) and any(self.isolates):
            s = s.filter('terms', isolate_name=self.isolates)

        logger.info(f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}")
        return s