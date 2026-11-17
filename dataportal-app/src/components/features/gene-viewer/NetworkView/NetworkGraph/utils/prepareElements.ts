import { NETWORK_VIEW_CONSTANTS } from '../../constants';
import type { NetworkGraphProps } from '../types';

/**
 * Prefer a short gene name on the graph; fall back to locus tag when name is blank.
 */
export const getNodeDisplayLabel = (node: {
    id?: string;
    name?: string | null;
    string_preferred_name?: string | null;
    locus_tag?: string | null;
    label?: string | null;
}): string => {
    const name = typeof node.name === 'string' ? node.name.trim() : '';
    if (name) return name;

    const preferred =
        typeof node.string_preferred_name === 'string'
            ? node.string_preferred_name.trim()
            : '';
    if (preferred) return preferred;

    const locus = typeof node.locus_tag === 'string' ? node.locus_tag.trim() : '';
    if (locus) return locus;

    const label = typeof node.label === 'string' ? node.label.trim() : '';
    if (label) return label;

    return String(node.id ?? '');
};

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
        pair_id?: string;
        consensus_score?: number;
        raw_consensus_score?: number;
        n_evidence_types?: number;
        n_networks_total?: number;
        evidence_scores?: Record<string, number>;
        network_counts?: Record<string, number>;
        score_type?: string;
        dataSource?: string;
        evidence_type?: string;
        evidence_channel?: string;
    };
}

/**
 * Prepare nodes for Cytoscape with hierarchical positioning
 */
const anchorFlag = (id: string, locusTag: string | undefined, focalNodeId?: string | null): string => {
    if (!focalNodeId) return 'false';
    const focal = String(focalNodeId);
    return id === focal || locusTag === focal ? 'true' : 'false';
};

export const prepareNodes = (
    nodes: NetworkGraphProps['nodes'],
    pathNodeIds: Set<string>,
    existingPositions: Map<string, { x: number; y: number }>,
    hasExpansionLevels: boolean,
    focalNodeId?: string | null,
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
        const displayLabel = getNodeDisplayLabel({
            id,
            name: node.name as string | undefined,
            string_preferred_name: node.string_preferred_name as string | undefined,
            locus_tag: node.locus_tag,
            label: node.label,
        });
        const locus = typeof node.locus_tag === 'string' ? node.locus_tag.trim() : '';
        const fullLabel =
            displayLabel && locus && displayLabel !== locus
                ? `${displayLabel} (${locus})`
                : displayLabel || locus || id;

        return {
            data: {
                id,
                nodeType: nodeType || 'ppi',
                hasOrthologs: hasOrthologs || false,
                expansionLevel: expansionLevel,
                inPath: inPath ? 'true' : 'false',
                ...nodeData,
                isAnchor: anchorFlag(id, locus, focalNodeId),
                // Keep computed display label last so source `label` cannot overwrite it
                label: displayLabel,
                fullLabel,
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
            dataSource?: string;
            evidence_type?: string;
            evidence_channel?: string;
            pair_id?: string;
            consensus_score?: number;
            raw_consensus_score?: number;
            n_evidence_types?: number;
            n_networks_total?: number;
            evidence_scores?: Record<string, number>;
            network_counts?: Record<string, number>;
            score_type?: string;
        };

        const sourceInPath = pathNodeIds.has(edge.source);
        const targetInPath = pathNodeIds.has(edge.target);
        const edgeInPath = sourceInPath && targetInPath;
        const dataSource = edgeData.dataSource ?? 'local';
        const edgeId =
            edgeData.id || `${dataSource}-${edge.source}-${edge.target}-${index}`;

        return {
            data: {
                id: edgeId,
                source: edge.source,
                target: edge.target,
                // Selected score. Zero stays zero so a missing category is not drawn as a strong edge.
                weight: edge.weight ?? 0,
                edgeType: edgeData.edgeType || 'ppi',
                orthology_type: edgeData.orthology_type,
                expansionLevel: edgeData.expansionLevel,
                dataSource,
                evidence_type: edgeData.evidence_type,
                evidence_channel: edgeData.evidence_channel,
                pair_id: edgeData.pair_id,
                consensus_score: edgeData.consensus_score,
                raw_consensus_score: edgeData.raw_consensus_score,
                n_evidence_types: edgeData.n_evidence_types,
                n_networks_total: edgeData.n_networks_total,
                evidence_scores: edgeData.evidence_scores,
                network_counts: edgeData.network_counts,
                score_type: edgeData.score_type,
                inPath: edgeInPath ? 'true' : 'false',
            },
        };
    });
};


