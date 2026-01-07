import { NETWORK_VIEW_CONSTANTS } from '../../constants';
import type { NetworkGraphProps } from '../types';

export interface PreparedNode {
    data: {
        id: string;
        label: string;
        nodeType: 'ppi' | 'ortholog';
        hasOrthologs: boolean;
        expansionLevel?: number;
        inPath: string;
        [key: string]: unknown;
    };
    position?: { x: number; y: number };
}

export interface PreparedEdge {
    data: {
        id: string;
        source: string;
        target: string;
        weight: number;
        edgeType: string;
        orthology_type?: string;
        expansionLevel?: number;
        inPath: string;
    };
}

/**
 * Prepare nodes for Cytoscape with hierarchical positioning
 */
export const prepareNodes = (
    nodes: NetworkGraphProps['nodes'],
    pathNodeIds: Set<string>,
    existingPositions: Map<string, { x: number; y: number }>,
    hasExpansionLevels: boolean
): PreparedNode[] => {
    // Group nodes by expansion level
    const nodesByLevel = new Map<number, Array<typeof nodes[0]>>();
    nodes.forEach(node => {
        const level = (node as { expansionLevel?: number }).expansionLevel ?? 0;
        if (!nodesByLevel.has(level)) {
            nodesByLevel.set(level, []);
        }
        nodesByLevel.get(level)!.push(node);
    });

    return nodes.map((node) => {
        const {id, x, y, nodeType, hasOrthologs, expansionLevel, ...nodeData} = node as {
            id: string;
            x?: number;
            y?: number;
            nodeType?: 'ppi' | 'ortholog';
            hasOrthologs?: boolean;
            expansionLevel?: number;
            locus_tag?: string;
            label?: string;
            [key: string]: unknown;
        };
        
        let initialPosition: {x: number; y: number} | undefined;
        
        // First, try to use preserved position from existing graph
        const preservedPosition = existingPositions.get(id);
        if (preservedPosition) {
            initialPosition = preservedPosition;
        }
        // If we have expansion levels and no preserved position, use hierarchical radial layout
        else if (hasExpansionLevels && expansionLevel !== undefined) {
            const levelNodes = nodesByLevel.get(expansionLevel) || [];
            const nodeIndex = levelNodes.findIndex(n => n.id === node.id);
            const totalAtLevel = levelNodes.length;
            
            if (totalAtLevel > 0) {
                const radius = expansionLevel === 0 
                    ? 0
                    : NETWORK_VIEW_CONSTANTS.EXPANSION.RADIAL_LAYOUT.BASE_RADIUS + 
                      (expansionLevel - 1) * NETWORK_VIEW_CONSTANTS.EXPANSION.RADIAL_LAYOUT.LEVEL_RADIUS_INCREMENT;
                
                const angle = expansionLevel === 0
                    ? 0
                    : (nodeIndex / totalAtLevel) * NETWORK_VIEW_CONSTANTS.EXPANSION.RADIAL_LAYOUT.ANGLE_SPREAD;
                
                initialPosition = {
                    x: NETWORK_VIEW_CONSTANTS.EXPANSION.RADIAL_LAYOUT.CENTER_X + radius * Math.cos(angle),
                    y: NETWORK_VIEW_CONSTANTS.EXPANSION.RADIAL_LAYOUT.CENTER_Y + radius * Math.sin(angle),
                };
            }
        } else if (x !== undefined && y !== undefined) {
            initialPosition = { x, y };
        }
        
        const inPath = pathNodeIds.has(id);
        
        return {
            data: {
                id,
                label: node.locus_tag || node.label || id,
                nodeType: nodeType || 'ppi',
                hasOrthologs: hasOrthologs || false,
                expansionLevel: expansionLevel,
                inPath: inPath ? 'true' : 'false',
                ...nodeData,
            },
            position: initialPosition,
        };
    });
};

/**
 * Prepare edges for Cytoscape
 */
export const prepareEdges = (
    edges: NetworkGraphProps['edges'],
    pathNodeIds: Set<string>
): PreparedEdge[] => {
    return edges.map((edge, index) => {
        const edgeData = edge as NetworkGraphProps['edges'][0] & {
            edgeType?: string;
            orthology_type?: string;
            weight?: number;
            expansionLevel?: number;
        };

        const sourceInPath = pathNodeIds.has(edge.source);
        const targetInPath = pathNodeIds.has(edge.target);
        const edgeInPath = sourceInPath && targetInPath;
        
        return {
            data: {
                id: edgeData.id || `edge-${index}`,
                source: edge.source,
                target: edge.target,
                weight: edge.weight ?? 1,
                edgeType: edgeData.edgeType || 'ppi',
                orthology_type: edgeData.orthology_type,
                expansionLevel: edgeData.expansionLevel,
                inPath: edgeInPath ? 'true' : 'false',
            },
        };
    });
};


