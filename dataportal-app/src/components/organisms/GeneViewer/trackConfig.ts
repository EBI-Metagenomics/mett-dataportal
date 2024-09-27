export const trackConfig = [
  {
    type: "FeatureTrack",
    trackId: "gene_annotations",
    name: "Gene Annotations",
    assemblyNames: ["Bacteroides_uniformis_BU_ATCC8492"],
    adapter: {
      type: "Gff3TabixAdapter",
      gffGzLocation: {
        uri: "ftp://your-ftp-server-path-to/Bacteroides_uniformis_BU_ATCC8492.gff.gz",
      },
      index: {
        location: {
          uri: "ftp://your-ftp-server-path-to/Bacteroides_uniformis_BU_ATCC8492.gff.gz.tbi",
        },
      },
    },
  },
];
