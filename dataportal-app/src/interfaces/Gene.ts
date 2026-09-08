import {FacetItem} from "./Auxiliary";
import {PaginatedApiResponse, SuccessApiResponse} from "./ApiResponse";

export interface GeneUnifireAnnotations {
    gene_name?: string | null;
    gene_name_synonym?: string | null;
    keywords?: string[] | null;
    ontology_terms?: string[] | null;
    protein_fullname?: string | null;
    protein_shortname?: string | null;
    protein_ec_number?: string | null;
    alt_protein_fullname?: string | null;
    alt_protein_shortname?: string | null;
    alt_ec_number?: string | null;
    chebi?: string[] | null;
    pirsr_cofactor?: string | null;
}

export interface GeneDbcanAnnotations {
    prot_type?: string | null;
    prot_family?: string[] | null;
    substrate_pul?: string | null;
    substrate_sub?: string | null;
}

export interface GeneBgcAnnotations {
    gecco_bgc_type?: string | null;
    nearest_mibig?: string | null;
    nearest_mibig_class?: string | null;
    antismash_bgc_function?: string | null;
}

export interface GeneMobilomeAnnotations {
    mge_id?: string | null;
    mge_types?: string[] | null;
}

export interface GeneDefenseAnnotations {
    finder_type?: string | null;
    finder_subtype?: string | null;
}

export interface GeneMetadataAnnotations {
    extra_copy_number?: number | null;
    note?: string | null;
}

export interface GeneMeta {
    locus_tag?: string;
    gene_name?: string;
    alias?: string[];
    product?: string;
    product_source?: string;
    inference?: string | null;
    start_position?: number;
    end_position?: number;
    seq_id: string;
    isolate_name: string;
    species_scientific_name: string;
    species_acronym: string;
    uniprot_id?: string | null;
    essentiality?: string;
    cog_funcats?: string[] | null;
    cog_id?: string[] | null;
    kegg?: string[] | null;
    pfam?: string[] | null;
    interpro?: string[] | null;
    eggnog?: string | null;
    ec_number?: string | null;
    ontology_terms?: {
        ontology_type?: string;
        ontology_id?: string;
        ontology_description?: string;
    }[] | null;
    uf_ontology_terms?: string[] | null;
    uf_prot_rec_fullname?: string | null;
    uf_keyword?: string[] | null;
    uf_gene_name?: string | null;
    dbxref?: { db: string; ref: string }[] | null;
    amr?: AMR[] | null;
    has_amr_info?: boolean | null;
    has_proteomics?: boolean | null;
    has_fitness?: boolean | null;
    has_mutant_growth?: boolean | null;
    has_reactions?: boolean | null;
    feature_type?: string;
    ig_locus_tag_a?: string | null;
    ig_locus_tag_b?: string | null;
    flanking_locus_tags?: string[] | null;
    annotation_run_id?: string | null;
    annotation_release?: string | null;
    unifire?: GeneUnifireAnnotations | null;
    dbcan?: GeneDbcanAnnotations | null;
    bgc?: GeneBgcAnnotations | null;
    mobilome?: GeneMobilomeAnnotations | null;
    defense?: GeneDefenseAnnotations | null;
    metadata?: GeneMetadataAnnotations | null;
}

export interface AMR {
    gene_symbol?: string;
    sequence_name?: string;
    scope?: string;
    element_type?: string;
    element_subtype?: string;
    drug_class?: string | null;
    drug_subclass?: string | null;
    uf_keyword?: string[] | null;
    uf_ecnumber?: string | null;
}

export interface Gene {
    locus_tag?: string;
    gene_name?: string;
    alias?: string[];
    product?: string;
}


export interface GeneProteinSeq {
    locus_tag?: string;
    protein_sequence?: string;
}

export interface GeneSuggestion {
    gene_name: string | '';
    locus_tag: string;
    alias: string[] | '';
    isolate_name?: string;
    uniprot_id?: string | null;
    species_scientific_name?: string;
    species_acronym?: string;
    product?: string | null;
    kegg?: string[] | null;
    pfam?: string[] | null;
    interpro?: string[] | null;
    cog_id?: string[] | null;
}

// Legacy pagination interface (for backward compatibility)
export interface PaginatedResponse<T> {
    results: T[];
    num_pages: number;
    page_number: number;
    has_previous: boolean;
    has_next: boolean;
}

// New standardized response types
export type GeneResponse = SuccessApiResponse<GeneMeta>;
export type GeneListResponse = PaginatedApiResponse<GeneMeta>;
export type GeneSuggestionResponse = SuccessApiResponse<GeneSuggestion[]>;
export type GeneProteinSeqResponse = SuccessApiResponse<GeneProteinSeq>;

export interface GeneFacetResponse {
    total_hits: number;
    operators: Record<string, 'AND' | 'OR'>;

    [facetGroup: string]: FacetItem[] | number | Record<string, 'AND' | 'OR'>;
}

// New standardized facet response
export type GeneFacetApiResponse = SuccessApiResponse<GeneFacetResponse>;
