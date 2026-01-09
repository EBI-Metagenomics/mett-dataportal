import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';

/**
 * Calculate degree centrality for each node
 * Degree centrality = number of connections (edges) for a node
 * Higher degree = more connected = closer to center in global view
 */
export function calculateDegreeCentrality(
  nodes: PPINetworkNode[],
  edges: PPINetworkEdge[]
): Map<string, number> {
  const centrality = new Map<string, number>();
  
  // Initialize all nodes with 0 degree
  nodes.forEach(node => {
    centrality.set(node.id, 0);
  });
  
  // Count edges for each node
  edges.forEach(edge => {
    const sourceCount = centrality.get(edge.source) || 0;
    const targetCount = centrality.get(edge.target) || 0;
    centrality.set(edge.source, sourceCount + 1);
    centrality.set(edge.target, targetCount + 1);
  });
  
  return centrality;
}

/**
 * Calculate normalized degree centrality (0-1 scale)
 * Normalizes by max degree in the network
 */
export function calculateNormalizedDegreeCentrality(
  nodes: PPINetworkNode[],
  edges: PPINetworkEdge[]
): Map<string, number> {
  const degreeCentrality = calculateDegreeCentrality(nodes, edges);
  const degrees = Array.from(degreeCentrality.values());
  const maxDegree = Math.max(...degrees, 1); // Avoid division by zero
  
  const normalized = new Map<string, number>();
  degreeCentrality.forEach((degree, nodeId) => {
    normalized.set(nodeId, degree / maxDegree);
  });
  
  return normalized;
}

/**
 * Get centrality tier for a node
 * Tiers determine which "ring" a node should be placed in
 * Higher centrality = inner ring (closer to center)
 */
export function getCentralityTier(centrality: number, numTiers: number = 6): number {
  // Map 0-1 centrality to tier 0 (outer) to numTiers-1 (inner)
  // Higher centrality = higher tier = closer to center
  // Use a formula that ensures proper distribution:
  // - centrality 0.0 -> tier 0 (outermost)
  // - centrality 1.0 -> tier numTiers-1 (innermost)
  const tier = Math.floor(centrality * numTiers);
  // Clamp to valid range [0, numTiers-1]
  return Math.min(Math.max(tier, 0), numTiers - 1);
}
