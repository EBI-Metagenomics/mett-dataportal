import {GenomeMeta} from '../../pages/GeneViewerPage';

const getTracks = (genomeMeta: GenomeMeta) => {

    const gffBaseUrl = genomeMeta.gff_url.replace(/\/[^/]+$/, '');

    return [
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
                    uri: `${genomeMeta.gff_url}.gz`,
                },
                index: {
                    location: {
                        uri: `${genomeMeta.gff_url}.gz.tbi`,
                    },
                },
            },
            textSearching: {
                textSearchAdapter: {
                    type: 'TrixTextSearchAdapter',
                    textSearchAdapterId: 'gff3tabix_genes-index',
                    ixFilePath: {
                        uri: `${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ix`,
                    },
                    ixxFilePath: {
                        uri: `${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz.ixx`,
                    },
                    metaFilePath: {
                        uri: `${gffBaseUrl}/trix/${genomeMeta.gff_file}.gz_meta.json`,
                    },
                    assemblyNames: ['b_uniformis'],
                },
            },
        },
    ];
};

export default getTracks;
