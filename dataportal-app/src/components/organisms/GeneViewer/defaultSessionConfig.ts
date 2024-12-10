import {GeneMeta} from "../../../interfaces/Gene";
import {GenomeMeta} from "../../../interfaces/Genome";

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

    const displayedRegions = genomeMeta.contigs.map(contig => ({
        refName: contig.seq_id,
        start: 0,
        end: contig.length,
        reversed: false,
        assemblyName: genomeMeta.assembly_name,
    }));

    return {
        name: 'Gene Viewer Session',
        configuration: {
            header: {
                disable: true,
                hidden: true,
            },
        },
        margin: 0,
        views: [
            {
                id: 'linearGenomeView',
                minimized: false,
                type: 'LinearGenomeView',
                hideHeader: true,
                configuration: {
                    // Add an extra configuration to hide header
                    header: {
                        hidden: true,
                        disable: true
                    }
                },
                hideTrackSelector: true,
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
                hideHeaderOverview: true,
                hideNoTracksActive: false,
                trackSelectorType: 'hierarchical',
                trackLabels: 'offset',
                showCenterLine: false,
                showCytobandsSetting: true,
                showGridlines: true,
                scale: 1,
                bpPerPx: 2,
            },
        ],
    };
};

export default getDefaultSessionConfig;
