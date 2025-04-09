import {GenomeMeta} from "../../../../interfaces/Genome";

const getTracks
        = (genomeMeta: GenomeMeta, gffBaseUrl: string, apiUrl: string, includeEssentiality: boolean) => {
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
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz`,
                },
                apiUrl: apiUrl,
                isTypeStrain: genomeMeta.type_strain,
                includeEssentiality: includeEssentiality,
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
                        color1: `jexl:getColorForEssentiality(get(feature, 'Essentiality'))`,
                        labels: {
                            name: `jexl:
                            (
                              (get(feature, 'gene') && get(feature, 'gene') + ' / ' + get(feature, 'locus_tag')) 
                              || get(feature, 'locus_tag')
                            ) + 
                            ' ' + (get(feature, 'EssentialityVisual') || '')
                          `,
                        },
                        showForward: true,
                        showReverse: true,
                        showTranslation: true,
                        showLabels: true,
                    },
                }
            ],
        });

        return tracks;
    }
;

export default getTracks;
