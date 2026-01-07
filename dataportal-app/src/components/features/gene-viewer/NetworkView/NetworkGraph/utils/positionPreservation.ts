import cytoscape from 'cytoscape';

/**
 * Preserve existing node positions from a Cytoscape instance
 */
export const preservePositions = (cy: cytoscape.Core | null): Map<string, { x: number; y: number }> => {
    const positions = new Map<string, { x: number; y: number }>();
    if (cy) {
        try {
            cy.nodes().forEach((node) => {
                const pos = node.position();
                if (pos) {
                    positions.set(node.id(), { x: pos.x, y: pos.y });
                }
            });
        } catch {
            // Ignore errors
        }
    }
    return positions;
};

/**
 * Apply positions to Cytoscape nodes and lock existing ones
 */
export const applyPositions = (
    cy: cytoscape.Core,
    preparedNodes: Array<{ data: { id: string }; position?: { x: number; y: number } }>,
    existingPositions: Map<string, { x: number; y: number }>
): void => {
    cy.batch(() => {
        preparedNodes.forEach((nodeData) => {
            if (nodeData.position) {
                const cyNode = cy.getElementById(nodeData.data.id);
                if (cyNode && cyNode.length > 0) {
                    cyNode.position(nodeData.position);
                    // Lock position for nodes that existed before (prevent shuffling)
                    if (existingPositions.has(nodeData.data.id)) {
                        cyNode.lock();
                    }
                }
            }
        });
        
        // Unlock new nodes
        cy.nodes().forEach(node => {
            if (!existingPositions.has(node.id())) {
                node.unlock();
            }
        });
    });
};

