import { useMemo } from 'react';
import getAssembly from '@components/organisms/Gene/GeneViewer/assembly';
import getTracks from '@components/organisms/Gene/GeneViewer/tracks';
import getDefaultSessionConfig from '@components/organisms/Gene/GeneViewer/defaultSessionConfig';
import { getEssentialityDataUrl } from '../utils/constants';
import { GenomeMeta } from '../interfaces/Genome';
import { GeneMeta } from '../interfaces/Gene';

export interface GeneViewerConfig {
  assembly: any;
  tracks: any[];
  sessionConfig: any;
  selectedGenomes: Array<{
    id: string;
    isolate_name: string;
    type_strain: boolean;
  }>;
}

export const useGeneViewerConfig = (
  genomeMeta: GenomeMeta | null,
  geneMeta: GeneMeta | null,
  includeEssentiality: boolean
): GeneViewerConfig => {
  const assembly = useMemo(() => {
    if (genomeMeta) {
      return getAssembly(
        genomeMeta, 
        import.meta.env.VITE_ASSEMBLY_INDEXES_PATH || ''
      );
    }
    return null;
  }, [genomeMeta]);

  const tracks = useMemo(() => {
    return genomeMeta
      ? getTracks(
          genomeMeta,
          import.meta.env.VITE_GFF_INDEXES_PATH || '',
          getEssentialityDataUrl(genomeMeta.isolate_name),
          includeEssentiality
        )
      : [];
  }, [genomeMeta, includeEssentiality]);

  const selectedGenomes = useMemo(() => {
    return genomeMeta
      ? [{
          id: genomeMeta.isolate_name,
          isolate_name: genomeMeta.isolate_name,
          type_strain: genomeMeta.type_strain
        }]
      : [];
  }, [genomeMeta]);

  const sessionConfig = useMemo(() => {
    if (genomeMeta) {
      return getDefaultSessionConfig(geneMeta, genomeMeta, assembly, tracks);
    } else {
      // Default session configuration if only genomeMeta is available
      return {
        name: "Default Genome View",
        views: [
          {
            type: "LinearGenomeView",
            bpPerPx: 2,
            tracks: tracks,
            displayedRegions: [
              {
                refName: 'Default assembly',
                start: 0,
                end: 5000000
              }
            ]
          }
        ]
      };
    }
  }, [genomeMeta, geneMeta, assembly, tracks]);

  return {
    assembly,
    tracks,
    sessionConfig,
    selectedGenomes,
  };
};

export const refreshStructuralAnnotationTrack = (viewState: any): void => {
  if (!viewState?.session?.views?.[0]) return;
  
  const view = viewState.session.views[0];
  viewState.session.tracks.forEach((track: any) => {
    const trackId = track.trackId || track.get('trackId');
    if (trackId === 'structural_annotation') {
      view.hideTrack(trackId);
      view.showTrack(trackId);
    }
  });
}; 