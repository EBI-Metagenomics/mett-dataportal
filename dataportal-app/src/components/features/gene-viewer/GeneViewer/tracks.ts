import {GenomeMeta} from "../../../../interfaces/Genome";

const getTracks
        = (genomeMeta: GenomeMeta, gffBaseUrl: string, apiUrl: string, includeEssentiality: boolean) => {
        console.log('🔧 getTracks called with:', {
            genomeMeta: genomeMeta?.isolate_name,
            type_strain: genomeMeta?.type_strain,
            includeEssentiality,
            gffBaseUrl,
            apiUrl
        });
        
        const tracks = [];

        // Structural Annotation Track
        tracks.push({
            type: 'FeatureTrack',
            trackId: 'structural_annotation',
            name: 'Structural Annotation',
            assemblyNames: [genomeMeta.assembly_name],
            category: ['Annotations'],
            adapter: {
                type: 'EnhancedGeneFeatureAdapter',
                gffGzLocation: {
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz`,
                },
                apiUrl: apiUrl,
                isTypeStrain: genomeMeta.type_strain,
                includeEssentiality: includeEssentiality,
                speciesName: genomeMeta.species_scientific_name || genomeMeta.species_acronym,
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
                    // Disable the default onClick handler that opens feature details
                    onClick: null,
                    onFeatureClick: null,
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
                        height: 50,
                        showForward: true,
                        showReverse: true,
                        showTranslation: true,
                        showLabels: true,
                    },
                    mouseover: `jexl:
                      (get(feature, 'gene') && 'Gene: ' + get(feature, 'gene')  + '<br/>'  || '') +
                      (get(feature, 'locus_tag') && 'Locus Tag: ' + get(feature, 'locus_tag') + '<br/>' || '') +
                      (get(feature, 'product') && 'Product: ' + get(feature, 'product') + '<br/>' || '') +
                      (get(feature, 'Alias') && 'Alias: ' + get(feature, 'Alias') + '<br/>'  || '') +
                      (get(feature, 'Essentiality') && 'Essentiality: ' + get(feature, 'Essentiality') + '<br/>' || '')
                    `
                }
            ],
        });

        return tracks;
    }
;

export default getTracks;
