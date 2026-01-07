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
import styles from './NetworkGraph.module.scss';

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
            
            if (min === max) return { min: min * 0.9, max: min * 1.1 };
            
            return { min, max };
        }, [edges]);

        // Generate Cytoscape styles
        const cyStyles = useCytoscapeStyles({
            showOrthologs,
            scoreRange,
            currentExpansionLevel,
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
            const existingPositions = preservePositions(cyRef.current);

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

                // Check if we have expansion levels
                const hasExpansionLevels = nodes.some(node => 
                    ((node as { expansionLevel?: number }).expansionLevel ?? 0) > 0
                );

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
                        wheelSensitivity: 0.2,
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

                    // Zoom handler for label visibility
                    cy.on('zoom', () => {
                        const z = cy.zoom();
                        cy.nodes().forEach(node => {
                            const nodeData = node.data();
                            const isPPI = nodeData.nodeType === 'ppi';
                            const isOrtholog = nodeData.nodeType === 'ortholog';
                            
                            if (showOrthologs && isPPI) {
                                node.style('text-opacity', 1);
                            } else if (isOrtholog) {
                                node.style('text-opacity', 0);
                            } else {
                                node.style('text-opacity', z > 0.9 ? 1 : 0);
                            }
                        });
                    });
                    
                    // Trigger initial label visibility
                    cy.trigger('zoom');

                    // Apply layout (direct call, not a hook)
                    if (hasExpansionLevels) {
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
                } catch {
                    // Initialization errors are swallowed
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
        }, [nodes, edges, cyStyles, showOrthologs, pathNodeIds, onNodeClick, onEdgeClick]);

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
