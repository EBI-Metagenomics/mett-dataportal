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
                uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz`,
            },
            index: {
                location: {
                    uri: `${gffBaseUrl}/${genomeMeta.isolate_name}/${genomeMeta.gff_file}.gz.tbi`,
                },
            },
        },
        visible: true,
    });

    return tracks;
};

export default getTracks;
