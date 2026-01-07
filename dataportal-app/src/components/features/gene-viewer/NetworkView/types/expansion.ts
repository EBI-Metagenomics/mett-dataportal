import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';

/**
 * Represents a node in the expansion path
 */
export interface ExpansionPathNode {
  locusTag: string;
  nodeId: string;
  node: PPINetworkNode;
  expandedAt: number; // timestamp
  level: number; // depth level (0 = original, 1 = first expansion, etc.)
}

/**
 * Represents the complete expansion path/history
 */
export interface ExpansionPath {
  nodes: ExpansionPathNode[];
  currentLevel: number;
}

/**
 * Data fetched for a node expansion
 */
export interface ExpansionData {
  nodes: PPINetworkNode[];
  edges: PPINetworkEdge[];
}

/**
 * State for managing network expansions
 */
export interface ExpansionState {
  path: ExpansionPath;
  expandedNodes: Map<string, ExpansionData>; // locusTag -> expansion data
  expandedNodeIds: Set<string>; // Set of all node IDs that have been expanded
  allExpandedNodes: Map<string, PPINetworkNode & { expansionLevel?: number }>; // All nodes including expansions
  allExpandedEdges: PPINetworkEdge[]; // All edges including expansions
}

