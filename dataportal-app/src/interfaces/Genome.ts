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
    current_annotation_run_id?: string | null;
    current_annotation_release?: string | null;
    annotation_doc_link?: string | null;
    mettannotator_version?: string | null;
    pipeline_version?: string | null;
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

export interface AnnotationRun {
    id: number;
    isolate_name: string;
    strain_id?: string | null;
    release_label: string;
    is_current: boolean;
    status: string;
    mettannotator_version?: string | null;
    pipeline_version?: string | null;
    doc_link?: string | null;
    comments?: string | null;
    processed_at?: string | null;
    created_at?: string | null;
    es_feature_index?: string | null;
    gff_file?: string | null;
    gff_url?: string | null;
}

export interface GenomeAnnotationsResponse {
    isolate_name: string;
    current: AnnotationRun | null;
    previous: AnnotationRun[];
    runs: AnnotationRun[];
}

export interface GenomeMinIntf {
    isolate_name: string;
    assembly_name: string;
}

// New standardized response types
export type GenomeApiResponse = SuccessApiResponse<GenomeMeta>;
export type GenomeListResponse = PaginatedApiResponse<GenomeMeta>;
export type AutocompleteApiResponse = SuccessApiResponse<AutocompleteResponse[]>;

