from elasticsearch_dsl import (
    Document,
    Text,
    Keyword,
    Integer,
    Boolean,
    analyzer,
    tokenizer,
    Nested,
    normalizer,
    Float, Long, ScaledFloat,
)

edge_ngram_tokenizer = tokenizer(
    "edge_ngram_tokenizer",
    type="edge_ngram",
    min_gram=1,
    max_gram=20,
    token_chars=["letter", "digit", "connector_punctuation"],
)

autocomplete_analyzer = analyzer(
    "autocomplete_analyzer", tokenizer=edge_ngram_tokenizer, filter=["lowercase"]
)

lowercase_normalizer = normalizer(
    "lowercase_normalizer", type="custom", filter=["lowercase"]
)


def canonical_pair(a: str, b: str) -> tuple[str, str]:
    """Return a,b sorted to ensure undirected symmetry."""
    return tuple(sorted([a, b]))

def build_pair_id(species_acronym: str, a: str, b: str) -> str:
    """Stable unique id for the interaction doc."""
    aa, bb = canonical_pair(a, b)
    # Use double-underscore to match your CSV pattern
    return f"{species_acronym}:{aa}__{bb}"



class SpeciesDocument(Document):
    scientific_name = Text(fields={"keyword": Keyword()})
    common_name = Text()
    acronym = Keyword()
    taxonomy_id = Integer()

    class Index:
        name = "species_index"

    def save(self, **kwargs):
        """set `_id` as `acronym`"""
        self.meta.id = self.acronym
        return super().save(**kwargs)


class StrainDocument(Document):
    strain_id = Keyword()

    species_scientific_name = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    species_acronym = Keyword(normalizer=lowercase_normalizer)

    isolate_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword(normalizer=lowercase_normalizer)},
    )
    isolate_key = Keyword()  # data cleanup resolver attribute

    assembly_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    assembly_accession = Keyword()

    fasta_file = Keyword()
    gff_file = Keyword()  # Nullable
    type_strain = Boolean()

    # Rollups for UI / sorting
    contig_count = Integer()
    genome_size = Long()

    # Contigs
    contigs = Nested(properties={
        "seq_id": Keyword(),
        "length": Integer()
    })

    # ---- Drug MIC (growth inhibition / MIC-like) ----
    drug_mic = Nested(properties={
        # drug metadata (all optional)
        "drug_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "drug_class": Keyword(normalizer=lowercase_normalizer),
        "drug_subclass": Keyword(normalizer=lowercase_normalizer),
        "compound_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "pubchem_id": Keyword(),

        # measurements
        "relation": Keyword(),  # '=', '>', '<=', etc.
        "mic_value": ScaledFloat(scaling_factor=1000),  # 0.001 precision (e.g., µM or mg/L)
        "unit": Keyword(),  # 'uM', 'mg/L'

        # experimental context (if/when available)
        "experimental_condition_id": Integer(),
        "experimental_condition_name": Keyword(normalizer=lowercase_normalizer)
    })

    # ---- Drug Metabolism ----
    drug_metabolism = Nested(properties={
        # drug metadata (all optional)
        "drug_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "drug_class": Keyword(normalizer=lowercase_normalizer),
        "drug_subclass": Keyword(normalizer=lowercase_normalizer),
        "compound_name": Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)}),
        "pubchem_id": Keyword(),

        # measurements
        "degr_percent": ScaledFloat(scaling_factor=10000),  # 0.0001 precision
        "pval": ScaledFloat(scaling_factor=1000000),
        "fdr": ScaledFloat(scaling_factor=1000000),
        "metabolizer_classification": Keyword(normalizer=lowercase_normalizer),

        # convenience flags for filtering
        "is_significant": Boolean(),  # e.g., fdr < 0.05

        # experimental context (optional)
        "experimental_condition_id": Integer(),
        "experimental_condition_name": Keyword(normalizer=lowercase_normalizer)
    })

    class Index:
        name = "strain_index"
        settings = {
            "analysis": {
                "analyzer": {"autocomplete_analyzer": autocomplete_analyzer},
                "tokenizer": {"edge_ngram_tokenizer": edge_ngram_tokenizer},
                "normalizer": {"lowercase_normalizer": lowercase_normalizer},
            }
        }

    def save(self, **kwargs):
        """set `_id` as `isolate_name`"""
        self.meta.id = self.isolate_name
        return super().save(**kwargs)


