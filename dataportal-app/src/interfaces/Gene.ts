import {GenomeMinIntf} from "./Genome";

export interface GeneEssentiality {
    id: number;
    media: string;
    essentiality: string;
}

export interface GeneMeta {
    id: number;
    seq_id: string;
    gene_name: string;
    description: string;
    strain: GenomeMinIntf;
    locus_tag: string;
    cog: string | null;
    kegg: string | null;
    pfam: string | null;
    interpro: string | null;
    dbxref: string | null;
    ec_number: string | null;
    product: string | null;
    start_position: number | null;
    end_position: number | null;
    annotations: Record<string, any> | null;
    essentiality_data: GeneEssentiality[] | null;
}

export interface Gene {
    id: number;
    name: string;
    description: string;
}

export interface GeneSuggestion {
    gene_id: number;
    gene_name: string | '';
    isolate_name: string;
    product: string | null;
    locus_tag: string;
    kegg: string | null;
    pfam: string | null;
    interpro: string | null;
    dbxref: string | null;
}

export interface PaginatedResponse<T> {
    results: T[];
    num_pages: number;
    page_number: number;
    has_previous: boolean;
    has_next: boolean;
}

export interface GeneEssentialityTag {
    id: number;
    name: string;
    label: string;
}