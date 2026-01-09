import cytoscape from 'cytoscape';
import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import { calculateNormalizedDegreeCentrality, getCentralityTier } from './centrality';

export interface GlobalCloudLayoutConfig {
  /** Center X coordinate for the cloud layout */
  centerX: number;
  /** Center Y coordinate for the cloud layout */
  centerY: number;
  /** Base radius for the outermost tier */
  baseRadius: number;
  /** Radius increment per tier (moving inward) */
  tierRadiusIncrement: number;
  /** Number of centrality tiers */
  numTiers: number;
  /** Angle spread for node distribution (in radians, e.g., 2π for full circle) */
  angleSpread: number;
  /** Minimum distance between nodes in the same tier */
  minNodeDistance: number;
}

const DEFAULT_CONFIG: GlobalCloudLayoutConfig = {
  centerX: 800,
  centerY: 600,
  baseRadius: 500, // Increased for better distribution
  tierRadiusIncrement: 100, // Increased spacing between tiers
  numTiers: 8, // More tiers for better granularity
  angleSpread: Math.PI * 2, // Full circle
  minNodeDistance: 35, // Increased minimum distance
};

/**
 * Calculate positions for nodes in a global cloud layout
 * Nodes are positioned in concentric rings based on their centrality:
 * - High centrality (highly connected) = inner rings (closer to center)
 * - Low centrality (less connected) = outer rings
 */
export function calculateGlobalCloudPositions(
  nodes: PPINetworkNode[],
  edges: PPINetworkEdge[],
  config: Partial<GlobalCloudLayoutConfig> = {}
): Map<string, { x: number; y: number }> {
  const layoutConfig = { ...DEFAULT_CONFIG, ...config };
  
  // Calculate centrality for each node
  const centralityMap = calculateNormalizedDegreeCentrality(nodes, edges);
  
  // Group nodes by tier
  const nodesByTier = new Map<number, PPINetworkNode[]>();
  nodes.forEach(node => {
    const centrality = centralityMap.get(node.id) || 0;
    const tier = getCentralityTier(centrality, layoutConfig.numTiers);
    
    if (!nodesByTier.has(tier)) {
      nodesByTier.set(tier, []);
    }
    nodesByTier.get(tier)!.push(node);
  });
  
  // Calculate positions
  const positions = new Map<string, { x: number; y: number }>();
  
  // Process tiers from inner (high centrality) to outer (low centrality)
  // Sort tiers descending so we process innermost (highest tier) first
  const sortedTiers = Array.from(nodesByTier.keys()).sort((a, b) => b - a);
  
  sortedTiers.forEach(tier => {
    const tierNodes = nodesByTier.get(tier)!;
    
    // Improved radius calculation for better distribution
    // Higher tier index = higher centrality = closer to center
    // Use a logarithmic scale for better spacing
    const innerRadius = 60; // Minimum radius from center for highest centrality nodes
    const radiusRange = layoutConfig.baseRadius - innerRadius;
    
    // Use exponential distribution: tiers closer to center get more space
    // This prevents overcrowding in the center
    const tierRatio = tier / (layoutConfig.numTiers - 1);
    const exponentialRatio = Math.pow(tierRatio, 0.7); // 0.7 gives a nice curve
    const tierRadius = innerRadius + (radiusRange * (1 - exponentialRatio));
    
    // Better angle distribution: use golden angle for more uniform spacing
    const goldenAngle = Math.PI * (3 - Math.sqrt(5)); // Golden angle in radians
    
    tierNodes.forEach((node, index) => {
      // Use golden angle spiral for better distribution
      const angle = (index * goldenAngle) % layoutConfig.angleSpread;
      
      // Add small random jitter for organic appearance (reduced from 0.1 to 0.05)
      const angleJitter = (Math.random() - 0.5) * (layoutConfig.angleSpread / tierNodes.length * 0.05);
      const finalAngle = angle + angleJitter;
      
      // Add radial jitter but keep it within tier bounds
      const radialJitter = (Math.random() - 0.5) * (layoutConfig.tierRadiusIncrement * 0.2);
      const radius = Math.max(innerRadius * 0.5, tierRadius + radialJitter);
      
      const x = layoutConfig.centerX + radius * Math.cos(finalAngle);
      const y = layoutConfig.centerY + radius * Math.sin(finalAngle);
      
      positions.set(node.id, { x, y });
    });
  });
  
  return positions;
}

/**
 * Apply global cloud layout to Cytoscape instance
 */
export function applyGlobalCloudLayout(
  cy: cytoscape.Core,
  positions: Map<string, { x: number; y: number }>,
  animate: boolean = true
): void {
  cy.batch(() => {
    cy.nodes().forEach(node => {
      const pos = positions.get(node.id());
      if (pos) {
        node.position(pos);
      }
    });
  });
  
  // Use preset layout to maintain positions
  // Convert positions map to function that takes node ID string
  const positionMap: Record<string, { x: number; y: number }> = {};
  positions.forEach((pos, nodeId) => {
    positionMap[nodeId] = pos;
  });
  
  const layout = cy.layout({
    name: 'preset',
    positions: (nodeId: string) => positionMap[nodeId],
    animate,
    animationDuration: animate ? 1000 : 0,
    fit: true,
    padding: 50,
  });
  
  layout.run();
}