class FeatureDocument(Document):
    # ---- Identity ----
    feature_id = Keyword()                                 # gene: locus_tag; IG: "IG-between-...-and-..."
    feature_type = Keyword(normalizer=lowercase_normalizer) # 'gene' | 'IG' | others
    element = Keyword(normalizer=lowercase_normalizer)      # gene, intergenic, ncRNA, ...

    # For genes (convenience/compatibility)
    locus_tag = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )                                 # still stored for genes
    uniprot_id = Keyword()

    # IG context (only meaningful when feature_type == 'IG')
    ig_locus_tag_a = Keyword()
    ig_locus_tag_b = Keyword()
    strand = Keyword()

    # Genomic coordinates (region-level; for genes or IGs)
    seq_id = Text(analyzer=autocomplete_analyzer,
                  search_analyzer="standard",
                  fields={"keyword": Keyword()})
    start = Integer()
    end = Integer()

    gene_name = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    alias = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )

    product = Text(
        analyzer=autocomplete_analyzer,
        search_analyzer="standard",
        fields={"keyword": Keyword()},
    )
    product_source = Text(fields={"keyword": Keyword()})

    species_scientific_name = Keyword()
    species_acronym = Keyword(normalizer=lowercase_normalizer)
    isolate_name = Keyword()


    # ---- Functional annotations (existing) ----
    cog_id = Keyword(multi=True)
    cog_funcats = Keyword(multi=True)
    kegg = Keyword(multi=True, normalizer=lowercase_normalizer)
    pfam = Keyword(multi=True, normalizer=lowercase_normalizer)
    eggnog = Text(fields={"keyword": Keyword(normalizer=lowercase_normalizer)})
    interpro = Keyword(multi=True, normalizer=lowercase_normalizer)
    has_amr_info = Boolean()
    uf_ontology_terms = Keyword(multi=True)
    uf_prot_rec_fullname = Text(fields={"keyword": Keyword()})

    dbxref = Nested(properties={"db": Keyword(), "ref": Keyword()})

    ec_number = Keyword()

    essentiality = Keyword(normalizer=lowercase_normalizer)  # legacy single-value (kept for backward compatibility)
    inference = Text(fields={"keyword": Keyword()})

    ontology_terms = Nested(
        properties={
            "ontology_type": Keyword(),
            "ontology_id": Keyword(),
            "ontology_description": Text(fields={"keyword": Keyword(ignore_above=256)}),
        }
    )

    amr = Nested(
        properties={
            "gene_symbol": Keyword(),
            "sequence_name": Text(fields={"keyword": Keyword()}),
            "scope": Keyword(),
            "element_type": Keyword(),
            "element_subtype": Keyword(),
            "drug_class": Keyword(),
            "drug_subclass": Keyword(),
            "uf_keyword": Keyword(multi=True),
            "uf_ecnumber": Keyword(),
        }
    )

    # ---- ESSENTIALITY (new, structured) ----
    # matches your CSV: TnSeq/TAs metrics + call + condition
    essentiality_data = Nested(
        properties={
            "experimental_condition": Keyword(),       # e.g. mGAM_undefined_rich_media
            "TAs_in_locus": Integer(),
            "TAs_hit": Float(),                        # fraction 0..1
            "essentiality_call": Keyword(              # essential, not_essential, essential_solid, essential_liquid, not_classified, unclear
                normalizer=lowercase_normalizer
            ),
        }
    )

    # quick-existence flags
    has_proteomics = Boolean()
    has_fitness = Boolean()
    has_mutant_growth = Boolean()
    has_reactions = Boolean()

    # ---- PROTEIN ↔ COMPOUND interactions (new) ----
    protein_compound = Nested(
        properties={
            "compound": Keyword(),
            "ttp_score": Float(),
            "fdr": Float(),
            "hit_calling": Boolean(),
            "experimental_condition": Keyword(),
        }
    )

    # ---- GENE FITNESS (new, structured) ----
    # You already had a simpler fitness_data; we supersede/extend it here
    fitness = Nested(
        properties={
            "experimental_condition": Keyword(),
            "media": Keyword(),
            "contrast": Keyword(),
            "lfc": Float(),
            "fdr": Float()
        }
    )

    # ---- REACTIONS / GPR / METABOLITES (new) ----
    # 1) direct gene→reaction links (many)
    reactions = Keyword(multi=True)                    # e.g. ["ASPTA","CPPPGO",...]
    # 2) per-reaction details + GPR and metabolite edges
    reaction_details = Nested(
        properties={
            "reaction": Keyword(),
            "gpr": Text(fields={"keyword": Keyword()}),  # e.g. "BU_... or BU_..."
            # reaction graph edges (optional but useful for UI filters)
            "substrates": Keyword(multi=True),
            "products": Keyword(multi=True),
            # convenience fields for searching metabolite involvement
            "metabolites": Keyword(multi=True),
        }
    )

    # ---- MUTANT GROWTH (new) ----
    mutant_growth = Nested(
        properties={
            "media": Keyword(),
            "experimental_condition": Keyword(),
            "replicate": Integer(),
            "tas_hit": Float(),                         # 0..1
            "doubling_rate_h": Float(),
        }
    )

    # ---- PROTEOMICS (new) ----
    proteomics = Nested(
        properties={
            "coverage": Float(),
            "unique_peptides": Integer(),
            "unique_intensity": Float(),
            "evidence": Boolean(),
        }
    )

    # ---- Sequences (existing) ----
    protein_sequence = Text(fields={"keyword": Keyword()})  # only for 'gene'

    class Index:
        name = "feature_index"
        settings = {
            "index": {"max_result_window": 500000},
            "analysis": {
                "analyzer": {"autocomplete_analyzer": autocomplete_analyzer},
                "tokenizer": {"edge_ngram_tokenizer": edge_ngram_tokenizer},
                "normalizer": {"lowercase_normalizer": lowercase_normalizer},
            },
        }
        dynamic = "true"

    def save(self, **kwargs):
        if not getattr(self, "feature_id", None):
            # fall back for genes
            self.feature_id = getattr(self, "locus_tag", None)
        self.meta.id = self.feature_id
        return super().save(**kwargs)



