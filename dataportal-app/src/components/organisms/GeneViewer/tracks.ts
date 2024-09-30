import {GenomeMeta} from '../../pages/GeneViewerPage';

const getTracks = (isolateData: GenomeMeta) => [
    {
        type: 'FeatureTrack',
        trackId: 'structural_annotation',
        name: 'Structural Annotation',
        assemblyNames: ['b_uniformis'],
        category: ['Annotations'],
        platform: 'jbrowse',
        adapter: {
            type: 'Gff3TabixAdapter',
            gffGzLocation: {
                // uri: isolateData.gff_file,
                uri: 'http://localhost:3000/BU_2243B_annotations_sorted.gff.gz',
            },
            index: {
                location: {
                    uri: 'http://localhost:3000/BU_2243B_annotations_sorted.gff.gz.tbi',
                },
            },
        },
        textSearching: {
            textSearchAdapter: {
                type: 'TrixTextSearchAdapter',
                textSearchAdapterId: 'gff3tabix_genes-index',
                ixFilePath: {
                    uri: 'http://localhost:3000/BU_2243B_annotations_sorted.ix',
                },
                ixxFilePath: {
                    uri: 'http://localhost:3000/BU_2243B_annotations_sorted.ixx',
                },
                metaFilePath: {
                    uri: 'http://localhost:3000/BU_2243B_annotations_sorted.gff.gz.meta.json',
                },
                assemblyNames: ['b_uniformis'],
            },
        },
    },
];

export default getTracks;
