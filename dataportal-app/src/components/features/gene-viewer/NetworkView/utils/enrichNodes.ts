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

    // Process orthologs and create nodes/edges
    orthologMap.forEach((orthologs, sourceLocusTag) => {
      // Find the source PPI node ID (could be locus_tag or uniprot_id)
      const sourceNode = ppiNodes.find(n => n.locus_tag === sourceLocusTag);
      if (!sourceNode) return; // Skip if source node not found

      orthologs.forEach((ortholog) => {
        const orthologLocusTag = ortholog.locus_tag_b;
        
        // Create ortholog node if it doesn't exist and isn't already a PPI node
        if (!orthologNodeMap.has(orthologLocusTag) && 
            !ppiNodes.find(n => n.locus_tag === orthologLocusTag)) {
          orthologNodeMap.set(orthologLocusTag, {
            id: orthologLocusTag,
            label: orthologLocusTag,
            locus_tag: orthologLocusTag,
            nodeType: 'ortholog',
          });
        }

        // Create edge from PPI node to ortholog node (use node IDs)
        const targetNodeId = orthologNodeMap.get(orthologLocusTag)?.id || orthologLocusTag;
        orthologEdges.push({
          source: sourceNode.id,
          target: targetNodeId,
          weight: ortholog.confidence_score || 1,
          edgeType: 'ortholog',
          orthology_type: ortholog.orthology_type,
        } as PPINetworkEdge & { edgeType: string; orthology_type?: string });
      });
    });

    return {
      enrichedNodes: [...ppiNodes, ...Array.from(orthologNodeMap.values())],
      enrichedEdges: [...networkData.edges, ...orthologEdges],
    };
  }

  return {
    enrichedNodes: ppiNodes.map(n => ({ ...n, nodeType: 'ppi' as const })),
    enrichedEdges: networkData.edges,
  };
};

