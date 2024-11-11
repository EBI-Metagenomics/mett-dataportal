import { GeneMeta, GenomeMeta } from '../../pages/GeneViewerPage';

const getDefaultSessionConfig = (
    geneMeta: GeneMeta | null,
    genomeMeta: GenomeMeta | null,
    assembly: any,
    tracks: any[]
) => {
    if (!genomeMeta) {
        console.log("Genome meta information not found");
        return null; // Return null if genomeMeta is missing
    }

    const displayedRegions = geneMeta
        ? [
            {
                refName: geneMeta.seq_id,
                start: geneMeta.start_position || 0,
                end: geneMeta.end_position || 50000,
                reversed: true,
                assemblyName: genomeMeta.assembly_name,
            },
        ]
        : [
            {
                refName: genomeMeta.assembly_name,
                start: 0,
                end: 5000000, // Adjust this default range
            },
        ];

    return {
        name: 'Gene Viewer Session',
        margin: 0,
        views: [
            {
                id: 'linearGenomeView',
                minimized: false,
                type: 'LinearGenomeView',
                hideTrackSelector: false,
                displayedRegions: displayedRegions,
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
                hideHeader: true,
                hideHeaderOverview: false,
                hideNoTracksActive: false,
                trackSelectorType: 'hierarchical',
                trackLabels: 'offset',
                showCenterLine: false,
                showCytobandsSetting: true,
                showGridlines: true,
            },
        ],
    };
};

export default getDefaultSessionConfig;
