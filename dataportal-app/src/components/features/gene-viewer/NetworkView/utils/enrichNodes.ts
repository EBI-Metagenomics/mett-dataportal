import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import { OrthologRelationship } from '../../../../../interfaces/Ortholog';

/**
 * Enrich network nodes with ortholog information and create ortholog nodes/edges
 */
export const enrichNetworkData = (
  networkData: { nodes: PPINetworkNode[]; edges: PPINetworkEdge[] } | null,
  orthologMap: Map<string, OrthologRelationship[]>,
  showOrthologs: boolean
): { enrichedNodes: Array<PPINetworkNode & { nodeType: 'ppi' | 'ortholog'; hasOrthologs?: boolean; orthologCount?: number }>; enrichedEdges: PPINetworkEdge[] } => {
  if (!networkData?.nodes) {
    return { enrichedNodes: [], enrichedEdges: networkData?.edges || [] };
  }

  const ppiNodes = networkData.nodes.map((node) => {
    const orthologs = node.locus_tag ? orthologMap.get(node.locus_tag) || [] : [];
    return {
      ...node,
      hasOrthologs: orthologs.length > 0,
      orthologCount: orthologs.length,
      nodeType: 'ppi' as const,
    };
  });

  // If showOrthologs is enabled, add ortholog nodes and edges
  if (showOrthologs && orthologMap.size > 0) {
    const orthologNodeMap = new Map<string, PPINetworkNode & { nodeType: 'ortholog' }>();
    const orthologEdges: PPINetworkEdge[] = [];
    // Track ortholog edges between PPI nodes (to avoid duplicates)
    const ppiOrthologEdgeKeys = new Set<string>();
    // Track how many PPI nodes each ortholog is connected to
    const orthologConnectionCount = new Map<string, number>();

    // First pass: collect and count ortholog connections
    // Also identify ortholog relationships between PPI nodes
    orthologMap.forEach((orthologs, sourceLocusTag) => {
      const sourceNode = ppiNodes.find(n => n.locus_tag === sourceLocusTag);
      if (!sourceNode) return;

      orthologs.forEach((ortholog) => {
        const orthologLocusTag = ortholog.locus_tag_b;
        const targetPPINode = ppiNodes.find(n => n.locus_tag === orthologLocusTag);
        
        if (targetPPINode) {
          // This ortholog is another PPI node - create ortholog edge between PPI nodes
          // Create edge key to avoid duplicates (bidirectional)
          const edgeKey1 = `${sourceNode.id}-${targetPPINode.id}`;
          const edgeKey2 = `${targetPPINode.id}-${sourceNode.id}`;
          
          if (!ppiOrthologEdgeKeys.has(edgeKey1) && !ppiOrthologEdgeKeys.has(edgeKey2)) {
            orthologEdges.push({
              source: sourceNode.id,
              target: targetPPINode.id,
              weight: ortholog.confidence_score || 1,
              edgeType: 'ortholog',
              orthology_type: ortholog.orthology_type,
            } as PPINetworkEdge & { edgeType: string; orthology_type?: string });
            ppiOrthologEdgeKeys.add(edgeKey1);
          }
        } else {
          // This ortholog is not a PPI node - track for creating ortholog nodes
          orthologConnectionCount.set(
            orthologLocusTag,
            (orthologConnectionCount.get(orthologLocusTag) || 0) + 1
          );
        }
      });
    });

    // Second pass: create ortholog nodes for non-PPI orthologs
    // Prioritize orthologs shared by multiple PPI nodes
    orthologMap.forEach((orthologs, sourceLocusTag) => {
      const sourceNode = ppiNodes.find(n => n.locus_tag === sourceLocusTag);
      if (!sourceNode) return;

      // Filter and sort orthologs: prefer 1:1, then by confidence, limit to top 3 per node
      const filteredOrthologs = [...orthologs]
        .filter(ortholog => {
          const orthologLocusTag = ortholog.locus_tag_b;
          // Skip if already a PPI node (we handled those in first pass)
          if (ppiNodes.find(n => n.locus_tag === orthologLocusTag)) {
            return false;
          }
          // Only include if we tracked this ortholog in the first pass
          return orthologConnectionCount.has(orthologLocusTag);
        })
        .sort((a, b) => {
          // Prefer orthologs shared by more PPI nodes, then 1:1, then confidence
          const aConnections = orthologConnectionCount.get(a.locus_tag_b) || 0;
          const bConnections = orthologConnectionCount.get(b.locus_tag_b) || 0;
          if (aConnections !== bConnections) {
            return bConnections - aConnections;
          }
          const aIsOneToOne = a.orthology_type === '1:1' ? 1 : 0;
          const bIsOneToOne = b.orthology_type === '1:1' ? 1 : 0;
          if (aIsOneToOne !== bIsOneToOne) {
            return bIsOneToOne - aIsOneToOne;
          }
          return (b.confidence_score || 0) - (a.confidence_score || 0);
        })
        .slice(0, 3); // Limit to top 3 per PPI node

      filteredOrthologs.forEach((ortholog) => {
        const orthologLocusTag = ortholog.locus_tag_b;
        
        // Create ortholog node if it doesn't exist
        if (!orthologNodeMap.has(orthologLocusTag)) {
          orthologNodeMap.set(orthologLocusTag, {
            id: orthologLocusTag,
            label: orthologLocusTag,
            locus_tag: orthologLocusTag,
            nodeType: 'ortholog',
          });
        }

        // Create edge from PPI node to ortholog node
        const targetNode = orthologNodeMap.get(orthologLocusTag);
        if (targetNode) {
          orthologEdges.push({
            source: sourceNode.id,
            target: targetNode.id,
            weight: ortholog.confidence_score || 1,
            edgeType: 'ortholog',
            orthology_type: ortholog.orthology_type,
          } as PPINetworkEdge & { edgeType: string; orthology_type?: string });
        }
      });
    });

    // Only include ortholog nodes that have at least one edge connecting them
    // This prevents orphaned nodes from appearing in the graph
    const connectedOrthologIds = new Set<string>();
    orthologEdges.forEach(edge => {
      connectedOrthologIds.add(edge.target);
    });
    
    // Filter ortholog nodes to only those that are connected
    const connectedOrthologNodes = Array.from(orthologNodeMap.values()).filter(
      node => connectedOrthologIds.has(node.id)
    );

    return {
      enrichedNodes: [...ppiNodes, ...connectedOrthologNodes],
      enrichedEdges: [...networkData.edges, ...orthologEdges],
    };
  }

  return {
    enrichedNodes: ppiNodes.map(n => ({ ...n, nodeType: 'ppi' as const })),
    enrichedEdges: networkData.edges,
  };
};

