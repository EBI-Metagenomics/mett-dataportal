import cytoscape from 'cytoscape';
import { NETWORK_VIEW_CONSTANTS } from '../../constants';
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
        const L = NETWORK_VIEW_CONSTANTS.COSE_LAYOUT;
        const layoutOptions: cytoscape.CoseLayoutOptions = {
            name: 'cose',
            animate: true,
            animationDuration: L.ANIMATION_DURATION_IN_PLACE,
            fit: true,
            padding: L.PADDING_IN_PLACE,
            idealEdgeLength: (edge: cytoscape.EdgeSingular) => {
                const w = edge.data('weight') ?? 1;
                const len = 140 - Math.min(w, 1) * 60;
                return Math.max(70, len);
            },
            nodeRepulsion: L.NODE_REPULSION_IN_PLACE,
            nodeOverlap: L.NODE_OVERLAP_IN_PLACE,
            gravity: L.GRAVITY_IN_PLACE,
            numIter: L.NUM_ITER_IN_PLACE,
        };

        const layout = cy.layout(layoutOptions);

        layout.one('layoutstop', () => {
            cy.fit(undefined, L.FIT_PADDING_IN_PLACE);
            layoutRunningRef.current = false;
        });

        layout.run();
    }
};

