import logging

from elasticsearch_dsl import FacetedSearch, TermsFacet

from dataportal.utils.constants import (
    GENE_ESSENTIALITY,
    DEFAULT_FACET_LIMIT,
    ES_FIELD_PFAM, ES_FIELD_INTERPRO,
    ES_FIELD_KEGG, ES_FIELD_COG_ID,
    ES_FIELD_ISOLATE_NAME,
    ES_FIELD_SPECIES_ACRONYM, ES_FIELD_COG_FUNCATS, ES_FIELD_AMR_INFO,
)

logger = logging.getLogger(__name__)


class GeneFacetedSearch(FacetedSearch):
    fields = [ES_FIELD_SPECIES_ACRONYM, GENE_ESSENTIALITY, ES_FIELD_COG_ID,
              ES_FIELD_KEGG, 'go_term', ES_FIELD_PFAM, ES_FIELD_INTERPRO, ES_FIELD_ISOLATE_NAME,
              ES_FIELD_COG_FUNCATS]

    def __init__(self, query='', filters=None, species_acronym=None, essentiality=None,
                 isolates=None, cog_id=None, cog_funcats=None, kegg=None, go_term=None, pfam=None, interpro=None,
                 has_amr_info=None, limit: int = DEFAULT_FACET_LIMIT, operators=None):
        self.species_acronym = species_acronym
        self.essentiality = essentiality
        self.isolates = isolates
        self.cog_id = cog_id
        self.cog_funcats = cog_funcats
        self.kegg = kegg
        self.go_term = go_term
        self.pfam = pfam
        self.interpro = interpro
        self.has_amr_info = has_amr_info
        self.operators = operators or {}

        self.facets = {
            GENE_ESSENTIALITY: TermsFacet(field=GENE_ESSENTIALITY, size=limit),
            ES_FIELD_PFAM: TermsFacet(field=ES_FIELD_PFAM, size=limit),
            ES_FIELD_INTERPRO: TermsFacet(field=ES_FIELD_INTERPRO, size=limit),
            ES_FIELD_KEGG: TermsFacet(field=ES_FIELD_KEGG, size=limit),
            ES_FIELD_COG_ID: TermsFacet(field=ES_FIELD_COG_ID, size=limit),
            ES_FIELD_COG_FUNCATS: TermsFacet(field=ES_FIELD_COG_FUNCATS, size=limit),
            ES_FIELD_AMR_INFO: TermsFacet(field=ES_FIELD_AMR_INFO, size=2),
        }

        super().__init__(query=query, filters=filters or {})

    def build_search(self):
        # Build the search
        self._hits_search = self._build_filtered_search()

        # Build a custom search per facet for aggregation
        self._facet_searches = {}
        for facet_field in self.facets:
            if self.operators.get(facet_field, "OR").upper() == "OR":
                self._facet_searches[facet_field] = self._build_filtered_search(skip_field=facet_field)
            else:
                self._facet_searches[facet_field] = self._hits_search

        return self._hits_search

    def _build_filtered_search(self, skip_field=None):
        s = super().build_search()

        # Attach facets
        if skip_field:
            if skip_field in self.facets:
                s.aggs.bucket(skip_field, self.facets[skip_field].get_aggregation())
        else:
            for facet_name, facet in self.facets.items():
                s.aggs.bucket(facet_name, facet.get_aggregation())

        # Core filters
        if self.species_acronym:
            s = s.filter("term", species_acronym=self.species_acronym)
        if self.essentiality:
            s = s.filter("terms", essentiality=[self.essentiality])
        if self.has_amr_info is not None:
            s = s.filter("term", has_amr_info=self.has_amr_info)
        if self.isolates:
            s = s.filter("terms", isolate_name=self.isolates)

        # Functional filters
        for field_name in [
            "pfam", "interpro", "cog_id", "cog_funcats", "kegg", "go_term"
        ]:
            if field_name == skip_field:
                continue

            values = self._get_cleaned_values(field_name)
            if not values:
                continue

            operator = self.operators.get(field_name, "OR").upper()
            if operator == "AND":
                for val in values:
                    s = s.filter("term", **{field_name: val})
            else:
                s = s.filter("terms", **{field_name: values})

        return s

    def _get_cleaned_values(self, field_name):
        val = getattr(self, field_name)
        if not val:
            return None
        if field_name in ["kegg", "go_term"]:
            return [v.lower() for v in val] if isinstance(val, list) else [val.lower()]
        return val if isinstance(val, list) else [val]

    def get_facet_search(self, facet_field):
        return self._facet_searches.get(facet_field, self._hits_search)
