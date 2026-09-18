import { useMemo } from 'react';
import getAssembly from '@components/features/gene-viewer/GeneViewer/assembly';
import getTracks from '@components/features/gene-viewer/GeneViewer/tracks';
import getDefaultSessionConfig from '@components/features/gene-viewer/GeneViewer/defaultSessionConfig';
import { ZOOM_LEVELS } from '../common/constants';
import { GenomeMeta } from '../../interfaces/Genome';
import { GeneMeta } from '../../interfaces/Gene';
import { useMettRelease } from '../../hooks/useMettRelease';
import { buildJbrowseIndexDirs } from './jbrowseIndexPaths';

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
  const { selected, catalog } = useMettRelease();

  const indexDirs = useMemo(() => {
    if (!genomeMeta) {
      return { fastaDir: '', gffDir: '' };
    }
    return buildJbrowseIndexDirs({
      basePath: import.meta.env.VITE_JBROWSE_INDEXES_PATH || '',
      selectedRelease: selected,
      catalog,
      isolateName: genomeMeta.isolate_name,
      speciesAcronym: genomeMeta.species_acronym,
      fastaFile: genomeMeta.fasta_file,
      assemblyName: genomeMeta.assembly_name,
    });
  }, [genomeMeta, selected, catalog]);

  const assembly = useMemo(() => {
    if (genomeMeta) {
      return getAssembly(
        genomeMeta, 
        indexDirs.fastaDir
      );
    }
    return null;
  }, [genomeMeta, indexDirs.fastaDir]);

  const tracks = useMemo(() => {
    return genomeMeta
      ? getTracks(
          genomeMeta,
          indexDirs.gffDir,
          includeEssentiality
        )
      : [];
  }, [genomeMeta, includeEssentiality, indexDirs.gffDir]);

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
            bpPerPx: ZOOM_LEVELS.BP_PER_PX,  // Base pairs per pixel for track display
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