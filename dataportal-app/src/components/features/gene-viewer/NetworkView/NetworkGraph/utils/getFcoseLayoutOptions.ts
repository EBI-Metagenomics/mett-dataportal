import type cytoscape from 'cytoscape';
import { NETWORK_VIEW_CONSTANTS } from '../../constants';

const L = NETWORK_VIEW_CONSTANTS.FCOSE_LAYOUT;

export interface FcoseLayoutParams {
  /** Place this node at the layout origin (neighborhood focal gene). */
  focalNodeId?: string | null;
  /** Slightly longer animation when updating an existing graph in place. */
  inPlace?: boolean;
  /** Override randomize. Reset uses true so the graph visibly re-spreads. */
  randomize?: boolean;
  animate?: boolean;
  nodeCount?: number;
}

/**
 * Build fCoSE layout options tuned for PPI neighborhood graphs.
 * Pins the focal gene when provided so hub-and-spoke stays readable.
 */
export function getFcoseLayoutOptions({
  focalNodeId,
  inPlace = false,
  randomize,
  animate,
  nodeCount = 0,
}: FcoseLayoutParams = {}): Record<string, unknown> {
  const large = nodeCount > 80;
  const pinFocal = !!focalNodeId && randomize !== true;
  const fixedNodeConstraint =
    pinFocal
      ? [{ nodeId: String(focalNodeId), position: { x: 0, y: 0 } }]
      : undefined;

  return {
    name: 'fcose',
    quality: large || inPlace ? 'default' : L.QUALITY,
    randomize: randomize ?? (fixedNodeConstraint ? false : L.RANDOMIZE),
    animate: animate ?? !inPlace,
    animationDuration: inPlace ? L.ANIMATION_DURATION_IN_PLACE : L.ANIMATION_DURATION,
    fit: false,
    padding: inPlace ? L.PADDING_IN_PLACE : L.PADDING,
    nodeDimensionsIncludeLabels: true,
    uniformNodeDimensions: false,
    packComponents: false,
    sampleSize: L.SAMPLE_SIZE,
    nodeSeparation: L.NODE_SEPARATION,
    nodeRepulsion: () => (large ? 2500 : L.NODE_REPULSION),
    idealEdgeLength: (edge: cytoscape.EdgeSingular) => {
      const w = Number(edge.data('weight') ?? 0);
      if (w <= 0) return L.IDEAL_EDGE_LENGTH;
      const len = L.IDEAL_EDGE_LENGTH - Math.min(w, 1) * L.WEIGHT_LENGTH_FACTOR;
      return Math.max(L.MIN_EDGE_LENGTH, len);
    },
    edgeElasticity: () => L.EDGE_ELASTICITY,
    nestingFactor: 0.1,
    numIter: inPlace || large ? Math.min(800, L.NUM_ITER_IN_PLACE) : L.NUM_ITER,
    tile: true,
    tilingPaddingVertical: 12,
    tilingPaddingHorizontal: 12,
    gravity: L.GRAVITY,
    gravityRange: L.GRAVITY_RANGE,
    initialEnergyOnIncremental: L.INITIAL_ENERGY_ON_INCREMENTAL,
    fixedNodeConstraint,
  };
}
