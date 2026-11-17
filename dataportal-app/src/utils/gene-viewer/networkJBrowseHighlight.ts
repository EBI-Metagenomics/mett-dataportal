import { VIEWPORT_SYNC_CONSTANTS } from './viewportSyncConstants';

/**
 * JBrowse gene colors driven by the PPI network.
 *
 * Priority: hovered gene, then the selected anchor gene (existing blue),
 * then the anchor's interaction partners, then essentiality.
 */

export interface AnchorGraphNode {
  id: string;
  locus_tag?: string | null;
}

export interface AnchorGraphEdge {
  source: string;
  target: string;
  edgeType?: string | null;
}

interface JBrowseDisplay {
  reload?: () => void;
  setError?: (error: unknown) => void;
}

interface JBrowseTrack {
  displays?: JBrowseDisplay[];
}

export interface JBrowseHighlightView {
  session?: {
    views?: Array<{
      tracks?: JBrowseTrack[];
    }>;
  };
}

export interface NetworkJBrowseHighlightState {
  interactionLocusTags: readonly string[];
  hoverLocusTag?: string | null;
}

const REFRESH_DELAY_MS = 50;

let interactionLocusTags = new Set<string>();
let hoverLocusTag: string | null = null;
let lastSignature = '';
let lastCouldPaint = false;
let refreshTimer: ReturnType<typeof setTimeout> | null = null;
let pendingView: JBrowseHighlightView | null | undefined;

/** Direct non-ortholog partners of the anchor, as locus tags JBrowse can paint. */
export function anchorInteractionLocusTags(
  nodes: readonly AnchorGraphNode[],
  edges: readonly AnchorGraphEdge[],
  anchorId: string | null | undefined,
): string[] {
  if (!anchorId) return [];
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const anchor = nodes.find((node) => node.id === anchorId || node.locus_tag === anchorId);
  if (!anchor) return [];

  const tags = new Set<string>();
  edges.forEach((edge) => {
    if (edge.edgeType === 'ortholog') return;
    const otherId =
      edge.source === anchor.id ? edge.target : edge.target === anchor.id ? edge.source : null;
    if (!otherId) return;
    const tag = byId.get(otherId)?.locus_tag?.trim();
    if (tag && tag !== anchor.locus_tag) tags.add(tag);
  });
  return [...tags].sort();
}

export function geneColorForNetworkHighlight(args: {
  locusTag?: string | null;
  selectedGeneId?: string | null;
  hoverLocusTag?: string | null;
  interactionLocusTags?: ReadonlySet<string> | null;
  essentialityColor: string;
}): string {
  const locusTag = args.locusTag?.trim();
  if (!locusTag) return args.essentialityColor;
  if (args.hoverLocusTag && locusTag === args.hoverLocusTag) {
    return VIEWPORT_SYNC_CONSTANTS.NETWORK_HOVER_HIGHLIGHT_COLOR;
  }
  if (args.selectedGeneId && locusTag === args.selectedGeneId) {
    return VIEWPORT_SYNC_CONSTANTS.GENE_HIGHLIGHT_COLOR;
  }
  if (args.interactionLocusTags?.has(locusTag)) {
    return VIEWPORT_SYNC_CONSTANTS.NETWORK_INTERACTION_HIGHLIGHT_COLOR;
  }
  return args.essentialityColor;
}

export function readNetworkJBrowseHighlight(): {
  interactionLocusTags: ReadonlySet<string>;
  hoverLocusTag: string | null;
} {
  return { interactionLocusTags, hoverLocusTag };
}

export function refreshJBrowseGeneColors(
  viewState: JBrowseHighlightView | null | undefined,
): void {
  const tracks = viewState?.session?.views?.[0]?.tracks;
  if (!tracks) return;
  tracks.forEach((track) => {
    track.displays?.forEach((display) => {
      try {
        if (display.reload) display.reload();
        else display.setError?.(undefined);
      } catch {
        // A display can reject reload while JBrowse is tearing down.
      }
    });
  });
}

function canPaint(viewState: JBrowseHighlightView | null | undefined): boolean {
  return Boolean(viewState?.session?.views?.[0]?.tracks);
}

function scheduleRefresh(viewState: JBrowseHighlightView | null | undefined): void {
  pendingView = viewState;
  if (refreshTimer) return;
  refreshTimer = setTimeout(() => {
    refreshTimer = null;
    refreshJBrowseGeneColors(pendingView);
  }, REFRESH_DELAY_MS);
}

export function publishNetworkJBrowseHighlight(
  next: NetworkJBrowseHighlightState,
  viewState: JBrowseHighlightView | null | undefined,
): void {
  interactionLocusTags = new Set(next.interactionLocusTags);
  hoverLocusTag = next.hoverLocusTag?.trim() || null;
  const signature = `${hoverLocusTag ?? ''}|${[...interactionLocusTags].sort().join(',')}`;
  const paintable = canPaint(viewState);
  if (signature === lastSignature && paintable === lastCouldPaint) return;
  lastSignature = signature;
  lastCouldPaint = paintable;
  scheduleRefresh(viewState);
}

export function clearNetworkJBrowseHighlight(
  viewState?: JBrowseHighlightView | null,
): void {
  interactionLocusTags = new Set();
  hoverLocusTag = null;
  lastSignature = '';
  lastCouldPaint = false;
  if (refreshTimer) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
  if (viewState) refreshJBrowseGeneColors(viewState);
}
