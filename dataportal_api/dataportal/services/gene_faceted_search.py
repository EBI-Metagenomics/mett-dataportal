import logging

from elasticsearch_dsl import FacetedSearch, TermsFacet

from dataportal.utils.constants import (
    GENE_ESSENTIALITY,
    DEFAULT_FACET_LIMIT,
    ES_FIELD_PFAM,
    ES_FIELD_INTERPRO,
    ES_FIELD_KEGG,
    ES_FIELD_COG_ID,
    ES_FIELD_ISOLATE_NAME,
    ES_FIELD_SPECIES_ACRONYM,
    ES_FIELD_COG_FUNCATS,
    ES_FIELD_AMR_INFO,
)

logger = logging.getLogger(__name__)


class GeneFacetedSearch(FacetedSearch):
    fields = [
        ES_FIELD_SPECIES_ACRONYM,
        GENE_ESSENTIALITY,
        ES_FIELD_COG_ID,
        ES_FIELD_KEGG,
        "go_term",
        ES_FIELD_PFAM,
        ES_FIELD_INTERPRO,
        ES_FIELD_ISOLATE_NAME,
        ES_FIELD_COG_FUNCATS,
    ]

    def __init__(
        self,
        query="",
        filters=None,
        species_acronym=None,
        essentiality=None,
        isolates=None,
        cog_id=None,
        cog_funcats=None,
        kegg=None,
        go_term=None,
        pfam=None,
        interpro=None,
        has_amr_info=None,
        limit: int = DEFAULT_FACET_LIMIT,
        operators=None,
    ):
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
        s = super().build_search()

        if self.species_acronym:
            s = s.filter("term", species_acronym=self.species_acronym)
        if self.essentiality:
            s = s.filter("terms", essentiality=[self.essentiality])
        if self.has_amr_info is not None:
            s = s.filter("term", has_amr_info=self.has_amr_info)
        if self.isolates and isinstance(self.isolates, list) and any(self.isolates):
            s = s.filter("terms", isolate_name=self.isolates)

        if self.pfam:
            s = self._apply_filter(s, "pfam", self.pfam)
        if self.interpro:
            s = self._apply_filter(s, "interpro", self.interpro)
        if self.cog_id:
            s = self._apply_filter(s, "cog_id", self.cog_id)
        if self.cog_funcats:
            s = self._apply_filter(s, "cog_funcats", self.cog_funcats)
        if self.kegg:
            kegg_values = [
                k.lower()
                for k in (self.kegg if isinstance(self.kegg, list) else [self.kegg])
            ]
            s = self._apply_filter(s, "kegg", kegg_values)
        if self.go_term:
            go_values = [
                g.lower()
                for g in (
                    self.go_term if isinstance(self.go_term, list) else [self.go_term]
                )
            ]
            s = self._apply_filter(s, "go_term", go_values)

        # logger.info(f"Final Elasticsearch Query: {json.dumps(s.to_dict(), indent=2)}")
        return s

    def _apply_filter(self, search_obj, field_name, values):
        operator = (self.operators.get(field_name) or "OR").upper()
        if not values:
            return search_obj
        if operator == "AND":
            for val in values:
                search_obj = search_obj.filter("term", **{field_name: val})
        else:
            search_obj = search_obj.filter("terms", **{field_name: values})
        return search_obj
