import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import styles from './NetworkGraph.module.scss';

interface NetworkGraphProps {
  nodes: Array<PPINetworkNode & { hasOrthologs?: boolean; orthologCount?: number; nodeType?: 'ppi' | 'ortholog' }>;
  edges: PPINetworkEdge[];
  showOrthologs: boolean;
  onNodeClick: (node: PPINetworkNode) => void;
  selectedNode: PPINetworkNode | null;
}

/**
 * NetworkGraph component - Cytoscape.js graph visualization
 */
export const NetworkGraph: React.FC<NetworkGraphProps> = ({
  nodes,
  edges,
  showOrthologs,
  onNodeClick,
  selectedNode,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    // Check if container exists and has nodes
    if (!containerRef.current || nodes.length === 0) {
      // Destroy existing instance if container is gone or no nodes
      if (cyRef.current) {
        try {
          cyRef.current.destroy();
        } catch {
          // Ignore errors during cleanup
        }
        cyRef.current = null;
      }
      return;
    }

    // Destroy existing instance before creating a new one
    if (cyRef.current) {
      try {
        cyRef.current.destroy();
      } catch {
        // Ignore errors during cleanup
      }
      cyRef.current = null;
    }

    // Small delay to ensure container is ready
    const initTimeout = setTimeout(() => {
      // Double-check container still exists
      if (!containerRef.current) return;

      // Prepare nodes data for Cytoscape
      const cyNodes = nodes.map((node) => {
        const { id, x, y, ...nodeData } = node;
        return {
          data: {
            id,
            label: node.locus_tag || node.label || id,
            ...nodeData,
          },
          position: x && y ? { x, y } : undefined,
        };
      });

      // Prepare edges data for Cytoscape
      const cyEdges = edges.map((edge, index) => {
        const edgeData = edge as PPINetworkEdge & { edgeType?: string; orthology_type?: string };
        return {
          data: {
            id: `edge-${index}`,
            source: edge.source,
            target: edge.target,
            weight: edge.weight || 1,
            edgeType: edgeData.edgeType || 'ppi',
            orthology_type: edgeData.orthology_type,
          },
        };
      });

      // Initialize Cytoscape
      try {
        const cy = cytoscape({
          container: containerRef.current,
          elements: [...cyNodes, ...cyEdges],
          style: [
            // PPI Edge styles
            {
              selector: 'edge[edgeType = "ortholog"]',
              style: {
                width: 2,
                'line-color': '#FF9800',
                'target-arrow-color': '#FF9800',
                'curve-style': 'straight',
                opacity: 0.5,
                'line-style': 'dashed',
              },
            },
            // Ortholog edge styles (dashed orange lines)
            {
              selector: 'edge',
              style: {
                width: (edge: cytoscape.EdgeSingular) => Math.sqrt(edge.data('weight') || 1) * 2,
                'line-color': '#999',
                'target-arrow-color': '#999',
                'curve-style': 'straight',
                opacity: 0.6,
              },
            },
            // Ortholog node styles (orange/diamond shape)
            {
              selector: 'node[nodeType = "ortholog"]',
              style: {
                label: 'data(label)',
                'text-valign': 'bottom',
                'text-halign': 'center',
                'text-margin-y': 8,
                'font-size': '10px',
                width: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 20 : 14),
                height: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 20 : 14),
                shape: 'diamond',
                'background-color': '#FF9800',
                'border-width': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 3 : 1),
                'border-color': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? '#FF6B6B' : '#E65100'),
              },
            },
            // PPI Node styles
            {
              selector: 'node',
              style: {
                label: 'data(label)',
                'text-valign': 'bottom',
                'text-halign': 'center',
                'text-margin-y': 8,
                'font-size': '10px',
                width: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 24 : 16),
                height: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 24 : 16),
                shape: 'ellipse',
                'background-color': (node: cytoscape.NodeSingular) => {
                  const nodeData = node.data() as { hasOrthologs?: boolean; nodeType?: string };
                  // Don't color PPI nodes green if we're showing ortholog nodes separately
                  if (nodeData.nodeType === 'ortholog') return '#FF9800';
                  if (showOrthologs && nodeData.hasOrthologs) return '#50C878';
                  return '#4A90E2';
                },
                'border-width': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 3 : 1),
                'border-color': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? '#FF6B6B' : '#333'),
              },
            },
          ],
          layout: {
            name: 'cose',
            // Force-directed layout similar to D3
            idealEdgeLength: (edge: cytoscape.EdgeSingular) => 100 / (edge.data('weight') || 1),
            nodeRepulsion: 3000,
            nodeOverlap: 20,
            nestingFactor: 0.1,
            gravity: 0.25,
            numIter: 2500,
            animate: true,
            animationDuration: 1000,
            animationEasing: 'ease-out',
          },
          userPanningEnabled: true,
          userZoomingEnabled: true,
          boxSelectionEnabled: false,
        });

        // Store cytoscape reference
        cyRef.current = cy;

        // Handle node clicks
        cy.on('tap', 'node', (event: cytoscape.EventObject) => {
          const node = event.target;
          const nodeData = node.data() as { id: string };
          // Find the original node data
          const originalNode = nodes.find((n) => n.id === nodeData.id);
          if (originalNode) {
            onNodeClick(originalNode);
          }
        });
      } catch {
        // Error initializing Cytoscape - will be handled by error state
      }
    }, 50);

    // Cleanup on unmount or dependency change
    return () => {
      clearTimeout(initTimeout);
      if (cyRef.current) {
        try {
          cyRef.current.destroy();
        } catch {
          // Ignore errors during cleanup
        }
        cyRef.current = null;
      }
    };
  }, [nodes, edges, showOrthologs, selectedNode, onNodeClick]);

  return (
    <div className={styles.graphContainer}>
      <div ref={containerRef} className={styles.cytoscapeContainer} />
    </div>
  );
};

