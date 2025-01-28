import {AutocompleteResponse, GenomeMeta, GenomeResponse} from "../interfaces/Genome";
import {Species} from "../interfaces/Species";

export function transformSpecies(rawSpecies: any): Species {
    return {
        id: rawSpecies.id,
        scientific_name: rawSpecies.scientific_name,
        common_name: rawSpecies.common_name,
        acronym: rawSpecies.acronym,
    };
}

export function transformGenomeMeta(rawGenome: any): GenomeMeta {
    return {
        species: transformSpecies(rawGenome.species),
        id: rawGenome.id,
        isolate_name: rawGenome.isolate_name,
        assembly_name: rawGenome.assembly_name,
        assembly_accession: rawGenome.assembly_accession,
        fasta_file: rawGenome.fasta_file,
        gff_file: rawGenome.gff_file,
        fasta_url: rawGenome.fasta_url,
        gff_url: rawGenome.gff_url,
        type_strain: rawGenome.type_strain,
        contigs: rawGenome.contigs.map((contig: any) => ({
            seq_id: contig.seq_id,
            length: contig.length,
        })),
    };
}

export function transformGenomeResponse(rawResponse: any): GenomeResponse {
    return {
        results: rawResponse.results.map(transformGenomeMeta),
        page_number: rawResponse.page_number,
        num_pages: rawResponse.num_pages,
        has_previous: rawResponse.has_previous,
        has_next: rawResponse.has_next,
        total_results: rawResponse.total_results,
    };
}

export function transformAutocompleteResponse(rawResponse: any[]): AutocompleteResponse[] {
    return rawResponse.map((item) => ({
        id: item.id,
        isolate_name: item.isolate_name,
        assembly_name: item.assembly_name,
    }));
}
