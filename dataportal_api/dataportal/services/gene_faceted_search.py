from elasticsearch_dsl import FacetedSearch, TermsFacet


class GeneFacetedSearch(FacetedSearch):
    index = 'gene_index'
    fields = ['species_acronym', 'essentiality', 'cog_funcats', 'kegg', 'go_term', 'pfam', 'interpro', 'isolate_name']

    def __init__(self, query='', filters=None, species_acronym=None, essentiality=None,
                 isolates=None, cog_funcat=None, kegg=None, go_term=None, pfam=None, interpro=None,
                 limit: int = 20):
        # Just store values
        self.species_acronym = species_acronym
        self.essentiality = essentiality
        self.isolates = isolates
        self.cog_funcat = cog_funcat
        self.kegg = kegg
        self.go_term = go_term
        self.pfam = pfam
        self.interpro = interpro

        self.facets = {
            'pfam': TermsFacet(field='pfam', size=limit),
            'interpro': TermsFacet(field='interpro', size=limit),
            'essentiality': TermsFacet(field='essentiality', size=limit)
        }

        # Now call super safely (this will call build_search)
        super().__init__(query=query, filters=filters or {})

    def build_search(self):
        s = super().build_search()

        if self.species_acronym:
            s = s.filter('term', species_acronym=self.species_acronym)
        if self.essentiality:
            s = s.filter('term', essentiality=self.essentiality.lower())
        if self.cog_funcat:
            s = s.filter('term', cog_funcats=self.cog_funcat.lower())
        if self.kegg:
            s = s.filter('prefix', kegg=self.kegg.lower())
        if self.go_term:
            s = s.filter('prefix', go_term=self.go_term.lower())
        if self.pfam:
            s = s.filter('prefix', pfam=self.pfam.lower())
        if self.interpro:
            s = s.filter('prefix', interpro=self.interpro.lower())
        if self.isolates:
            s = s.filter('terms', isolate_name=self.isolates)

        return s
