import logging

from elasticsearch_dsl import A, FacetedSearch, TermsFacet, Q

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
    ES_FIELD_GO_TERM,
    GENE_SEARCH_FIELDS,
)

logger = logging.getLogger(__name__)


class GeneFacetedSearch(FacetedSearch):
    fields = GENE_SEARCH_FIELDS + [
        ES_FIELD_SPECIES_ACRONYM,
        GENE_ESSENTIALITY,
        ES_FIELD_COG_ID,
        ES_FIELD_KEGG,
        ES_FIELD_GO_TERM,
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
        limit=DEFAULT_FACET_LIMIT,
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

        must_clauses = []
        post_filter_clauses = []

        # Context filters (always applied)
        if self.species_acronym:
            must_clauses.append(Q("term", species_acronym=self.species_acronym))
        if self.has_amr_info is not None:
            must_clauses.append(Q("term", has_amr_info=self.has_amr_info))
        if self.isolates and isinstance(self.isolates, list) and any(self.isolates):
            must_clauses.append(Q("terms", isolate_name=self.isolates))
        if self.essentiality:
            must_clauses.append(Q("term", essentiality=self.essentiality))

        # Facet filters: split AND (query) vs OR (post_filter)
        facet_fields = [
            ES_FIELD_PFAM,
            ES_FIELD_INTERPRO,
            ES_FIELD_COG_ID,
            ES_FIELD_COG_FUNCATS,
            ES_FIELD_KEGG,
            ES_FIELD_GO_TERM,
        ]
        active_filters = {}
        for field in facet_fields:
            values = getattr(self, field)
            operator = (self.operators.get(field) or "OR").upper()
            if values:
                if operator == "AND":
                    for v in values:
                        must_clauses.append(Q("term", **{field: v}))
                else:
                    post_filter_clauses.append(Q("terms", **{field: values}))
                active_filters[field] = (values, operator)

        if must_clauses:
            s = s.query("bool", filter=must_clauses)

        if post_filter_clauses:
            s = s.post_filter("bool", must=post_filter_clauses)

        # Aggregations: use context + other facets excluding current facet if AND
        for facet_field, facet_def in self.facets.items():
            field_name = facet_def._params["field"]
            terms_agg = A("terms", field=field_name, size=facet_def._params["size"])

            agg_must_clauses = must_clauses.copy()
            for other_field, (values, operator) in active_filters.items():
                if other_field == facet_field:
                    if operator == "AND":
                        for v in values:
                            agg_must_clauses.append(Q("term", **{other_field: v}))
                else:
                    if operator == "AND":
                        for v in values:
                            agg_must_clauses.append(Q("term", **{other_field: v}))
                    else:
                        agg_must_clauses.append(Q("terms", **{other_field: values}))

            filtered_agg = A(
                "filter", bool={"must": [q.to_dict() for q in agg_must_clauses]}
            )
            filtered_agg.bucket(facet_field, terms_agg)
            s.aggs.bucket(f"{facet_field}_filtered", filtered_agg)

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
