import {GenomeMeta} from '../../pages/GeneViewerPage';

const getTracks = (genomeMeta: GenomeMeta, gffBaseUrl: string) => [
    {
        type: 'FeatureTrack',
        trackId: 'structural_annotation',
        name: 'Structural Annotation',
        assemblyNames: [genomeMeta.assembly_name],
        category: ['Annotations'],
        adapter: {
            type: 'Gff3TabixAdapter',
            gffGzLocation: {
                uri: `${gffBaseUrl}/${genomeMeta.gff_file}.gz`,
            },
            index: {
                location: {
                    uri: `${gffBaseUrl}/${genomeMeta.gff_file}.gz.tbi`,
                },
            },
        },
        visible: true,
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
                assemblyNames: [genomeMeta.assembly_name],
            },
        },
    },

];

export default getTracks;
