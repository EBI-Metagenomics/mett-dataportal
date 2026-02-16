import { useMemo } from 'react';
import cytoscape from 'cytoscape';
import { NETWORK_VIEW_CONSTANTS } from '../../constants';

const GT = NETWORK_VIEW_CONSTANTS.GRAPH_THEME;
const EW = NETWORK_VIEW_CONSTANTS.EDGE_WIDTH;
const EX = NETWORK_VIEW_CONSTANTS.EXPANSION;

interface UseCytoscapeStylesProps {
    showOrthologs: boolean;
    scoreRange: { min: number; max: number };
    currentExpansionLevel?: number;
}

/**
 * Generate Cytoscape stylesheet based on props.
 * All styling values come from constants.ts (GRAPH_THEME).
 */
export const useCytoscapeStyles = ({
    showOrthologs,
    scoreRange,
    currentExpansionLevel,
}: UseCytoscapeStylesProps): cytoscape.StylesheetJson => {
    return useMemo(() => {
        const styles = [
            {
                selector: 'edge',
                style: {
                    'curve-style': 'bezier',
                    'control-point-step-size': GT.EDGE.CONTROL_POINT_STEP_SIZE,
                    'line-color': (edge: cytoscape.EdgeSingular) => {
                        const dataSource = edge.data('dataSource') as string | undefined;
                        if (dataSource === 'stringdb') return GT.EDGE.STRINGDB_EDGE_COLOR;
                        return GT.EDGE.LOCAL_EDGE_COLOR;
                    },
                    opacity: GT.EDGE.OPACITY,
                    width: (edge: cytoscape.EdgeSingular) => {
                        const w = edge.data('weight') ?? 0;
                        if (w <= 0) return EW.MIN;
                        const { MIN, MAX, BASE_SCALE } = EW;
                        const normalized = scoreRange.max > scoreRange.min
                            ? (w - scoreRange.min) / (scoreRange.max - scoreRange.min)
                            : 0.5;
                        const scaled = MIN + (normalized * (MAX - MIN)) * BASE_SCALE;
                        return Math.min(Math.max(scaled, MIN), MAX);
                    },
                },
            },
            {
                selector: 'edge[edgeType = "ortholog"]',
                style: {
                    'line-color': GT.EDGE.ORTHOLOG_LINE_COLOR,
                    opacity: GT.EDGE.ORTHOLOG_OPACITY,
                    'line-style': 'dashed',
                    width: GT.EDGE.ORTHOLOG_WIDTH,
                },
            },
            {
                selector: 'node',
                style: {
                    'background-color': (node: cytoscape.NodeSingular) => {
                        const nodeData = node.data();
                        if (nodeData.nodeType === 'ortholog') return GT.NODE.ORTHOLOG_COLOR;
                        if (nodeData.hasOrthologs && showOrthologs) return GT.NODE.PPI_WITH_ORTHOLOGS_COLOR;
                        return GT.NODE.PPI_COLOR;
                    },
                    'border-color': GT.NODE.BORDER_COLOR,
                    'border-width': GT.NODE.BORDER_WIDTH,
                    width: GT.NODE.WIDTH,
                    height: GT.NODE.HEIGHT,
                    shape: (node: cytoscape.NodeSingular) => {
                        const nodeData = node.data();
                        return nodeData.nodeType === 'ortholog' ? 'diamond' : 'ellipse';
                    },
                    label: 'data(label)',
                    'font-size': GT.NODE.FONT_SIZE,
                    'text-valign': 'bottom',
                    'text-margin-y': GT.NODE.TEXT_MARGIN_Y,
                    'text-max-width': GT.NODE.TEXT_MAX_WIDTH,
                    'text-wrap': 'ellipsis',
                    'text-opacity': 0,
                },
            },
            {
                selector: '.faded',
                style: {
                    opacity: GT.FADED.OPACITY,
                    'text-opacity': GT.FADED.TEXT_OPACITY,
                },
            },
            {
                selector: 'node[inPath = "true"]',
                style: {
                    opacity: GT.PATH.NODE_OPACITY,
                    'text-opacity': 1,
                },
            },
            {
                selector: 'edge[inPath = "true"]',
                style: {
                    opacity: GT.PATH.EDGE_OPACITY,
                    'text-opacity': 1,
                },
            },
            ...(currentExpansionLevel !== undefined && currentExpansionLevel > 0 ? [{
                selector: `node[expansionLevel = "${currentExpansionLevel}"]`,
                style: {
                    'border-width': EX.EXPANDED_NODE_BORDER_WIDTH,
                    'border-color': EX.EXPANDED_NODE_BORDER_COLOR,
                    width: GT.NODE.WIDTH * EX.EXPANDED_NODE_SIZE_MULTIPLIER,
                    height: GT.NODE.HEIGHT * EX.EXPANDED_NODE_SIZE_MULTIPLIER,
                    'font-weight': 'bold' as const,
                },
            }] : []),
            {
                selector: 'node[expansionLevel]',
                style: {
                    'border-width': (node: cytoscape.NodeSingular) => {
                        const level = node.data('expansionLevel') as number | undefined;
                        if (level === undefined) return GT.NODE.BORDER_WIDTH;
                        if (level === currentExpansionLevel) return EX.EXPANDED_NODE_BORDER_WIDTH;
                        return GT.NODE.BORDER_WIDTH;
                    },
                    'border-color': (node: cytoscape.NodeSingular) => {
                        const level = node.data('expansionLevel') as number | undefined;
                        if (level === undefined) return GT.NODE.BORDER_COLOR;
                        if (level === currentExpansionLevel) return EX.EXPANDED_NODE_BORDER_COLOR;
                        return GT.PREVIOUS_EXPANSION.BORDER_COLOR;
                    },
                    opacity: (node: cytoscape.NodeSingular) => {
                        const level = node.data('expansionLevel') as number | undefined;
                        if (level === undefined) return 1;
                        if (level === currentExpansionLevel) return 1;
                        return GT.PREVIOUS_EXPANSION.NODE_OPACITY;
                    },
                },
            },
            {
                selector: 'edge[expansionLevel]',
                style: {
                    'line-color': (edge: cytoscape.EdgeSingular) => {
                        const dataSource = edge.data('dataSource') as string | undefined;
                        if (dataSource === 'stringdb') return GT.EDGE.STRINGDB_EDGE_COLOR;
                        if (dataSource === 'local') return GT.EDGE.LOCAL_EDGE_COLOR;
                        const level = edge.data('expansionLevel') as number | undefined;
                        if (level === undefined || level === 0) return '#999';
                        const colors = EX.LEVEL_COLORS;
                        return colors[Math.min(level, colors.length - 1)] || '#999';
                    },
                    'line-width': GT.EXPANSION_EDGE.LINE_WIDTH,
                    opacity: GT.EXPANSION_EDGE.OPACITY,
                },
            },
            {
                selector: 'edge.selected',
                style: {
                    'line-width': GT.SELECTED_EDGE.LINE_WIDTH,
                    opacity: GT.SELECTED_EDGE.OPACITY,
                    'line-color': GT.SELECTED_EDGE.LINE_COLOR,
                    'z-index': GT.SELECTED_EDGE.Z_INDEX,
                },
            },
        ];

        return styles as cytoscape.StylesheetJson;
    }, [showOrthologs, scoreRange, currentExpansionLevel]);
};

