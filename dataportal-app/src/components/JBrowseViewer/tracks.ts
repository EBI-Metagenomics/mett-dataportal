import { IsolateData } from './JBrowseViewer';

const getTracks = (isolateData: IsolateData) => [
  {
    type: 'FeatureTrack',
    trackId: 'structural_annotation',
    name: 'Structural Annotation',
    category: ['Annotations'],
    adapter: {
      type: 'FromConfigAdapter',
      gffLocation: {
        uri: isolateData.gff_url,
      },
    },
  },
];

export default getTracks;
