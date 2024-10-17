import { GeneMeta, GenomeMeta } from '../../pages/GeneViewerPage';

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
            hideTrackSelector: false,
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
                ...tracks.map(track => ({
                    id: track.trackId,
                    type: track.type,
                    configuration: track.trackId,
                    minimized: false,
                    visible: true,
                    displays: track.displays,
                })),
            ],
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
