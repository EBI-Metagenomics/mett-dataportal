import { useEffect, useRef } from 'react';
import { reaction } from 'mobx';
import { GeneService } from '../../../../../services/gene';
import { useViewportSyncStore } from '../../../../../stores/viewportSyncStore';
import { isLikelyGeneId } from '../../../../../utils/gene-viewer/isLikelyGeneId';

declare global {
  interface Window {
    selectedGeneId?: string;
  }
}

function extractLocusTag(selection: unknown): string | null {
  if (!selection || typeof selection !== 'object') return null;

  const feature = selection as {
    get?: (key: string) => unknown;
    id?: () => string;
    locus_tag?: string;
  };

  const fromGet = feature.get?.('locus_tag');
  if (typeof fromGet === 'string' && fromGet) return fromGet;

  if (typeof feature.locus_tag === 'string' && feature.locus_tag) {
    return feature.locus_tag;
  }

  const id = feature.id?.();
  if (typeof id === 'string' && id) return id;

  return null;
}

function refreshTrackHighlighting(viewState: { session?: { views?: any[] } }): void {
  try {
    const view = viewState.session?.views?.[0];
    if (!view?.tracks) return;

    view.tracks.forEach((track: any) => {
      track.displays?.forEach((display: any) => {
        try {
          if (display.reload) {
            display.reload();
          } else if (display.setError) {
            display.setError(undefined);
          }
        } catch {
          // Ignore individual display errors
        }
      });
    });

    if (view.setWidth) {
      view.setWidth(view.width + 0.001);
      setTimeout(() => view.setWidth(view.width - 0.001), 10);
    }
  } catch (err) {
    console.warn('Could not trigger JBrowse re-render:', err);
  }
}

/**
 * Observe JBrowse session.selection (canvas/SVG-agnostic) and load gene details.
 */
export function useJBrowseFeatureSelection(
  viewState: any,
  onFeatureSelect?: (feature: any) => void
): void {
  const lastSelectedIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!viewState?.session || !onFeatureSelect) return;

    const dispose = reaction(
      () => viewState.session?.selection,
      selection => {
        const featureId = extractLocusTag(selection);
        if (!featureId || !isLikelyGeneId(featureId)) return;
        if (featureId === lastSelectedIdRef.current) return;

        lastSelectedIdRef.current = featureId;
        window.selectedGeneId = featureId;
        refreshTrackHighlighting(viewState);
        useViewportSyncStore.getState().setSelectedLocusTag(featureId);

        Promise.all([
          GeneService.fetchGeneByLocusTag(featureId),
          GeneService.fetchGeneProteinSeq(featureId).catch(() => ({
            protein_sequence: '',
          })),
        ])
          .then(([geneData, proteinData]) => {
            onFeatureSelect({
              ...geneData,
              protein_sequence: proteinData.protein_sequence || '',
            });
          })
          .catch((err: unknown) => {
            console.warn('Failed to fetch gene data:', err);
            onFeatureSelect({
              locus_tag: featureId,
              id: featureId,
            });
          });
      }
    );

    return dispose;
  }, [viewState, onFeatureSelect]);
}
