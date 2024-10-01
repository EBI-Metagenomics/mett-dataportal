import {GenomeMeta} from '../../pages/GeneViewerPage';

const getAssembly = (genomeMeta: GenomeMeta) => ({
    name: genomeMeta.isolate_name,
    sequence: {
        type: 'ReferenceSequenceTrack',
        trackId: 'reference',
        adapter: {
            type: 'BgzipFastaAdapter',
            fastaLocation: {
                uri: `${genomeMeta.fasta_url}.gz`,
            },
            faiLocation: {
                uri: `${genomeMeta.fasta_url}.gz.fai`,
            },
            gziLocation: {
                uri: `${genomeMeta.fasta_url}.gz.gzi`,
            },
        },
    },
});

export default getAssembly;

