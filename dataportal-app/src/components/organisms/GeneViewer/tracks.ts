import {GenomeMeta} from "../../../interfaces/Genome";

const getTracks = (genomeMeta: GenomeMeta, gffBaseUrl: string, apiUrl: string) => {
    const tracks = [];

    // Structural Annotation Track
    tracks.push({
        type: 'FeatureTrack',
        trackId: 'structural_annotation',
        name: 'Structural Annotation',
        assemblyNames: [genomeMeta.assembly_name],
        category: ['Annotations'],
        adapter: {
            type: 'EssentialityAdapter',
            gffGzLocation: {
                locationType: 'UriLocation',
                uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz`,
            },
            apiUrl: apiUrl,
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
                // rendererTypeName: 'CustomSvgFeatureRenderer',
                renderer: {
                    type: 'SvgFeatureRenderer',
                    color1: `
                            jexl: (
                              get(feature, 'essentiality').includes('essential') && 'red'
                            ) || (
                              get(feature, 'essentiality').includes('not_essential') && 'blue'
                            ) || (
                              get(feature, 'essentiality').includes('unclear') && 'yellow'
                            ) || 'gray'
                          `,
                    labels: {
                        name: "jexl:get(feature, 'locus_tag')",
                    },
                },
                showLabels: true,
                showForward: true,
                showReverse: true,
                showTranslation: true,
            },
        ],
    });

    return tracks;
};

export default getTracks;
