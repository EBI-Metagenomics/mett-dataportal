import {Species} from "./Species";

export interface Contig {
    seq_id: string;
    length: number;
}

export interface GenomeMeta {
    id: number;
    species: Species;
    isolate_name: string;
    assembly_name: string;
    assembly_accession: string | null;
    fasta_file: string;
    gff_file: string;
    fasta_url: string;
    gff_url: string;
    type_strain: boolean;
    contigs: Contig[];
}

export interface BaseGenome {
    id: number;
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
    id: number,
    isolate_name: string,
    assembly_name: string
}

export interface GenomeMinIntf {
    id: number,
    isolate_name: string,
    assembly_name: string
}

