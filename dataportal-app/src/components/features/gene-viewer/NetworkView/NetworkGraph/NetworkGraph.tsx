import React, {
    useEffect,
    useRef,
    useImperativeHandle,
    forwardRef,
    useMemo,
} from 'react';
import cytoscape from 'cytoscape';
import {PPINetworkNode, PPINetworkEdge} from '../../../../../interfaces/PPI';
import styles from './NetworkGraph.module.scss';

export interface NetworkGraphRef {
    resetView: () => void;
    fitToNodes: () => void;
}

interface NetworkGraphProps {
    nodes: Array<
        PPINetworkNode & {
        hasOrthologs?: boolean;
        orthologCount?: number;
        nodeType?: 'ppi' | 'ortholog';
        x?: number;
        y?: number;
    }
    >;
    edges: Array<PPINetworkEdge & { edgeType?: string; orthology_type?: string }>;
    showOrthologs: boolean;
    onNodeClick: (node: PPINetworkNode, event?: MouseEvent) => void;
    selectedNode: PPINetworkNode | null;
}

/**
 * NetworkGraph component - Cytoscape.js graph visualization
 */
export const NetworkGraph = forwardRef<NetworkGraphRef, NetworkGraphProps>(
    ({nodes, edges, showOrthologs, onNodeClick, selectedNode}, ref) => {
        const containerRef = useRef<HTMLDivElement>(null);
        const cyRef = useRef<cytoscape.Core | null>(null);
        const layoutRunningRef = useRef(false);

        // Styles depend on showOrthologs, so memoize to avoid recreation noise
        const cyStyles = useMemo<cytoscape.StylesheetCSS[]>(() => {
            return [
                {
                    selector: 'edge',
                    style: {
                        'curve-style': 'bezier',
                        'control-point-step-size': 18,
                        'line-color': '#999',
                        opacity: 0.55,
                        width: (edge: cytoscape.EdgeSingular) => {
                            const w = edge.data('weight') ?? 1;
                            const scaled = Math.sqrt(Math.max(w, 0.01)) * 1.6;
                            return Math.min(Math.max(scaled, 1), 6);
                        },
                    },
                },

                // Ortholog edges override base
                {
                    selector: 'edge[edgeType = "ortholog"]',
                    style: {
                        'line-color': '#FF9800',
                        opacity: 0.6,
                        'line-style': 'dashed',
                        width: 2,
                    },
                },

                // Optional: if you ever add per-source edges, you can extend here
                // e.g. edge[sourceType="string_experiments"] ...

                // --------- Nodes (base) ---------
                {
                    selector: 'node',
                    style: {
                        label: 'data(label)',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'text-margin-y': 6,
                        'font-size': 10,
                        'text-wrap': 'wrap',
                        'text-max-width': 90,
                        width: 16,
                        height: 16,
                        shape: 'ellipse',
                        'background-color': (node: cytoscape.NodeSingular) => {
                            const d = node.data() as {
                                hasOrthologs?: boolean;
                                nodeType?: string;
                            };
                            if (d.nodeType === 'ortholog') return '#FF9800';
                            if (showOrthologs && d.hasOrthologs) return '#50C878';
                            return '#4A90E2';
                        },
                        'border-width': 1,
                        'border-color': '#333',
                    },
                },

                // Ortholog nodes override base
                {
                    selector: 'node[nodeType = "ortholog"]',
                    style: {
                        shape: 'diamond',
                        width: 14,
                        height: 14,
                        'border-color': '#E65100',
                    },
                },

                // Selected node via class
                {
                    selector: 'node.isSelected',
                    style: {
                        'border-width': 3,
                        'border-color': '#FF6B6B',
                        width: 24,
                        height: 24,
                        'z-index': 9999,
                    },
                },

                // Selected ortholog slightly smaller
                {
                    selector: 'node[nodeType = "ortholog"].isSelected',
                    style: {
                        width: 20,
                        height: 20,
                    },
                },

                // Fade class (optional, used by interaction pattern)
                {
                    selector: '.faded',
                    style: {
                        opacity: 0.15,
                        'text-opacity': 0.05,
                    },
                },
            ];
        }, [showOrthologs]);

        // Expose view controls to parent
        useImperativeHandle(ref, () => ({
            resetView: () => {
                if (cyRef.current) cyRef.current.fit(undefined, 50);
            },
            fitToNodes: () => {
                if (!cyRef.current) return;
                const all = cyRef.current.nodes();
                if (all.length > 0) cyRef.current.fit(all, 100);
                else cyRef.current.fit(undefined, 50);
            },
        }));

        // (Re)create Cytoscape instance when nodes/edges change
        useEffect(() => {
            // Container check + empty graph cleanup
            if (!containerRef.current || nodes.length === 0) {
                if (cyRef.current) {
                    try {
                        cyRef.current.destroy();
                    } catch {
                        // ignore cleanup errors
                    }
                    cyRef.current = null;
                }
                return;
            }

            // Destroy any existing instance before recreating
            if (cyRef.current) {
                try {
                    cyRef.current.destroy();
                } catch {
                    // ignore
                }
                cyRef.current = null;
                layoutRunningRef.current = false;
            }

            const initTimeout = setTimeout(() => {
                if (!containerRef.current) return;

                // Prepare nodes for Cytoscape
                const cyNodes = nodes.map((node) => {
                    const {id, x, y, nodeType, hasOrthologs, ...nodeData} = node as {
                        id: string;
                        x?: number;
                        y?: number;
                        nodeType?: 'ppi' | 'ortholog';
                        hasOrthologs?: boolean;
                        locus_tag?: string;
                        label?: string;
                        [key: string]: unknown;
                    };
                    return {
                        data: {
                            id,
                            label: node.locus_tag || node.label || id,
                            nodeType: nodeType || 'ppi', // Explicitly preserve nodeType
                            hasOrthologs: hasOrthologs || false,
                            ...nodeData,
                        },
                        // IMPORTANT: allow x or y = 0
                        position:
                            x !== undefined && y !== undefined ? {x, y} : undefined,
                    };
                });

                // Prepare edges for Cytoscape
                const cyEdges = edges.map((edge, index) => {
                    const edgeData = edge as PPINetworkEdge & {
                        edgeType?: string;
                        orthology_type?: string;
                        weight?: number;
                    };

                    return {
                        data: {
                            id: edgeData.id || `edge-${index}`,
                            source: edge.source,
                            target: edge.target,
                            weight: edge.weight ?? 1,
                            edgeType: edgeData.edgeType || 'ppi',
                            orthology_type: edgeData.orthology_type,
                        },
                    };
                });

                try {
                    const cy = cytoscape({
                        container: containerRef.current,
                        elements: [...cyNodes, ...cyEdges],
                        style: cyStyles,
                        userPanningEnabled: true,
                        userZoomingEnabled: true,
                        boxSelectionEnabled: false,
                        wheelSensitivity: 0.2,
                    });

                    cyRef.current = cy;
                    layoutRunningRef.current = true;

                    // Better COSE defaults for PPI networks
                    const layout = cy.layout({
                        name: 'cose',
                        animate: true,
                        animationDuration: 700,
                        fit: true,
                        padding: 50,
                        // Keep edge lengths sane; don't collapse high-weight edges into hairballs
                        idealEdgeLength: (edge: cytoscape.EdgeSingular) => {
                            const w = edge.data('weight') ?? 1;
                            // If weight is higher, make it slightly shorter, but not tiny
                            const len = 140 - Math.min(w, 1) * 60;
                            return Math.max(70, len);
                        },
                        nodeRepulsion: 6000,
                        nodeOverlap: 10,
                        gravity: 0.15,
                        numIter: 1200,
                    });

                    layout.one('layoutstop', () => {
                        cy.fit(undefined, 50);
                        layoutRunningRef.current = false;
                    });

                    layout.run();

                    // Node click handler
                    cy.on('tap', 'node', (event: cytoscape.EventObject) => {
                        const tapped = event.target as cytoscape.NodeSingular;
                        const nodeData = tapped.data() as { id: string };

                        // Optional: fade others to highlight neighborhood
                        cy.batch(() => {
                            cy.elements().removeClass('faded');
                            cy.elements().addClass('faded');

                            tapped.removeClass('faded');
                            tapped.connectedEdges().removeClass('faded');
                            tapped.connectedEdges().connectedNodes().removeClass('faded');
                        });

                        // Find original node object (for your metadata panel)
                        const original = nodes.find((n) => n.id === nodeData.id);
                        if (original) {
                            const originalEvent = event.originalEvent as MouseEvent | undefined;
                            onNodeClick(original, originalEvent);
                        }
                    });

                    // Background click: remove fading (optional)
                    cy.on('tap', (event: cytoscape.EventObject) => {
                        if (event.target === cy) {
                            cy.elements().removeClass('faded');
                        }
                    });

                    // Reduce label clutter at low zoom
                    // When orthologs are shown, always show labels for PPI nodes
                    cy.on('zoom', () => {
                        const z = cy.zoom();
                        cy.nodes().forEach(node => {
                            const nodeData = node.data();
                            const isPPI = nodeData.nodeType === 'ppi';
                            const isOrtholog = nodeData.nodeType === 'ortholog';
                            
                            if (showOrthologs && isPPI) {
                                // Always show labels for PPI nodes when orthologs are visible
                                node.style('text-opacity', 1);
                            } else if (isOrtholog) {
                                // Hide ortholog node labels to reduce clutter
                                node.style('text-opacity', 0);
                            } else {
                                // Regular PPI nodes without orthologs - show at higher zoom
                                node.style('text-opacity', z > 0.9 ? 1 : 0);
                            }
                        });
                    });
                    
                    // Trigger initial label visibility
                    cy.trigger('zoom');
                } catch {
                    // Initialization errors are swallowed; you can add a UI error state if desired.
                }
            }, 50);

            return () => {
                clearTimeout(initTimeout);
                if (cyRef.current) {
                    try {
                        cyRef.current.destroy();
                    } catch {
                        // ignore
                    }
                    cyRef.current = null;
                    layoutRunningRef.current = false;
                }
            };
            // IMPORTANT: do NOT depend on selectedNode here (avoid graph recreation)
            // showOrthologs is included because it affects node labeling logic
        }, [nodes, edges, cyStyles, onNodeClick, showOrthologs]);

        // Update label visibility when showOrthologs changes
        useEffect(() => {
            const cy = cyRef.current;
            if (!cy) return;
            
            // Trigger zoom to update label visibility based on showOrthologs
            cy.trigger('zoom');
        }, [showOrthologs]);

        // Update selection class when selectedNode changes (no graph recreation)
        useEffect(() => {
            const cy = cyRef.current;
            if (!cy) return;

            cy.batch(() => {
                cy.nodes().removeClass('isSelected');
                if (selectedNode?.id) {
                    const el = cy.getElementById(selectedNode.id);
                    if (el && el.nonempty()) el.addClass('isSelected');
                }
            });
        }, [selectedNode?.id]);

        return (
            <div className={styles.graphContainer}>
                <div ref={containerRef} className={styles.cytoscapeContainer}/>
            </div>
        );
    }
);

NetworkGraph.displayName = 'NetworkGraph';
  