import {FacetItem} from "./Auxiliary";

export interface GeneMeta {
    locus_tag?: string;
    gene_name?: string;
    alias?: string[];
    product?: string;
    start_position?: number;
    end_position?: number;
    seq_id: string;
    isolate_name: string;
    uniprot_id?: string | null;
    essentiality?: string;
    cog_funcats?: string[] | null;
    cog_id?: string | null;
    kegg?: string[] | null;
    pfam?: string[] | null;
    interpro?: string[] | null;
    ec_number?: string | null;
    dbxref?: { db: string; ref: string }[] | null;
}

export interface Gene {
    locus_tag?: string;
    gene_name?: string;
    alias?: string[];
    product?: string;
}

export interface GeneSuggestion {
    gene_name: string | '';
    locus_tag: string;
    alias: string[] | '';
    isolate_name?: string;
    species_scientific_name?: string;
    species_acronym?: string;
    product?: string | null;
    kegg?: string[] | null;
    pfam?: string[] | null;
    interpro?: string[] | null;
    cog_id?: string | null;
}

export interface PaginatedResponse<T> {
    results: T[];
    num_pages: number;
    page_number: number;
    has_previous: boolean;
    has_next: boolean;
}

export interface GeneFacetResponse {
    [facetGroup: string]: FacetItem[] | number;
}