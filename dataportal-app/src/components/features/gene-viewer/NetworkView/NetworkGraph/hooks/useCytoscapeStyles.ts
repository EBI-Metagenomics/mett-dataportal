import { useMemo } from 'react';
import cytoscape from 'cytoscape';
import { NETWORK_VIEW_CONSTANTS } from '../../constants';

interface UseCytoscapeStylesProps {
    showOrthologs: boolean;
    scoreRange: { min: number; max: number };
    currentExpansionLevel?: number;
    viewMode?: 'global' | 'focused';
}

/**
 * Generate Cytoscape stylesheet based on props
 */
export const useCytoscapeStyles = ({
    showOrthologs,
    scoreRange,
    currentExpansionLevel,
    viewMode = 'focused',
}: UseCytoscapeStylesProps): cytoscape.StylesheetCSS[] => {
    return useMemo(() => {
        const styles: cytoscape.StylesheetCSS[] = [
            // Base edge styling
            {
                selector: 'edge',
                style: {
                    'curve-style': 'bezier',
                    'control-point-step-size': 18,
                    'line-color': '#999',
                    // Hide edges in global view (too cluttered)
                    opacity: viewMode === 'global' ? 0 : 0.55,
                    'transition-property': 'opacity',
                    'transition-duration': '0.2s',
                    'transition-timing-function': 'ease-out',
                    width: (edge: cytoscape.EdgeSingular) => {
                        const w = edge.data('weight') ?? 0; 
                        if (w <= 0) return NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN;
                        
                        const normalized = scoreRange.max > scoreRange.min
                            ? (w - scoreRange.min) / (scoreRange.max - scoreRange.min)
                            : 0.5;
                        
                        const scaled = NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN + 
                            (normalized * (NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MAX - NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN)) *
                            NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.BASE_SCALE;
                        
                        return Math.min(Math.max(scaled, NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN), NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MAX);
                    },
                },
            },
            
            // Ortholog edges
            {
                selector: 'edge[edgeType = "ortholog"]',
                style: {
                    'line-color': '#FF9800',
                    opacity: 0.6,
                    'line-style': 'dashed',
                    width: 2,
                },
            },
            
            // Base node styling
            {
                selector: 'node',
                style: {
                    'background-color': (node: cytoscape.NodeSingular) => {
                        const nodeData = node.data();
                        if (nodeData.nodeType === 'ortholog') return '#FF9800';
                        if (nodeData.hasOrthologs && showOrthologs) return '#50C878';
                        return '#4A90E2';
                    },
                    'border-color': '#333',
                    'border-width': 1,
                    width: 16,
                    height: 16,
                    shape: (node: cytoscape.NodeSingular) => {
                        const nodeData = node.data();
                        return nodeData.nodeType === 'ortholog' ? 'diamond' : 'ellipse';
                    },
                    label: 'data(label)',
                    'font-size': '10px',
                    // Hide labels in global view (not readable anyway)
                    'text-opacity': viewMode === 'global' ? 0 : 0,
                    'transition-property': 'text-opacity, opacity',
                    'transition-duration': '0.2s',
                    'transition-timing-function': 'ease-out',
                },
            },
            
            // Fade class
            {
                selector: '.faded',
                style: {
                    opacity: 0.2,
                    'text-opacity': 0.1,
                },
            },
            
            // Nodes in expansion path
            {
                selector: 'node[inPath = "true"]',
                style: {
                    opacity: 1,
                    'text-opacity': 1,
                },
            },
            
            // Edges connected to path nodes
            {
                selector: 'edge[inPath = "true"]',
                style: {
                    opacity: 0.7,
                    'text-opacity': 1,
                },
            },
            
            // Current expansion level nodes
            ...(currentExpansionLevel !== undefined && currentExpansionLevel > 0 ? [{
                selector: `node[expansionLevel = "${currentExpansionLevel}"]`,
                style: {
                    'border-width': NETWORK_VIEW_CONSTANTS.EXPANSION.EXPANDED_NODE_BORDER_WIDTH,
                    'border-color': NETWORK_VIEW_CONSTANTS.EXPANSION.EXPANDED_NODE_BORDER_COLOR,
                    width: 16 * NETWORK_VIEW_CONSTANTS.EXPANSION.EXPANDED_NODE_SIZE_MULTIPLIER,
                    height: 16 * NETWORK_VIEW_CONSTANTS.EXPANSION.EXPANDED_NODE_SIZE_MULTIPLIER,
                    'font-weight': 'bold',
                },
            }] : []),
            
            // Previous expansion levels
            {
                selector: 'node[expansionLevel]',
                style: {
                    'border-width': (node: cytoscape.NodeSingular) => {
                        const level = node.data('expansionLevel') as number | undefined;
                        if (level === undefined) return 1;
                        if (level === currentExpansionLevel) return NETWORK_VIEW_CONSTANTS.EXPANSION.EXPANDED_NODE_BORDER_WIDTH;
                        return 1;
                    },
                    'border-color': (node: cytoscape.NodeSingular) => {
                        const level = node.data('expansionLevel') as number | undefined;
                        if (level === undefined) return '#333';
                        if (level === currentExpansionLevel) return NETWORK_VIEW_CONSTANTS.EXPANSION.EXPANDED_NODE_BORDER_COLOR;
                        return '#ccc';
                    },
                    opacity: (node: cytoscape.NodeSingular) => {
                        const level = node.data('expansionLevel') as number | undefined;
                        if (level === undefined) return 1;
                        if (level === currentExpansionLevel) return 1;
                        return 0.7;
                    },
                },
            },
            
            // Edges with expansion level styling
            {
                selector: 'edge[expansionLevel]',
                style: {
                    'line-color': (edge: cytoscape.EdgeSingular) => {
                        const level = edge.data('expansionLevel') as number | undefined;
                        if (level === undefined || level === 0) return '#999';
                        const colors = NETWORK_VIEW_CONSTANTS.EXPANSION.LEVEL_COLORS;
                        return colors[Math.min(level, colors.length - 1)] || '#999';
                    },
                    'line-width': 2,
                    opacity: 0.7,
                },
            },
            
            // Selected edge styling
            {
                selector: 'edge.selected',
                style: {
                    'line-width': 4,
                    opacity: 1,
                    'line-color': '#FF6B6B',
                    'z-index': 999,
                },
            },
        ];
        
        return styles as cytoscape.StylesheetCSS[];
    }, [showOrthologs, scoreRange, currentExpansionLevel, viewMode]);
};

