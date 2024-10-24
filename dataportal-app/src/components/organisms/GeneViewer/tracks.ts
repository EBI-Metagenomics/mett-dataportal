import { GenomeMeta } from '../../pages/GeneViewerPage';

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
        displays: [
            {
                displayId: `structural_annotation-${genomeMeta.assembly_name}-LinearBasicDisplay`,
                type: 'LinearBasicDisplay',
                renderer: {
                    type: 'SvgFeatureRenderer',
                    maxHeight: 5000,
                    labels: {
                        name: "jexl:get(feature,'locus') || get(feature,'sequence_name')",
                    },
                    color3: '#965567',
                    color1: "jexl:get(feature,'type')!='CDS'?'gray':get(feature,'strand')>0?'violet':'turquoise'",
                },
            },
        ],
    },
    {
        type: 'FeatureTrack',
        trackId: 'my_special_track',
        name: 'Special Track',
        assemblyNames: [genomeMeta.assembly_name],
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
        displays: [
            {
                displayId: `my_special_track-${genomeMeta.assembly_name}-LinearBasicDisplay`,
                type: 'LinearBasicDisplay',
                renderer: {
                    type: 'SvgFeatureRenderer',
                    maxHeight: 5000,
                    labels: {
                        name: "jexl:get(feature,'locus') || get(feature,'sequence_name')",
                    },
                    color3: '#965567',
                    color1: "jexl:get(feature,'type')!='CDS'?'gray':get(feature,'strand')>0?'violet':'turquoise'",
                },
            },
        ],
    },
];

export default getTracks;
