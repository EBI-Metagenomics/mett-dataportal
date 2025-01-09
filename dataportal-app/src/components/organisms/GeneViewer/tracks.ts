import {GenomeMeta} from "../../../interfaces/Genome";

const getTracks = (genomeMeta: GenomeMeta, gffBaseUrl: string) => {
    const tracks = [];

    // Structural Annotation Track
    tracks.push({
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
                rendererTypeName: 'CustomSvgFeatureRenderer',
                renderer: {
                    type: 'CustomSvgFeatureRenderer',
                    // maxHeight: 5000,
                    // labels: {
                    //     name: "jexl:get(feature,'locus_tag') || get(feature,'sequence')",
                    // },
                    // color3: '#965567',
                    // color1: "jexl:get(feature,'type')!='CDS'?'gray':get(feature,'strand')>0?'violet':'turquoise'",
                },
                showForward: true,
                showReverse: true,
                showTranslation: true,
                showLabels: true,
            },
        ],
    });

    // Conditionally add the Essentiality Track for type strains
    // if (genomeMeta.type_strain) {
    //     tracks.push({
    //         type: 'FeatureTrack',
    //         trackId: 'essentiality_annotation',
    //         name: 'Essentiality Annotation',
    //         assemblyNames: [genomeMeta.assembly_name],
    //         category: ['Essentiality'],
    //         adapter: {
    //             type: 'Gff3TabixAdapter',
    //             gffGzLocation: {
    //                 uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/essentiality/${genomeMeta.isolate_name}_essentiality.gff3.gz`,
    //             },
    //             index: {
    //                 location: {
    //                     uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/essentiality/${genomeMeta.isolate_name}_essentiality.gff3.gz.tbi`,
    //                 },
    //             },
    //         },
    //         visible: true,
    //         displays: [
    //             {
    //                 displayId: `essentiality_annotation-${genomeMeta.assembly_name}-LinearBasicDisplay`,
    //                 type: 'LinearBasicDisplay',
    //                 renderer: {
    //                     type: 'SvgFeatureRenderer',
    //                     color1: "jexl: (get(feature, 'essentiality_solid') == 'essential' && 'red') || " +
    //                         "(get(feature, 'essentiality_solid') == 'not_essential' && 'blue') || " +
    //                         "(get(feature, 'essentiality_solid') == 'unclear' && 'yellow') || " +
    //                         "(get(feature, 'essentiality_solid').includes('liquid') && 'orange') || " +
    //                         "(get(feature, 'essentiality_solid').includes('solid') && 'green') || " +
    //                         "(get(feature, 'essentiality_liquid').includes('liquid') && 'orange') || " +
    //                         "(get(feature, 'essentiality_liquid').includes('solid') && 'green') || 'gray'",
    //                     labels: {
    //                         name: "jexl:get(feature, 'id') + ' (' + get(feature, 'essentiality_solid') + ')'",
    //                     },
    //
    //                 },
    //                 showLabels: true,
    //             },
    //         ],
    //     });
    // }

    return tracks;
};

export default getTracks;
