import {IsolateData} from './JBrowseViewer';

const getAssembly = (isolateData: IsolateData) => ({
  name: isolateData.isolate_name,
  sequence: {
    type: 'ReferenceSequenceTrack',
    trackId: 'reference',
    adapter: {
      type: 'FromConfigSequenceAdapter',
      fastaLocation: {
        uri: isolateData.fasta_url,
      },
    },
  },
});

export default getAssembly;
