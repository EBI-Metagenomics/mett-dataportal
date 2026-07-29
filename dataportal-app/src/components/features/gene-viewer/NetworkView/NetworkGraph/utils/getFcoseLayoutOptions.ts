import type cytoscape from 'cytoscape';
import { NETWORK_VIEW_CONSTANTS } from '../../constants';

const L = NETWORK_VIEW_CONSTANTS.FCOSE_LAYOUT;

export interface FcoseLayoutParams {
  /** Place this node at the layout origin (neighborhood focal gene). */
  focalNodeId?: string | null;
  /** Slightly longer animation when updating an existing graph in place. */
  inPlace?: boolean;
}

/**
 * Build fCoSE layout options tuned for PPI neighborhood graphs.
 * Pins the focal gene when provided so hub-and-spoke stays readable.
 */
export function getFcoseLayoutOptions({
  focalNodeId,
  inPlace = false,
}: FcoseLayoutParams = {}): Record<string, unknown> {
  const fixedNodeConstraint =
    focalNodeId
      ? [{ nodeId: focalNodeId, position: { x: 0, y: 0 } }]
      : undefined;

  return {
    name: 'fcose',
    // "proof" = better aesthetics; required when randomize is false with constraints
    quality: L.QUALITY,
    randomize: fixedNodeConstraint ? false : L.RANDOMIZE,
    animate: true,
    animationDuration: inPlace ? L.ANIMATION_DURATION_IN_PLACE : L.ANIMATION_DURATION,
    fit: true,
    padding: inPlace ? L.PADDING_IN_PLACE : L.PADDING,
    nodeDimensionsIncludeLabels: true,
    uniformNodeDimensions: false,
    // Requires cytoscape-layout-utilities; keep off to avoid an extra dependency
    packComponents: false,
    sampleSize: L.SAMPLE_SIZE,
    nodeSeparation: L.NODE_SEPARATION,
    nodeRepulsion: () => L.NODE_REPULSION,
    idealEdgeLength: (edge: cytoscape.EdgeSingular) => {
      const w = Number(edge.data('weight') ?? 0);
      if (w <= 0) return L.IDEAL_EDGE_LENGTH;
      // Stronger interactions → slightly shorter preferred length
      const len = L.IDEAL_EDGE_LENGTH - Math.min(w, 1) * L.WEIGHT_LENGTH_FACTOR;
      return Math.max(L.MIN_EDGE_LENGTH, len);
    },
    edgeElasticity: () => L.EDGE_ELASTICITY,
    nestingFactor: 0.1,
    numIter: inPlace ? L.NUM_ITER_IN_PLACE : L.NUM_ITER,
    tile: true,
    tilingPaddingVertical: 12,
    tilingPaddingHorizontal: 12,
    gravity: L.GRAVITY,
    gravityRange: L.GRAVITY_RANGE,
    initialEnergyOnIncremental: L.INITIAL_ENERGY_ON_INCREMENTAL,
    fixedNodeConstraint,
  };
}
