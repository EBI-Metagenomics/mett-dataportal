import cytoscape from 'cytoscape';
import { applyPositions } from '../utils/positionPreservation';
import { PreparedNode } from '../utils/prepareElements';

interface UseCytoscapeLayoutProps {
    cy: cytoscape.Core;
    preparedNodes: PreparedNode[];
    existingPositions: Map<string, { x: number; y: number }>;
    hasExpansionLevels: boolean;
    layoutRunningRef: { current: boolean };
}

/**
 * Apply layout to Cytoscape instance
 */
export const useCytoscapeLayout = ({
    cy,
    preparedNodes,
    existingPositions,
    hasExpansionLevels,
    layoutRunningRef,
}: UseCytoscapeLayoutProps): void => {
    if (!cy) return;

    if (hasExpansionLevels) {
        // Set node positions and lock existing ones
        applyPositions(cy, preparedNodes, existingPositions);
        
        const hasNewNodes = preparedNodes.some(n => !existingPositions.has(n.data.id));
        
        if (hasNewNodes) {
            setTimeout(() => {
                const newNodes = cy.nodes().filter(node => {
                    return !existingPositions.has(node.id());
                });
                if (newNodes.length > 0) {
                    cy.fit(newNodes, 100);
                }
                layoutRunningRef.current = false;
            }, 50);
        } else {
            layoutRunningRef.current = false;
        }
    } else {
        // For original network: use standard COSE force-directed layout
        const layoutOptions: cytoscape.CoseLayoutOptions = {
            name: 'cose',
            animate: true,
            animationDuration: 700,
            fit: true,
            padding: 50,
            idealEdgeLength: (edge: cytoscape.EdgeSingular) => {
                const w = edge.data('weight') ?? 1;
                const len = 140 - Math.min(w, 1) * 60;
                return Math.max(70, len);
            },
            nodeRepulsion: 6000,
            nodeOverlap: 10,
            gravity: 0.15,
            numIter: 1200,
        };
        
        const layout = cy.layout(layoutOptions);

        layout.one('layoutstop', () => {
            cy.fit(undefined, 50);
            layoutRunningRef.current = false;
        });

        layout.run();
    }
};

