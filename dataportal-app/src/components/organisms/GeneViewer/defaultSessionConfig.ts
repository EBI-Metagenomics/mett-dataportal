import {GeneMeta} from "@components/interfaces/Gene";
import {GenomeMeta} from "@components/interfaces/Genome";


const getDefaultSessionConfig = (
    geneMeta: GeneMeta | null,
    genomeMeta: GenomeMeta | null,
    assembly: any,
    tracks: any[]
) => {
    if (!genomeMeta) {
        console.log("Genome meta information not found");
        return null;
    }

    const displayedRegions = geneMeta
        ? [
            {
                refName: geneMeta.seq_id,
                start: geneMeta.start_position || 0,
                end: geneMeta.end_position || 1000,
                reversed: true,
                assemblyName: genomeMeta.assembly_name,
            },
        ]
        : [
            {
                refName: genomeMeta.contigs[0].seq_id,
                start: 0,
                end: 1000,
                reversed: true,
                assemblyName: genomeMeta.assembly_name,
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
