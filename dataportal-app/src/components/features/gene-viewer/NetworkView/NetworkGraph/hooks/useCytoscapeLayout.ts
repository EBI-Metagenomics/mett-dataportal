import cytoscape from 'cytoscape';
import { NETWORK_VIEW_CONSTANTS } from '../../constants';
import { applyPositions } from '../utils/positionPreservation';
import { PreparedNode } from '../utils/prepareElements';
import { registerCytoscapeExtensions } from '../utils/registerCytoscapeExtensions';
import { getFcoseLayoutOptions } from '../utils/getFcoseLayoutOptions';

registerCytoscapeExtensions();

interface UseCytoscapeLayoutProps {
    cy: cytoscape.Core;
    preparedNodes: PreparedNode[];
    existingPositions: Map<string, { x: number; y: number }>;
    hasExpansionLevels: boolean;
    layoutRunningRef: { current: boolean };
    focalNodeId?: string | null;
}

/**
 * Apply layout to Cytoscape instance (fCoSE for full layouts).
 */
export const useCytoscapeLayout = ({
    cy,
    preparedNodes,
    existingPositions,
    hasExpansionLevels,
    layoutRunningRef,
    focalNodeId,
}: UseCytoscapeLayoutProps): void => {
    if (!cy) return;

    if (hasExpansionLevels) {
        // Set node positions and lock existing ones
        applyPositions(cy, preparedNodes, existingPositions);

        const hasNewNodes = preparedNodes.some((n) => !existingPositions.has(n.data.id));

        if (hasNewNodes) {
            setTimeout(() => {
                const newNodes = cy.nodes().filter((node) => {
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
        const L = NETWORK_VIEW_CONSTANTS.FCOSE_LAYOUT;
        const layoutOptions = getFcoseLayoutOptions({
            focalNodeId,
            inPlace: true,
        });

        const layout = cy.layout(layoutOptions as unknown as cytoscape.LayoutOptions);

        layout.one('layoutstop', () => {
            cy.fit(undefined, L.FIT_PADDING_IN_PLACE);
            layoutRunningRef.current = false;
        });

        layout.run();
    }
};
