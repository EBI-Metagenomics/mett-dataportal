import React, {
    useEffect,
    useRef,
    useImperativeHandle,
    forwardRef,
    useMemo,
} from 'react';
import cytoscape from 'cytoscape';
import {PPINetworkNode, PPINetworkEdge} from '../../../../../interfaces/PPI';
import { NETWORK_VIEW_CONSTANTS } from '../constants';
import styles from './NetworkGraph.module.scss';

export interface NetworkGraphRef {
    resetView: () => void;
    fitToNodes: () => void;
    getCytoscapeInstance: () => cytoscape.Core | null;
}

interface NetworkGraphProps {
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
    currentExpansionLevel?: number; // Current expansion level to highlight
    expansionPath?: Array<{ nodeId: string; level: number }>; // Path of expanded nodes for trail highlighting
    onNodeClick: (node: PPINetworkNode, event?: MouseEvent) => void;
    onEdgeClick?: (edge: PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number }, event?: MouseEvent) => void;
    selectedNode: PPINetworkNode | null;
}

/**
 * NetworkGraph component - Cytoscape.js graph visualization
 */
export const NetworkGraph = forwardRef<NetworkGraphRef, NetworkGraphProps>(
    ({nodes, edges, showOrthologs, currentExpansionLevel, expansionPath = [], onNodeClick, onEdgeClick, selectedNode}, ref) => {
        // Create a set of path node IDs for quick lookup
        const pathNodeIds = useMemo(() => {
            return new Set(expansionPath.map(p => p.nodeId));
        }, [expansionPath]);
        const containerRef = useRef<HTMLDivElement>(null);
        const cyRef = useRef<cytoscape.Core | null>(null);
        const layoutRunningRef = useRef(false);

        // Calculate score range for normalization
        const scoreRange = useMemo(() => {
            if (edges.length === 0) return { min: 0, max: 1 };
            
            const weights = edges.map(e => e.weight ?? 0).filter(w => w > 0);
            if (weights.length === 0) return { min: 0, max: 1 };
            
            const min = Math.min(...weights);
            const max = Math.max(...weights);
            
            // If all scores are the same, use a small range
            if (min === max) return { min: min * 0.9, max: min * 1.1 };
            
            return { min, max };
        }, [edges]);

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
                            const w = edge.data('weight') ?? 0;
                            if (w <= 0) return NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN;
                            
                            // Normalize weight to 0-1 range
                            const normalized = scoreRange.max > scoreRange.min
                                ? (w - scoreRange.min) / (scoreRange.max - scoreRange.min)
                                : 0.5;
                            
                            // Scale to width range with more aggressive scaling
                            const scaled = NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN + 
                                (normalized * (NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MAX - NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN)) *
                                NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.BASE_SCALE;
                            
                            return Math.min(Math.max(scaled, NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MIN), NETWORK_VIEW_CONSTANTS.EDGE_WIDTH.MAX);
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

                // Fade class for graying out old level nodes/edges not in path
                {
                    selector: '.faded',
                    style: {
                        opacity: 0.2,
                        'text-opacity': 0.1,
                    },
                },

                // Nodes in expansion path should remain visible
                {
                    selector: 'node[inPath = "true"]',
                    style: {
                        opacity: 1,
                        'text-opacity': 1,
                    },
                },

                // Edges connected to path nodes should remain visible
                {
                    selector: 'edge[inPath = "true"]',
                    style: {
                        opacity: 0.7, // Slightly reduced but still visible
                        'text-opacity': 1,
                    },
                },

                // Expanded nodes styling - only highlight current expansion level
                // Use dynamic selector based on currentExpansionLevel
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

                // Previous expansion levels - subtle styling (fade out previous levels)
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
                            return 0.7; // Fade previous levels
                        },
                    },
                },

                // Edges with expansion level styling - different colors for different levels
                {
                    selector: 'edge[expansionLevel]',
                    style: {
                        'line-color': (edge: cytoscape.EdgeSingular) => {
                            const level = edge.data('expansionLevel') as number | undefined;
                            if (level === undefined || level === 0) return '#999';
                            const colors = NETWORK_VIEW_CONSTANTS.EXPANSION.LEVEL_COLORS;
                            return colors[Math.min(level, colors.length - 1)] || '#999';
                        },
                        'line-width': 2, // Make expansion edges slightly thicker
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
        }, [showOrthologs, scoreRange, currentExpansionLevel]);

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
            getCytoscapeInstance: () => cyRef.current,
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

            // Preserve existing node positions before destroying instance
            const existingPositions = new Map<string, { x: number; y: number }>();
            if (cyRef.current) {
                try {
                    cyRef.current.nodes().forEach((node) => {
                        const pos = node.position();
                        if (pos) {
                            existingPositions.set(node.id(), { x: pos.x, y: pos.y });
                        }
                    });
                    cyRef.current.destroy();
                } catch {
                    // ignore
                }
                cyRef.current = null;
                layoutRunningRef.current = false;
            }

            const initTimeout = setTimeout(() => {
                if (!containerRef.current) return;

                // Group nodes by expansion level for hierarchical layout
                const nodesByLevel = new Map<number, Array<typeof nodes[0]>>();
                let hasExpansionLevels = false;
                
                nodes.forEach(node => {
                    const level = (node as { expansionLevel?: number }).expansionLevel ?? 0;
                    if (!nodesByLevel.has(level)) {
                        nodesByLevel.set(level, []);
                    }
                    nodesByLevel.get(level)!.push(node);
                    if (level > 0) hasExpansionLevels = true;
                });

                // Prepare nodes for Cytoscape with hierarchical positioning
                const cyNodes = nodes.map((node) => {
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
                                ? 0  // Center for level 0
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
                        // Use existing position if available
                        initialPosition = { x, y };
                    }
                    
                    // Check if node is in expansion path
                    const inPath = pathNodeIds.has(id);
                    
                    return {
                        data: {
                            id,
                            label: node.locus_tag || node.label || id,
                            nodeType: nodeType || 'ppi', // Explicitly preserve nodeType
                            hasOrthologs: hasOrthologs || false,
                            expansionLevel: expansionLevel, // Preserve expansion level for styling
                            inPath: inPath ? 'true' : 'false', // Mark if in expansion path
                            ...nodeData,
                        },
                        position: initialPosition,
                    };
                });

                // Prepare edges for Cytoscape
                const cyEdges = edges.map((edge, index) => {
                    const edgeData = edge as PPINetworkEdge & {
                        edgeType?: string;
                        orthology_type?: string;
                        weight?: number;
                        expansionLevel?: number;
                    };

                    // Check if edge is in path
                    // An edge is in path if both source and target are in path, OR
                    // if it connects path nodes to each other (both are path nodes)
                    const sourceInPath = pathNodeIds.has(edge.source);
                    const targetInPath = pathNodeIds.has(edge.target);
                    const edgeInPath = sourceInPath && targetInPath; // Edge is in path if both nodes are in path
                    
                    return {
                        data: {
                            id: edgeData.id || `edge-${index}`,
                            source: edge.source,
                            target: edge.target,
                            weight: edge.weight ?? 1,
                            edgeType: edgeData.edgeType || 'ppi',
                            orthology_type: edgeData.orthology_type,
                            expansionLevel: edgeData.expansionLevel, // Preserve expansion level for styling
                            inPath: edgeInPath ? 'true' : 'false', // Mark if in expansion path
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

                    // For expanded networks: use preset positions (no layout) to maintain level separation
                    // For original network: use COSE force-directed layout
                    if (hasExpansionLevels) {
                        // Set node positions directly based on expansion level (radial/concentric layout)
                        // This keeps levels separated without overlap
                        cy.batch(() => {
                            cyNodes.forEach((nodeData) => {
                                if (nodeData.position) {
                                    const cyNode = cy.getElementById(nodeData.data.id);
                                    if (cyNode && cyNode.length > 0) {
                                        cyNode.position(nodeData.position);
                                    }
                                }
                            });
                        });
                        
                        // Use preset layout to respect initial positions without recalculating
                        // Only fit if there are new nodes (nodes without preserved positions)
                        const hasNewNodes = cyNodes.some(n => !existingPositions.has(n.data.id));
                        const presetLayout = cy.layout({
                            name: 'preset',
                            animate: false,
                            fit: hasNewNodes, // Only fit if we have new nodes
                            padding: 50,
                        });
                        
                        presetLayout.one('layoutstop', () => {
                            // Only fit to new nodes, preserving view if no new nodes
                            if (hasNewNodes) {
                                // Fit to only new nodes to avoid disrupting view
                                const newNodes = cy.nodes().filter(node => {
                                    return !existingPositions.has(node.id());
                                });
                                if (newNodes.length > 0) {
                                    cy.fit(newNodes, 100);
                                }
                            }
                            layoutRunningRef.current = false;
                        });
                        
                        presetLayout.run();
                    } else {
                        // For original network: use standard COSE force-directed layout
                        const layoutOptions: cytoscape.CoseLayoutOptions = {
                            name: 'cose',
                            animate: true,
                            animationDuration: 700,
                            fit: true,
                            padding: 50,
                            idealEdgeLength: (edge: cytoscape.EdgeSingular) => {
                                const w = edge.data('weight') ?? 1;
                                const len = 140 - Math.min(w, 1) * 60;
                                return Math.max(70, len);
                            },
                            nodeRepulsion: 6000,
                            nodeOverlap: 10,
                            gravity: 0.15,
                            numIter: 1200,
                        };
                        
                        const layout = cy.layout(layoutOptions);

                        layout.one('layoutstop', () => {
                            cy.fit(undefined, 50);
                            layoutRunningRef.current = false;
                        });

                        layout.run();
                    }

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

                    // Edge click handler
                    cy.on('tap', 'edge', (event: cytoscape.EventObject) => {
                        const tapped = event.target as cytoscape.EdgeSingular;
                        const edgeData = tapped.data() as {
                            id: string;
                            source: string;
                            target: string;
                            weight?: number;
                            edgeType?: string;
                            orthology_type?: string;
                            expansionLevel?: number;
                        };

                        // Highlight the edge
                        cy.batch(() => {
                            cy.edges().removeClass('selected');
                            tapped.addClass('selected');
                        });

                        // Find original edge object
                        const originalEdge = edges.find((e) => 
                            e.source === edgeData.source && e.target === edgeData.target
                        );
                        if (originalEdge && onEdgeClick) {
                            const originalEvent = event.originalEvent as MouseEvent | undefined;
                            onEdgeClick(originalEdge, originalEvent);
                        }
                    });

                    // Background click: remove fading and edge selection
                    cy.on('tap', (event: cytoscape.EventObject) => {
                        if (event.target === cy) {
                            cy.elements().removeClass('faded');
                            cy.edges().removeClass('selected');
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
        }, [nodes, edges, cyStyles, onNodeClick, onEdgeClick, showOrthologs]);

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

        // Apply fading to old level nodes/edges not in expansion path
        useEffect(() => {
            const cy = cyRef.current;
            if (!cy || currentExpansionLevel === undefined || currentExpansionLevel <= 0) {
                // No fading needed if no expansions or at base level
                cy?.elements().removeClass('faded');
                return;
            }

            cy.batch(() => {
                // First, remove faded class from all
                cy.elements().removeClass('faded');

                // Apply faded class to nodes from previous levels not in path
                cy.nodes().forEach((node) => {
                    const level = node.data('expansionLevel') as number | undefined;
                    const inPath = node.data('inPath') === 'true';
                    const isCurrentLevel = level === currentExpansionLevel;
                    
                    // Gray out if: has expansion level, level < current, and not in path
                    if (level !== undefined && !isCurrentLevel && level < currentExpansionLevel && !inPath) {
                        // Also gray out level 0 nodes if we're beyond level 0
                        node.addClass('faded');
                    }
                });

                // Apply faded class to edges from previous levels not in path
                cy.edges().forEach((edge) => {
                    const level = edge.data('expansionLevel') as number | undefined;
                    const inPath = edge.data('inPath') === 'true';
                    const isCurrentLevel = level === currentExpansionLevel;
                    
                    // Gray out if: has expansion level, level < current, and not in path
                    if (level !== undefined && !isCurrentLevel && level < currentExpansionLevel && !inPath) {
                        edge.addClass('faded');
                    }
                });
            });
        }, [currentExpansionLevel, pathNodeIds]);

        return (
            <div className={styles.graphContainer}>
                <div ref={containerRef} className={styles.cytoscapeContainer}/>
            </div>
        );
    }
);

NetworkGraph.displayName = 'NetworkGraph';
  