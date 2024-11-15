import {GenomeMeta} from "@components/interfaces/Genome";

const getAssembly = (genomeMeta: GenomeMeta, fastaBaseUrl: string) => ({
    name: genomeMeta.assembly_name,
    sequence: {
        type: 'ReferenceSequenceTrack',
        trackId: 'reference',
        adapter: {
            type: 'BgzipFastaAdapter',
            fastaLocation: {
                uri: `${fastaBaseUrl}/${genomeMeta.fasta_file}.gz`,
            },
            faiLocation: {
                uri: `${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.fai`,
            },
            gziLocation: {
                uri: `${fastaBaseUrl}/${genomeMeta.fasta_file}.gz.gzi`,
            },
        },
    },
});

export default getAssembly;
