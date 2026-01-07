import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import { ExpansionState, ExpansionPathNode, ExpansionData } from '../types/expansion';
export type { ExpansionState } from '../types/expansion';
import { NETWORK_VIEW_CONSTANTS } from '../constants';

/**
 * Create initial expansion state
 */
export const createInitialExpansionState = (): ExpansionState => ({
  path: { nodes: [], currentLevel: 0 },
  expandedNodes: new Map(),
  expandedNodeIds: new Set(),
  allExpandedNodes: new Map(),
  allExpandedEdges: [],
});

/**
 * Check if a node can be expanded (within depth limit)
 */
export const canExpandNode = (currentLevel: number): boolean => {
  return currentLevel < NETWORK_VIEW_CONSTANTS.MAX_EXPANSION_DEPTH;
};

/**
 * Get the expansion level for a node
 */
export const getNodeExpansionLevel = (
  state: ExpansionState,
  nodeId: string
): number | undefined => {
  const pathNode = state.path.nodes.find(n => n.nodeId === nodeId);
  return pathNode?.level;
};

/**
 * Check if a node has been expanded
 */
export const isNodeExpanded = (state: ExpansionState, locusTag: string): boolean => {
  return state.expandedNodes.has(locusTag);
};

/**
 * Merge expansion data into the network
 * Handles one-to-many edges by keeping the highest scoring edge
 */
export const mergeExpansionData = (
  currentState: ExpansionState,
  expansionData: ExpansionData,
  expandingNode: PPINetworkNode,
  level: number
): ExpansionState => {
  const newNodes = new Map(currentState.allExpandedNodes);
  const edgeMap = new Map<string, PPINetworkEdge>(); // source-target -> edge

  // Index existing edges
  currentState.allExpandedEdges.forEach(edge => {
    const key = `${edge.source}-${edge.target}`;
    const existing = edgeMap.get(key);
    if (!existing || (edge.weight ?? 0) > (existing.weight ?? 0)) {
      edgeMap.set(key, edge);
    }
  });

  // Add new nodes with expansion level metadata
  expansionData.nodes.forEach(node => {
    if (!newNodes.has(node.id)) {
      newNodes.set(node.id, {
        ...node,
        expansionLevel: level,
      });
    }
  });

  // Add new edges, merging with existing ones (keep highest weight)
  // Also tag edges with expansion level for visual styling
  expansionData.edges.forEach(edge => {
    const key = `${edge.source}-${edge.target}`;
    const existing = edgeMap.get(key);
    
    const edgeWithLevel = {
      ...edge,
      expansionLevel: level,
    } as PPINetworkEdge & { expansionLevel?: number };
    
    if (!existing || (edge.weight ?? 0) > (existing.weight ?? 0)) {
      edgeMap.set(key, edgeWithLevel);
    } else if (existing) {
      // Keep existing but update level if this edge is from a higher level
      const existingLevel = (existing as PPINetworkEdge & { expansionLevel?: number }).expansionLevel;
      if (existingLevel === undefined || level > existingLevel) {
        edgeMap.set(key, edgeWithLevel);
      }
    }
  });

  // Update expanded nodes tracking
  const newExpandedNodes = new Map(currentState.expandedNodes);
  newExpandedNodes.set(expandingNode.locus_tag || expandingNode.id, expansionData);

  const newExpandedNodeIds = new Set(currentState.expandedNodeIds);
  newExpandedNodeIds.add(expandingNode.id);

  // Update path
  const newPathNode: ExpansionPathNode = {
    locusTag: expandingNode.locus_tag || expandingNode.id,
    nodeId: expandingNode.id,
    node: expandingNode,
    expandedAt: Date.now(),
    level,
  };

  const newPathNodes = [...currentState.path.nodes, newPathNode];

  return {
    path: {
      nodes: newPathNodes,
      currentLevel: level,
    },
    expandedNodes: newExpandedNodes,
    expandedNodeIds: newExpandedNodeIds,
    allExpandedNodes: newNodes,
    allExpandedEdges: Array.from(edgeMap.values()),
  };
};

/**
 * Clear all expansions, returning to original state
 */
export const clearExpansions = (): ExpansionState => {
  return createInitialExpansionState();
};

/**
 * Navigate back to a specific point in the expansion path
 */
export const navigateToPathLevel = (
  state: ExpansionState,
  targetLevel: number,
  originalNodes: PPINetworkNode[],
  originalEdges: PPINetworkEdge[]
): ExpansionState => {
  // If targetLevel is -1, return to initial state (only starting node)
  if (targetLevel < -1 || targetLevel >= state.path.nodes.length) {
    return state;
  }

  if (targetLevel === -1) {
    // Return to initial state - only starting node (level 0)
    const initialState = createInitialExpansionState();
    if (state.path.nodes.length > 0) {
      const startingNode = state.path.nodes[0];
      initialState.path.nodes = [startingNode];
      initialState.path.currentLevel = 0;
      initialState.allExpandedNodes = new Map(
        originalNodes.map(node => [node.id, { ...node, expansionLevel: 0 }])
      );
      initialState.allExpandedEdges = [...originalEdges];
    }
    return initialState;
  }

  // Rebuild state from scratch up to target level
  let newState = createInitialExpansionState();
  newState.allExpandedNodes = new Map(
    originalNodes.map(node => [node.id, { ...node, expansionLevel: 0 }])
  );
  newState.allExpandedEdges = [...originalEdges];
  
  // Keep starting node in path
  if (state.path.nodes.length > 0) {
    newState.path.nodes = [state.path.nodes[0]];
  }

  // Apply expansions up to target level
  for (let i = 1; i <= targetLevel + 1 && i < state.path.nodes.length; i++) {
    const pathNode = state.path.nodes[i];
    const expansionData = state.expandedNodes.get(pathNode.locusTag);
    
    if (expansionData) {
      const expandingNode = pathNode.node;
      newState = mergeExpansionData(newState, expansionData, expandingNode, i);
      newState.path.nodes.push(pathNode);
    }
  }

  newState.path.currentLevel = targetLevel;
  return newState;
};

