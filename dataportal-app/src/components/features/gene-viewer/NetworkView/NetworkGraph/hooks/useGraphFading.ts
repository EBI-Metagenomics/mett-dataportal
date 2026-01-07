import { useEffect } from 'react';
import cytoscape from 'cytoscape';

interface UseGraphFadingProps {
    cy: cytoscape.Core | null;
    currentExpansionLevel?: number;
    pathNodeIds: Set<string>;
}

/**
 * Apply fading to old level nodes/edges not in expansion path
 */
export const useGraphFading = ({
    cy,
    currentExpansionLevel,
    pathNodeIds,
}: UseGraphFadingProps): void => {
    useEffect(() => {
        if (!cy || currentExpansionLevel === undefined || currentExpansionLevel <= 0) {
            cy?.elements().removeClass('faded');
            return;
        }

        cy.batch(() => {
            cy.elements().removeClass('faded');

            // Apply faded class to nodes from previous levels not in path
            cy.nodes().forEach((node) => {
                const level = node.data('expansionLevel') as number | undefined;
                const inPath = node.data('inPath') === 'true';
                const isCurrentLevel = level === currentExpansionLevel;
                
                if (level !== undefined && !isCurrentLevel && level < currentExpansionLevel && !inPath) {
                    node.addClass('faded');
                }
            });

            // Apply faded class to edges from previous levels not in path
            cy.edges().forEach((edge) => {
                const level = edge.data('expansionLevel') as number | undefined;
                const inPath = edge.data('inPath') === 'true';
                const isCurrentLevel = level === currentExpansionLevel;
                
                if (level !== undefined && !isCurrentLevel && level < currentExpansionLevel && !inPath) {
                    edge.addClass('faded');
                }
            });
        });
    }, [cy, currentExpansionLevel, pathNodeIds]);
};

