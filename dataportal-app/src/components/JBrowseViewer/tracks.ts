import {IsolateData} from './JBrowseViewer';

const getTracks = (isolateData: IsolateData) => [
  {
    type: 'FeatureTrack',
    trackId: 'annotations',
    name: 'Annotations',
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
