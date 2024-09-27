export const assemblyConfig = {
  name: "Bacteroides_uniformis_BU_ATCC8492",
  sequence: {
    type: "ReferenceSequenceTrack",
    trackId: "assembly_sequence",
    adapter: {
      type: "IndexedFastaAdapter",
      fastaLocation: {
        uri: "ftp://your-ftp-server-path-to/Bacteroides_uniformis_BU_ATCC8492.fasta",
      },
      faiLocation: {
        uri: "ftp://your-ftp-server-path-to/Bacteroides_uniformis_BU_ATCC8492.fasta.fai",
      },
    },
  },
  aliases: ["BU_ATCC8492"],
};
