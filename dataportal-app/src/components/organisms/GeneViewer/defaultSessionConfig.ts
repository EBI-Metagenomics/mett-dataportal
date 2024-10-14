import {GeneMeta, GenomeMeta} from '../../pages/GeneViewerPage';

const getDefaultSessionConfig = (
    geneMeta: GeneMeta,
    genomeMeta: GenomeMeta,
    assembly: any,
    tracks: any[]
) => {
    return {
        name: 'Gene Viewer Session',
        view: {
            id: 'linearGenomeView',
            type: 'LinearGenomeView',
            trackSelectorType: 'hierarchical',
            displayedRegions: [
                {
                    refName: geneMeta.seq_id,
                    start: geneMeta?.start_position || 0,
                    end: geneMeta?.end_position || 50000,
                    assemblyName: genomeMeta.assembly_name,
                },
            ],
            tracks: [
                {
                    id: assembly.sequence.trackId,
                    type: assembly.sequence.type,
                    configuration: 'reference',
                    minimized: false,
                    displays: [
                        {
                            id: assembly.sequence.trackId,
                            type: 'LinearReferenceSequenceDisplay',
                            height: 180,
                            showForward: true,
                            showReverse: true,
                            showTranslation: true,
                            showLabels: true,
                        },
                    ],
                },
                // Feature/Annotation tracks
                ...tracks.map(track => ({
                    id: track.trackId,
                    type: track.type,
                    configuration: track.trackId,
                    minimized: false,
                    visible: true,
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
                })),
            ]
        },
        hideHeader: false,
        hideHeaderOverview: false,
        hideNoTracksActive: false,
        trackSelectorType: 'hierarchical',
        trackLabels: 'overlapping',
        showCenterLine: false,
        showCytobandsSetting: true,
        showGridlines: true,
    };
};

export default getDefaultSessionConfig;
