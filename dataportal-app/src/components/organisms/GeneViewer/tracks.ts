import {GenomeMeta} from "../../../interfaces/Genome";

const getTracks = (genomeMeta: GenomeMeta, gffBaseUrl: string) => [
    // Structural Annotation Track
    {
        type: 'FeatureTrack',
        trackId: 'structural_annotation',
        name: 'Structural Annotation',
        assemblyNames: [genomeMeta.assembly_name],
        category: ['Annotations'],
        adapter: {
            type: 'Gff3TabixAdapter',
            gffGzLocation: {
                uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz`,
            },
            index: {
                location: {
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz.tbi`,
                },
            },
        },
        visible: true,
        textSearching: {
            textSearchAdapter: {
                type: 'TrixTextSearchAdapter',
                textSearchAdapterId: 'gff3tabix_genes-index',
                ixFilePath: {
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/trix/${genomeMeta.gff_file}.gz.ix`,
                },
                ixxFilePath: {
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/trix/${genomeMeta.gff_file}.gz.ixx`,
                },
                metaFilePath: {
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/trix/${genomeMeta.gff_file}.gz_meta.json`,
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
                showForward: true,
                showReverse: true,
                showTranslation: true,
                showLabels: true,
            },
        ],
    },

    // Essentiality Track
    {
        type: 'FeatureTrack',
        trackId: 'essentiality_annotation',
        name: 'Essentiality Annotation',
        assemblyNames: [genomeMeta.assembly_name],
        category: ['Essentiality'],
        adapter: {
            type: 'Gff3TabixAdapter',
            gffGzLocation: {
                uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/essentiality/${genomeMeta.isolate_name}_essentiality.gff3.gz`,
            },
            index: {
                location: {
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/essentiality/${genomeMeta.isolate_name}_essentiality.gff3.gz.tbi`,
                },
            },
        },
        visible: true,
        displays: [
            {
                displayId: `essentiality_annotation-${genomeMeta.assembly_name}-LinearBasicDisplay`,
                type: 'LinearBasicDisplay',
                renderer: {
                    type: 'SvgFeatureRenderer',
                    color: "jexl:get(feature, 'Essentiality') == 'essential' ? 'red' : " +
                        "get(feature, 'Essentiality') == 'not_essential' ? 'blue' : " +
                        "get(feature, 'Essentiality').includes('liquid') ? 'orange' : " +
                        "get(feature, 'Essentiality').includes('solid') ? 'green' : 'gray'",
                    labels: {
                        name: "jexl:get(feature, 'ID') + ' (' + get(feature, 'Essentiality_Liquid') + ', ' + get(feature, 'Essentiality_Solid') + ')'",
                    },
                },
                showLabels: true,
            },
        ],
    },
];

export default getTracks;
