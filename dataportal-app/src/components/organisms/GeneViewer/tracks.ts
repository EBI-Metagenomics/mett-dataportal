import {GenomeMeta} from "../../../interfaces/Genome";
import {Feature} from '@jbrowse/core/util';

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
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz`,
                },
                apiUrl: apiUrl,
                isTypeStrain: genomeMeta.type_strain,
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
                        color1: `jexl:
                            get(feature, 'essentiality') == 'essential' ? '#FF0000' :
                            get(feature, 'essentiality') == 'not_essential' ? '#008000' :
                            get(feature, 'essentiality') == 'essential_liquid' ? '#FFA500' :
                            get(feature, 'essentiality') == 'essential_solid' ? '#800080' :
                            get(feature, 'essentiality') == 'unclear' ? '#808080' :
                            '#DAA520'`,
                        labels: {
                            name: `jexl:
                                get(feature, 'locus_tag') + ' ' +
                                (get(feature, 'essentiality') == 'essential' ? '🔴' :
                                get(feature, 'essentiality') == 'not_essential' ? '🟢' :
                                get(feature, 'essentiality') == 'essential_liquid' ? '🟠' :
                                get(feature, 'essentiality') == 'essential_solid' ? '🟣' : 
                                get(feature, 'essentiality') == 'unclear' ? '⚪️' : '')
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