class ProteinProteinDocument(Document):
    # ---- Identity / keys ----
    species_scientific_name = Keyword()                         # e.g., "Bacteroides uniformis"
    species_acronym = Keyword(normalizer=lowercase_normalizer)  # e.g., "BU"
    # Optional isolate, if/when you scope PPIs more granularly
    isolate_name = Keyword()                                    # nullable

    # Participants (undirected)
    protein_a = Keyword()
    protein_b = Keyword()
    participants = Keyword(multi=True)      # [protein_a, protein_b] (order does not matter)
    participants_sorted = Keyword(multi=True)  # [min(a,b), max(a,b)] for symmetric queries
    pair_id = Keyword()                     # "{species}:{min}__{max}" – set as _id
    is_self_interaction = Boolean()         # convenience flag when a == b

    # ---- Scores / evidence (ScaledFloat keeps storage compact & sortable) ----
    # Use scaling_factor=1e6 to preserve up to ~6 decimal places and allow negatives.
    dl_score             = ScaledFloat(scaling_factor=1_000_000)     # "ds_score" in CSV?
    comelt_score         = ScaledFloat(scaling_factor=1_000_000)     # "melt_score" / "comelt" variants
    perturbation_score   = ScaledFloat(scaling_factor=1_000_000)     # "perturb_score"
    abundance_score      = ScaledFloat(scaling_factor=1_000_000)     # "gp_score" (global proteomics)
    melt_score           = ScaledFloat(scaling_factor=1_000_000)     # "melt_score" (if distinct)
    secondary_score      = ScaledFloat(scaling_factor=1_000_000)     # "sec_score"
    bayesian_score       = ScaledFloat(scaling_factor=1_000_000)     # "bn_score"
    string_score         = ScaledFloat(scaling_factor=1_000_000)     # "string_physical_score"
    operon_score         = ScaledFloat(scaling_factor=1_000_000)
    ecocyc_score         = ScaledFloat(scaling_factor=1_000_000)
    tt_score             = ScaledFloat(scaling_factor=1_000_000)     # "tt_score" in CSV
    ds_score             = ScaledFloat(scaling_factor=1_000_000)     # "ds_score" in CSV (keep both if needed)

    # ---- Experimental context ----
    experimental_condition_id = Integer()       # from SP2_ppi_interaction
    experimental_condition    = Keyword()       # optional human-friendly label

    # ---- XL-MS & external evidence ----
    xlms_peptides = Text()                      # free text list from CSV / DB
    xlms_files    = Keyword(multi=True)         # split on delimiters into array if possible

    # Quick evidence flags for filtering
    has_xlms      = Boolean()
    has_string    = Boolean()
    has_operon    = Boolean()
    has_ecocyc    = Boolean()
    has_experimental = Boolean()                # e.g., co-melt/perturb present

    # Optional rollups for UI
    evidence_count = Integer()                  # how many sources contributed (non-null scores)
    confidence_bin = Keyword(normalizer=lowercase_normalizer)  # "high" | "medium" | "low" (set at ingest)

    class Index:
        name = "ppi_index"
        settings = {
            "index": {"max_result_window": 500000},
            "analysis": {
                "analyzer": {"autocomplete_analyzer": autocomplete_analyzer},
                "tokenizer": {"edge_ngram_tokenizer": edge_ngram_tokenizer},
                "normalizer": {"lowercase_normalizer": lowercase_normalizer},
            },
        }
        dynamic = "true"

    def save(self, **kwargs):
        # Enforce canonical undirected identity before saving
        aa, bb = canonical_pair(self.protein_a, self.protein_b)
        self.participants = [self.protein_a, self.protein_b]
        self.participants_sorted = [aa, bb]
        self.is_self_interaction = (aa == bb)

        # Build id; species_acronym should be present (fallback to scientific name if needed)
        species_key = getattr(self, "species_acronym", None) or getattr(self, "species_scientific_name", "na")
        self.pair_id = build_pair_id(species_key, aa, bb)
        self.meta.id = self.pair_id

        # Convenience flags
        self.has_xlms = bool(self.xlms_peptides or self.xlms_files)
        self.has_string = self.string_score is not None
        self.has_operon = self.operon_score is not None
        self.has_ecocyc = self.ecocyc_score is not None
        self.has_experimental = any(
            s is not None for s in [
                self.comelt_score, self.perturbation_score, self.abundance_score, self.melt_score,
                self.secondary_score, self.bayesian_score, self.tt_score, self.ds_score
            ]
        )

        # Rollup counts & bins
        numeric_scores = [
            self.dl_score, self.comelt_score, self.perturbation_score, self.abundance_score,
            self.melt_score, self.secondary_score, self.bayesian_score, self.string_score,
            self.operon_score, self.ecocyc_score, self.tt_score, self.ds_score
        ]
        self.evidence_count = sum(1 for v in numeric_scores if v is not None)

        # Example binning heuristic (adjust during ingest as you learn ranges)
        if (self.string_score and self.string_score >= 0.7) or self.evidence_count >= 4:
            self.confidence_bin = "high"
        elif (self.string_score and self.string_score >= 0.4) or self.evidence_count >= 2:
            self.confidence_bin = "medium"
        else:
            self.confidence_bin = "low"

        return super().save(**kwargs)


class OperonDocument(Document):
    operon_id = Keyword(required=True)
    isolate_name = Keyword()
    species_acronym = Keyword()
    species_scientific_name = Keyword()

    # composition
    genes = Keyword(multi=True)
    gene_count = Integer()

    # rollups
    has_tss = Boolean()
    has_terminator = Boolean()

    class Index:
        name = "operon_index"
        settings = {"index": {"max_result_window": 500_000}}

class OrthologDocument(Document):
    # identity: order-insensitive pair-id
    pair_id = Keyword()               # "BU_61_00001__BU_909_00001"
    doc_type = Keyword()              # 'pair'
    # genes
    gene_a = Keyword()
    gene_b = Keyword()
    # attrs
    orthology_type = Keyword()
    oma_group = Keyword()
    # convenience members array
    members = Keyword(multi=True)

    class Index:
        name = "ortholog_index"
        settings = {"index": {"max_result_window": 500000}}
