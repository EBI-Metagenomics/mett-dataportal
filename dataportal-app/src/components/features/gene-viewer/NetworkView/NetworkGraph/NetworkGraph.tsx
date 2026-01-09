import React, {
    useEffect,
    useRef,
    useImperativeHandle,
    forwardRef,
    useMemo,
} from 'react';
import cytoscape from 'cytoscape';
import { NetworkGraphRef, NetworkGraphProps } from './types';
import { useCytoscapeStyles } from './hooks/useCytoscapeStyles';
import { useGraphFading } from './hooks/useGraphFading';
import { prepareNodes, prepareEdges } from './utils/prepareElements';
import { preservePositions, applyPositions } from './utils/positionPreservation';
import { calculateGlobalCloudPositions } from '../utils/globalCloudLayout';
import { getZoomLevel, applyZoomOptimization, createDebouncedZoomHandler } from '../utils/zoomOptimization';
import { NETWORK_VIEW_CONSTANTS } from '../constants';
import styles from './NetworkGraph.module.scss';

/**
 * NetworkGraph component - Cytoscape.js graph visualization
 */
export const NetworkGraph = forwardRef<NetworkGraphRef, NetworkGraphProps>(
    ({nodes, edges, showOrthologs, viewMode = 'focused', currentExpansionLevel, expansionPath = [], onNodeClick, onEdgeClick, selectedNode}, ref) => {
        // Create a set of path node IDs for quick lookup
        const pathNodeIds = useMemo(() => {
            return new Set(expansionPath.map(p => p.nodeId));
        }, [expansionPath]);
        
        const containerRef = useRef<HTMLDivElement>(null);
        const cyRef = useRef<cytoscape.Core | null>(null);
        const layoutRunningRef = useRef(false);
        const zoomHandlerCleanupRef = useRef<(() => void) | null>(null);
        const existingNodeIdsRef = useRef<Set<string>>(new Set());
        const existingEdgeKeysRef = useRef<Set<string>>(new Set());
        const nodesKeyRef = useRef<string>('');
        const edgesKeyRef = useRef<string>('');
        const previousViewModeRef = useRef<string>(viewMode);
        const previousNodesKeyRef = useRef<string>('');
        const previousEdgesKeyRef = useRef<string>('');

        // Calculate score range for normalization
        const scoreRange = useMemo(() => {
            if (edges.length === 0) return { min: 0, max: 1 };
            
            const weights = edges.map(e => e.weight ?? 0).filter(w => w > 0);
            if (weights.length === 0) return { min: 0, max: 1 };
            
            const min = Math.min(...weights);
            const max = Math.max(...weights);
            
            if (min === max) return { min: min * 0.9, max: min * 1.1 };
            
            return { min, max };
        }, [edges]);

        // Generate Cytoscape styles
        const cyStyles = useCytoscapeStyles({
            showOrthologs,
            scoreRange,
            currentExpansionLevel,
            viewMode,
        });

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

        // Create stable keys for nodes/edges to detect actual changes
        const nodesKey = useMemo(() => {
            return `${nodes.length}-${nodes.map(n => n.id).sort().join(',')}`;
        }, [nodes]);
        
        const edgesKey = useMemo(() => {
            return `${edges.length}-${edges.map(e => `${e.source}-${e.target}`).sort().join(',')}`;
        }, [edges]);

        // Initialize or update Cytoscape instance when:
        // 1. First mount
        // 2. View mode changes
        // 3. Nodes/edges actually change (e.g., after expansion)
        // 4. Graph becomes empty
        useEffect(() => {
            // Container check + empty graph cleanup
            if (!containerRef.current) {
                return;
            }

            const viewModeChanged = previousViewModeRef.current !== viewMode;
            const nodesChanged = nodesKey !== previousNodesKeyRef.current;
            const edgesChanged = edgesKey !== previousEdgesKeyRef.current;
            
            // Only recreate if:
            // - No instance exists
            // - View mode changed
            // - Nodes or edges actually changed (but not if we're currently empty)
            const shouldRecreate = !cyRef.current || viewModeChanged || (nodesChanged && nodes.length > 0) || (edgesChanged && edges.length > 0);

            if (shouldRecreate) {
                // Clean up existing instance
                if (cyRef.current) {
                    // Cleanup zoom handler
                    if (zoomHandlerCleanupRef.current) {
                        zoomHandlerCleanupRef.current();
                        zoomHandlerCleanupRef.current = null;
                    }
                    try {
                        cyRef.current.destroy();
                    } catch {
                        // ignore cleanup errors
                    }
                    cyRef.current = null;
                    layoutRunningRef.current = false;
                    existingNodeIdsRef.current = new Set();
                    existingEdgeKeysRef.current = new Set();
                }

                // If graph is empty, just cleanup and return
                if (nodes.length === 0) {
                    previousViewModeRef.current = viewMode;
                    previousNodesKeyRef.current = nodesKey;
                    previousEdgesKeyRef.current = edgesKey;
                    return;
                }

                previousViewModeRef.current = viewMode;
                previousNodesKeyRef.current = nodesKey;
                previousEdgesKeyRef.current = edgesKey;

                const initTimeout = setTimeout(() => {
                    if (!containerRef.current) return;

                // Check if we have expansion levels
                const hasExpansionLevels = nodes.some(node => 
                    ((node as { expansionLevel?: number }).expansionLevel ?? 0) > 0
                );

                // Preserve existing node positions if instance exists
                const existingPositions = cyRef.current ? preservePositions(cyRef.current) : new Map<string, { x: number; y: number }>();

                // Prepare nodes and edges for Cytoscape
                const preparedNodes = prepareNodes(nodes, pathNodeIds, existingPositions, hasExpansionLevels);
                const preparedEdges = prepareEdges(edges, pathNodeIds);

                try {
                    const cy = cytoscape({
                        container: containerRef.current,
                        elements: [...preparedNodes, ...preparedEdges],
                        style: cyStyles,
                        userPanningEnabled: true,
                        userZoomingEnabled: true,
                        boxSelectionEnabled: false,
                        wheelSensitivity: 0.1, // Lower sensitivity for smoother, more controlled zoom
                    });

                    cyRef.current = cy;
                    layoutRunningRef.current = true;

                    // Set up event handlers immediately after creating instance
                    // Node click handler
                    cy.on('tap', 'node', (event: cytoscape.EventObject) => {
                        const tapped = event.target as cytoscape.NodeSingular;
                        const nodeData = tapped.data() as { id: string };

                        cy.batch(() => {
                            cy.elements().removeClass('faded');
                            cy.elements().addClass('faded');

                            tapped.removeClass('faded');
                            tapped.connectedEdges().removeClass('faded');
                            tapped.connectedEdges().connectedNodes().removeClass('faded');
                        });

                        const original = nodes.find((n) => n.id === nodeData.id);
                        if (original) {
                            const originalEvent = event.originalEvent as MouseEvent | undefined;
                            onNodeClick(original, originalEvent);
                        }
                    });

                    // Edge click handler
                    if (onEdgeClick) {
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

                            cy.batch(() => {
                                cy.edges().removeClass('selected');
                                tapped.addClass('selected');
                            });

                            const originalEdge = edges.find((e) => 
                                e.source === edgeData.source && e.target === edgeData.target
                            );
                            if (originalEdge) {
                                const originalEvent = event.originalEvent as MouseEvent | undefined;
                                onEdgeClick(originalEdge, originalEvent);
                            }
                        });
                    }

                    // Background click handler
                    cy.on('tap', (event: cytoscape.EventObject) => {
                        if (event.target === cy) {
                            cy.elements().removeClass('faded');
                            cy.edges().removeClass('selected');
                        }
                    });

                    // Set up debounced zoom handler for smooth zooming
                    // This only applies optimization when zoom level actually changes
                    const { handler: zoomHandler, cleanup: zoomCleanup } = createDebouncedZoomHandler(
                        cy,
                        showOrthologs,
                        100 // 100ms debounce for smooth zoom
                    );
                    cy.on('zoom', zoomHandler);
                    zoomHandlerCleanupRef.current = zoomCleanup;
                    
                    // Trigger initial label visibility
                    const initialZoom = cy.zoom();
                    const initialZoomLevel = getZoomLevel(initialZoom);
                    applyZoomOptimization(cy, initialZoomLevel, showOrthologs);

                    // Apply layout based on view mode
                    if (viewMode === 'global') {
                        // Global cloud layout: positions nodes by centrality
                        const cloudPositions = calculateGlobalCloudPositions(
                            nodes,
                            edges,
                            {
                                centerX: NETWORK_VIEW_CONSTANTS.GLOBAL_CLOUD.CENTER_X,
                                centerY: NETWORK_VIEW_CONSTANTS.GLOBAL_CLOUD.CENTER_Y,
                                baseRadius: NETWORK_VIEW_CONSTANTS.GLOBAL_CLOUD.BASE_RADIUS,
                                tierRadiusIncrement: NETWORK_VIEW_CONSTANTS.GLOBAL_CLOUD.TIER_RADIUS_INCREMENT,
                                numTiers: NETWORK_VIEW_CONSTANTS.GLOBAL_CLOUD.NUM_TIERS,
                                angleSpread: NETWORK_VIEW_CONSTANTS.GLOBAL_CLOUD.ANGLE_SPREAD,
                                minNodeDistance: NETWORK_VIEW_CONSTANTS.GLOBAL_CLOUD.MIN_NODE_DISTANCE,
                            }
                        );
                        
                        // Apply positions to nodes
                        cy.batch(() => {
                            cy.nodes().forEach(node => {
                                const pos = cloudPositions.get(node.id());
                                if (pos) {
                                    node.position(pos);
                                }
                            });
                        });
                        
                        // Use preset layout to maintain cloud positions
                        // Create position map from node ID to position
                        const positionMap: Record<string, { x: number; y: number }> = {};
                        cloudPositions.forEach((pos, nodeId) => {
                            positionMap[nodeId] = pos;
                        });
                        
                        const cloudLayout = cy.layout({
                            name: 'preset',
                            positions: (nodeId: string) => positionMap[nodeId],
                            animate: true,
                            animationDuration: 1000,
                            fit: true,
                            padding: 50,
                        });
                        
                        cloudLayout.one('layoutstop', () => {
                            layoutRunningRef.current = false;
                        });
                        
                        cloudLayout.run();
                    } else if (hasExpansionLevels) {
                        // Focused mode with expansions: use radial layout
                        // Set node positions and lock existing ones
                        applyPositions(cy, preparedNodes, existingPositions);
                        
                        const hasNewNodes = preparedNodes.some(n => !existingPositions.has(n.data.id));
                        
                        if (hasNewNodes) {
                            setTimeout(() => {
                                const newNodes = cy.nodes().filter(node => {
                                    return !existingPositions.has(node.id());
                                });
                                if (newNodes.length > 0) {
                                    cy.fit(newNodes, 100);
                                }
                                layoutRunningRef.current = false;
                            }, 50);
                        } else {
                            layoutRunningRef.current = false;
                        }
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

                    // Track existing elements
                    cy.nodes().forEach(node => {
                        existingNodeIdsRef.current.add(node.id());
                    });
                    cy.edges().forEach(edge => {
                        const source = edge.source().id();
                        const target = edge.target().id();
                        existingEdgeKeysRef.current.add(`${source}-${target}`);
                    });
                    nodesKeyRef.current = nodesKey;
                    edgesKeyRef.current = edgesKey;
                } catch {
                    // Initialization errors are swallowed
                }
                }, 50);

                return () => {
                    clearTimeout(initTimeout);
                };
            }
            // eslint-disable-next-line react-hooks/exhaustive-deps
            // We depend on viewMode, nodesKey, and edgesKey to detect actual changes
            // nodesKey and edgesKey are stable and only change when node/edge IDs actually change
        }, [viewMode, nodesKey, edgesKey]); // Recreate when view mode changes OR nodes/edges actually change

        // Handle empty graph cleanup separately
        useEffect(() => {
            if (nodes.length === 0 && cyRef.current) {
                try {
                    if (zoomHandlerCleanupRef.current) {
                        zoomHandlerCleanupRef.current();
                        zoomHandlerCleanupRef.current = null;
                    }
                    cyRef.current.destroy();
                    cyRef.current = null;
                    layoutRunningRef.current = false;
                    existingNodeIdsRef.current = new Set();
                    existingEdgeKeysRef.current = new Set();
                } catch {
                    // ignore
                }
            }
        }, [nodes.length]);

        // Skip all updates during transitions - this prevents flickering
        // The graph will remain stable with existing data until a full recreation happens
        // Note: We intentionally don't update elements incrementally to prevent multiple renders
        // The graph will only be recreated when viewMode changes, keeping it stable during data fetches

        // Cleanup on unmount
        useEffect(() => {
            return () => {
                if (zoomHandlerCleanupRef.current) {
                    zoomHandlerCleanupRef.current();
                    zoomHandlerCleanupRef.current = null;
                }
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
        }, []);

        // Update label visibility when showOrthologs changes
        useEffect(() => {
            const cy = cyRef.current;
            if (!cy) return;
            cy.trigger('zoom');
        }, [showOrthologs]);

        // Update selection class when selectedNode changes
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

        // Apply fading to old level nodes/edges
        useGraphFading({
            cy: cyRef.current,
            currentExpansionLevel,
            pathNodeIds,
        });

        return (
            <div className={styles.graphContainer}>
                <div ref={containerRef} className={styles.cytoscapeContainer}/>
            </div>
        );
    }
);

NetworkGraph.displayName = 'NetworkGraph';
