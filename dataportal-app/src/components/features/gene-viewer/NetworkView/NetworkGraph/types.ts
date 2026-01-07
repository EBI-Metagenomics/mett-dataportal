import { PPINetworkNode, PPINetworkEdge } from '../../../../../interfaces/PPI';
import cytoscape from 'cytoscape';

export interface NetworkGraphRef {
    resetView: () => void;
    fitToNodes: () => void;
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
    onNodeClick: (node: PPINetworkNode, event?: MouseEvent) => void;
    onEdgeClick?: (edge: PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number }, event?: MouseEvent) => void;
    selectedNode: PPINetworkNode | null;
}

