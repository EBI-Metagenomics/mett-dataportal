import {GenomeMeta} from '../../pages/GeneViewerPage';

const getAssembly = (isolateData: GenomeMeta) => ({
    name: isolateData.isolate_name,
    sequence: {
        type: 'ReferenceSequenceTrack',
        trackId: 'reference',
        adapter: {
            type: 'IndexedFastaAdapter',
            fastaLocation: {
                // uri: isolateData.fasta_file,
                uri: 'http://localhost:3000/BU_2243B_NT5389.1.fa',
            },
            faiLocation: {
                uri: 'http://localhost:3000/BU_2243B_NT5389.1.fa.fai',
            },
        },
    },
});

export default getAssembly;

