import { useEffect, useCallback } from 'react';
import cytoscape from 'cytoscape';
import type { NetworkGraphProps } from '../types';
import type { PPINetworkNode, PPINetworkEdge } from '../../../../../../interfaces/PPI';

interface UseCytoscapeHandlersProps {
    cy: cytoscape.Core | null;
    nodes: NetworkGraphProps['nodes'];
    edges: NetworkGraphProps['edges'];
    showOrthologs: boolean;
    onNodeClick: (node: PPINetworkNode, event?: MouseEvent) => void;
    onEdgeClick?: (edge: PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number }, event?: MouseEvent) => void;
}

/**
 * Set up Cytoscape event handlers
 */
export const useCytoscapeHandlers = ({
    cy,
    nodes,
    edges,
    showOrthologs,
    onNodeClick,
    onEdgeClick,
}: UseCytoscapeHandlersProps): void => {
    // Node click handler
    const handleNodeClick = useCallback((event: cytoscape.EventObject) => {
        if (!cy) return;
        const tapped = event.target as cytoscape.NodeSingular;
        const nodeData = tapped.data() as { id: string };

        cy.batch(() => {
            cy.elements().removeClass('faded');
            cy.elements().addClass('faded');

            tapped.removeClass('faded');
            tapped.connectedEdges().removeClass('faded');
            tapped.connectedEdges().connectedNodes().removeClass('faded');
        });

        const original = nodes.find((n) => n.id === nodeData.id);
        if (original) {
            const originalEvent = event.originalEvent as MouseEvent | undefined;
            onNodeClick(original, originalEvent);
        }
    }, [cy, nodes, onNodeClick]);

    // Edge click handler
    const handleEdgeClick = useCallback((event: cytoscape.EventObject) => {
        if (!cy || !onEdgeClick) return;
        const tapped = event.target as cytoscape.EdgeSingular;
        const edgeData = tapped.data() as {
            id: string;
            source: string;
            target: string;
            weight?: number;
            edgeType?: string;
            orthology_type?: string;
            expansionLevel?: number;
        };

        cy.batch(() => {
            cy.edges().removeClass('selected');
            tapped.addClass('selected');
        });

        const originalEdge = edges.find((e) => 
            e.source === edgeData.source && e.target === edgeData.target
        );
        if (originalEdge) {
            const originalEvent = event.originalEvent as MouseEvent | undefined;
            onEdgeClick(originalEdge, originalEvent);
        }
    }, [cy, edges, onEdgeClick]);

    // Background click handler
    const handleBackgroundClick = useCallback((event: cytoscape.EventObject) => {
        if (!cy) return;
        if (event.target === cy) {
            cy.elements().removeClass('faded');
            cy.edges().removeClass('selected');
        }
    }, [cy]);

    // Zoom handler for label visibility
    const handleZoom = useCallback(() => {
        if (!cy) return;
        const z = cy.zoom();
        cy.nodes().forEach(node => {
            const nodeData = node.data();
            const isPPI = nodeData.nodeType === 'ppi';
            const isOrtholog = nodeData.nodeType === 'ortholog';
            
            if (showOrthologs && isPPI) {
                node.style('text-opacity', 1);
            } else if (isOrtholog) {
                node.style('text-opacity', 0);
            } else {
                node.style('text-opacity', z > 0.9 ? 1 : 0);
            }
        });
    }, [cy, showOrthologs]);

    // Set up event listeners
    useEffect(() => {
        if (!cy) return;

        cy.off('tap', 'node');
        cy.on('tap', 'node', handleNodeClick);
        
        cy.off('tap', 'edge');
        if (onEdgeClick) {
            cy.on('tap', 'edge', handleEdgeClick);
        }
        
        cy.off('tap');
        cy.on('tap', handleBackgroundClick);
        
        cy.off('zoom');
        cy.on('zoom', handleZoom);
        
        cy.trigger('zoom');

        return () => {
            cy.off('tap', 'node');
            cy.off('tap', 'edge');
            cy.off('tap');
            cy.off('zoom');
        };
    }, [cy, handleNodeClick, handleEdgeClick, handleBackgroundClick, handleZoom, onEdgeClick]);
};

