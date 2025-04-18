import {GenomeMeta} from "../../../../interfaces/Genome";

const getAssembly = (genomeMeta: GenomeMeta, fastaBaseUrl: string) => ({
    name: genomeMeta.assembly_name,
    sequence: {
        type: 'ReferenceSequenceTrack',
        trackId: 'reference',
        adapter: {
            type: 'BgzipFastaAdapter',
            sequences: genomeMeta.contigs.map(contig => ({
                name: contig.seq_id,
                length: contig.length,
            })),
            fastaLocation: {
                uri: `${fastaBaseUrl}/${genomeMeta.assembly_name}/${genomeMeta.fasta_file}.gz`,
            },
            faiLocation: {
                uri: `${fastaBaseUrl}/${genomeMeta.assembly_name}/${genomeMeta.fasta_file}.gz.fai`,
            },
            gziLocation: {
                uri: `${fastaBaseUrl}/${genomeMeta.assembly_name}/${genomeMeta.fasta_file}.gz.gzi`,
            },
        }
    },
});

export default getAssembly;
