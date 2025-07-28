import {PaginatedApiResponse, SuccessApiResponse} from "./ApiResponse";

export interface Contig {
    seq_id: string;
    length: number;
}

export interface GenomeMeta {
    species_scientific_name?: string;
    species_acronym: string;
    isolate_name: string;
    assembly_name: string;
    assembly_accession?: string | null;
    fasta_file: string;
    gff_file: string;
    fasta_url: string;
    gff_url: string;
    type_strain: boolean;
    contigs: Contig[];
}

export interface BaseGenome {
    isolate_name: string;
    type_strain: boolean;
}

export interface GenomeResponse {
    results: GenomeMeta[];
    page_number: number;
    num_pages: number;
    has_previous: boolean;
    has_next: boolean;
    total_results: number;
}

export interface AutocompleteResponse {
    isolate_name: string;
    assembly_name: string;
}

export interface GenomeMinIntf {
    isolate_name: string;
    assembly_name: string;
}

// New standardized response types
export type GenomeApiResponse = SuccessApiResponse<GenomeMeta>;
export type GenomeListResponse = PaginatedApiResponse<GenomeMeta>;
export type AutocompleteApiResponse = SuccessApiResponse<AutocompleteResponse[]>;

