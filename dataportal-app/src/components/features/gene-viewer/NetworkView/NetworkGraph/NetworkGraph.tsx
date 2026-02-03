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
import { preservePositions } from './utils/positionPreservation';
import styles from './NetworkGraph.module.scss';

/**
 * NetworkGraph component - Cytoscape.js graph visualization
 */
export const NetworkGraph = forwardRef<NetworkGraphRef, NetworkGraphProps>(
    ({nodes, edges, showOrthologs, currentExpansionLevel, expansionPath = [], focalNodeId, onNodeClick, onEdgeClick, selectedNode}, ref) => {
        // Create a set of path node IDs for quick lookup
        const pathNodeIds = useMemo(() => {
            return new Set(expansionPath.map(p => p.nodeId));
        }, [expansionPath]);
        
        const containerRef = useRef<HTMLDivElement>(null);
        const cyRef = useRef<cytoscape.Core | null>(null);
        const layoutRunningRef = useRef(false);
        const ppiSignatureRef = useRef<string>('');

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
            // PPI-only signature: when only ortholog nodes/edges change we update in place (no layout reset)
            const ppiNodeIds = nodes
                .filter((n) => (n as { nodeType?: string }).nodeType !== 'ortholog')
                .map((n) => n.id);
            const ppiEdgeKeys = edges
                .filter((e) => (e as { edgeType?: string }).edgeType !== 'ortholog')
                .map((e) => `${e.source}-${e.target}`);
            const ppiSignature = JSON.stringify([[...new Set(ppiNodeIds)].sort(), [...new Set(ppiEdgeKeys)].sort()]);

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
                ppiSignatureRef.current = '';
                return;
            }

            const cy = cyRef.current;
            if (cy && ppiSignature === ppiSignatureRef.current) {
                // Only ortholog visibility changed: add/remove ortholog elements in place, do not run layout
                const existingIds = new Set(cy.nodes().map((n) => n.id()));
                const existingEdgeKeys = new Set(cy.edges().map((e) => `${e.source().id()}-${e.target().id()}`));
                const currentNodeIds = new Set(nodes.map((n) => n.id));
                const currentEdgeKeys = new Set(edges.map((e) => `${e.source}-${e.target}`));
                const toRemoveNodes = cy.nodes().filter((n) => !currentNodeIds.has(n.id()));
                const toRemoveEdges = cy.edges().filter((e) => !currentEdgeKeys.has(`${e.source().id()}-${e.target().id()}`));
                const toAddNodes = nodes.filter((n) => !existingIds.has(n.id));
                const toAddEdges = edges.filter((e) => !existingEdgeKeys.has(`${e.source}-${e.target}`));
                cy.batch(() => {
                    toRemoveEdges.remove();
                    toRemoveNodes.remove();
                });
                if (toAddNodes.length > 0 || toAddEdges.length > 0) {
                    const hasExpansionLevels = nodes.some((node) => ((node as { expansionLevel?: number }).expansionLevel ?? 0) > 0);
                    const preparedNewNodes = prepareNodes(toAddNodes, pathNodeIds, new Map(), hasExpansionLevels);
                    const preparedNewEdges = prepareEdges(toAddEdges, pathNodeIds);
                    cy.add([...preparedNewNodes, ...preparedNewEdges]);
                }
                cy.style(cyStyles);
                cy.trigger('zoom');
                return;
            }

            // Full recreate: preserve existing node positions before destroying instance
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
                    ppiSignatureRef.current = ppiSignature;

                    // Set up event handlers immediately after creating instance
                    // Node click handler - show popup only; no fading to avoid confusing "refresh" effect
                    cy.on('tap', 'node', (event: cytoscape.EventObject) => {
                        const tapped = event.target as cytoscape.NodeSingular;
                        const nodeData = tapped.data() as { id: string };

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

                    // Zoom handler: show labels – when Show Orthologs is on, show PPI and ortholog labels at any zoom; otherwise show when zoomed in
                    cy.on('zoom', () => {
                        const z = cy.zoom();
                        const labelThreshold = 0.5;
                        cy.nodes().forEach(node => {
                            const nodeData = node.data();
                            const isPPI = nodeData.nodeType === 'ppi';
                            const isOrtholog = nodeData.nodeType === 'ortholog';

                            if (showOrthologs && (isPPI || isOrtholog)) {
                                node.style('text-opacity', 1);
                            } else {
                                node.style('text-opacity', z > labelThreshold ? 1 : 0);
                            }
                        });
                    });
                    
                    // Trigger initial label visibility
                    cy.trigger('zoom');

                    // Apply layout: always use force-directed (cose) for organic look, including expanded graphs
                    // Nodes already have initial positions from prepareNodes (radial or preserved); don't lock so cose can rearrange all
                    cy.nodes().unlock();
                    const coseOptions: cytoscape.CoseLayoutOptions = {
                        name: 'cose',
                        fit: true,
                        padding: 80,
                        animate: true,
                        animationDuration: 500,
                        avoidOverlap: true,
                        nodeDimensionsIncludeLabels: true,
                        idealEdgeLength: 100,
                        nodeRepulsion: 80000,
                        nodeOverlap: 20,
                        gravity: 0.2,
                        numIter: 1000,
                        randomize: false,
                    };
                    const layout = cy.layout(coseOptions);
                    layout.one('layoutstop', () => {
                        cy.fit(undefined, 80);
                        layoutRunningRef.current = false;
                    });
                    layout.run();
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
        }, [nodes, edges, cyStyles, showOrthologs, pathNodeIds, focalNodeId, expansionPath, onNodeClick, onEdgeClick]);

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
