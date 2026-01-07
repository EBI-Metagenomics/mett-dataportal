import { ExpansionState } from '../types/expansion';
import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import cytoscape from 'cytoscape';

/**
 * Export expansion path as JSON
 */
export const exportExpansionPathJSON = (
  expansionState: ExpansionState,
  originalNodes: PPINetworkNode[],
  originalEdges: PPINetworkEdge[]
): void => {
  const exportData = {
    expansionPath: expansionState.path.nodes.map(node => ({
      locusTag: node.locusTag,
      nodeId: node.nodeId,
      level: node.level,
      expandedAt: new Date(node.expandedAt).toISOString(),
      nodeInfo: {
        name: node.node.name,
        product: node.node.product,
        uniprotId: node.node.id,
      },
    })),
    totalNodes: expansionState.allExpandedNodes.size,
    totalEdges: expansionState.allExpandedEdges.length,
    originalNodeCount: originalNodes.length,
    originalEdgeCount: originalEdges.length,
    exportedAt: new Date().toISOString(),
  };

  const jsonStr = JSON.stringify(exportData, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `network-expansion-path-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Export network visualization as PNG image
 */
export const exportNetworkImage = (
  cy: cytoscape.Core,
  filename?: string
): void => {
  try {
    // Fit to all elements before exporting
    cy.fit(undefined, 50);
    
    // Get PNG data
    const pngData = cy.png({
      output: 'blob-promise',
      bg: 'white',
      full: true, // Export full graph, not just visible viewport
    });

    pngData.then((blob: Blob) => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || `network-${new Date().toISOString().split('T')[0]}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }).catch((error: Error) => {
      console.error('Error exporting network image:', error);
      alert('Failed to export network image. Please try again.');
    });
  } catch (error) {
    console.error('Error exporting network image:', error);
    alert('Failed to export network image. Please try again.');
  }
};

