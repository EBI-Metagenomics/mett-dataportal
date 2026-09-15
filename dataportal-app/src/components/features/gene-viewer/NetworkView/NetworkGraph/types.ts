import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import cytoscape from 'cytoscape';

export interface NetworkGraphRef {
    resetView: () => void;
    fitToNodes: () => void;
    relayout: () => void;
    getCytoscapeInstance: () => cytoscape.Core | null;
}

export interface NetworkGraphProps {
    nodes: Array<
        PPINetworkNode & {
        hasOrthologs?: boolean;
        orthologCount?: number;
        nodeType?: 'ppi' | 'ortholog';
        expansionLevel?: number;
        x?: number;
        y?: number;
    }
    >;
    edges: Array<PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number }>;
    showOrthologs: boolean;
    currentExpansionLevel?: number;
    expansionPath?: Array<{ nodeId: string; level: number }>;
    /** Node id to place at center (e.g. selected gene in neighborhood view). Enables concentric layout. */
    focalNodeId?: string | null;
    onNodeClick: (node: PPINetworkNode, event?: MouseEvent) => void;
    onEdgeClick?: (edge: PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number }, event?: MouseEvent) => void;
    selectedNode: PPINetworkNode | null;
    /** Increment to force a full layout + fit (Reset). */
    layoutRevision?: number;
}

