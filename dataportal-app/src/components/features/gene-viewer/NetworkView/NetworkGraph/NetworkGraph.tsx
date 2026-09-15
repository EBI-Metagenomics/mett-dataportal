import React, {
    useEffect,
    useRef,
    useImperativeHandle,
    forwardRef,
    useMemo,
    useCallback,
} from 'react';
import cytoscape from 'cytoscape';
import { NetworkGraphRef, NetworkGraphProps } from './types';
import { useCytoscapeStyles } from './hooks/useCytoscapeStyles';
import { useGraphFading } from './hooks/useGraphFading';
import { prepareNodes, prepareEdges } from './utils/prepareElements';
import { registerCytoscapeExtensions } from './utils/registerCytoscapeExtensions';
import { runSafeLayout, stopLayout, type LayoutControl } from './utils/runSafeLayout';
import styles from './NetworkGraph.module.scss';

registerCytoscapeExtensions();

const incomingEdgeId = (edge: NetworkGraphProps['edges'][0], index: number): string =>
    (edge as { id?: string }).id ||
    `${(edge as { dataSource?: string }).dataSource ?? 'local'}-${edge.source}-${edge.target}-${index}`;

const ppiSignatureOf = (nodes: NetworkGraphProps['nodes'], edges: NetworkGraphProps['edges']): string => {
    const ppiNodeIds = nodes
        .filter((n) => (n as { nodeType?: string }).nodeType !== 'ortholog')
        .map((n) => n.id);
    const ppiEdgeKeys = edges
        .filter((e) => (e as { edgeType?: string }).edgeType !== 'ortholog')
        .map((e, i) => incomingEdgeId(e, i));
    return JSON.stringify([[...new Set(ppiNodeIds)].sort(), [...new Set(ppiEdgeKeys)].sort()]);
};

const seedNewNodePositions = (
    cy: cytoscape.Core,
    addedIds: string[],
    existingIds: Set<string>
): void => {
    cy.batch(() => {
        addedIds.forEach((id, i) => {
            const el = cy.getElementById(id);
            if (!el || el.empty()) return;
            const neighbor = el.neighborhood('node').filter((n) => existingIds.has(n.id()));
            const base = neighbor.nonempty()
                ? neighbor[0].position()
                : { x: 0, y: 0 };
            const angle = (2 * Math.PI * i) / Math.max(addedIds.length, 1);
            el.position({
                x: base.x + 90 * Math.cos(angle),
                y: base.y + 90 * Math.sin(angle),
            });
        });
    });
};

/**
 * NetworkGraph component - Cytoscape.js graph visualization
 */
export const NetworkGraph = forwardRef<NetworkGraphRef, NetworkGraphProps>(
    ({nodes, edges, showOrthologs, currentExpansionLevel, expansionPath = [], focalNodeId, onNodeClick, onEdgeClick, selectedNode, layoutRevision = 0}, ref) => {
        const pathNodeIds = useMemo(() => {
            return new Set(expansionPath.map(p => p.nodeId));
        }, [expansionPath]);

        const containerRef = useRef<HTMLDivElement>(null);
        const cyRef = useRef<cytoscape.Core | null>(null);
        const layoutControlRef = useRef<LayoutControl>({ instance: null, running: false });
        const overlayLayoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
        const prevLayoutRevisionRef = useRef(layoutRevision);
        const ppiSignatureRef = useRef<string>('');
        const nodesRef = useRef(nodes);
        const edgesRef = useRef(edges);
        const pathNodeIdsRef = useRef(pathNodeIds);
        const focalNodeIdRef = useRef(focalNodeId);
        const showOrthologsRef = useRef(showOrthologs);
        const onNodeClickRef = useRef(onNodeClick);
        const onEdgeClickRef = useRef(onEdgeClick);
        const cyStylesRef = useRef<cytoscape.StylesheetJson | null>(null);

        nodesRef.current = nodes;
        edgesRef.current = edges;
        pathNodeIdsRef.current = pathNodeIds;
        focalNodeIdRef.current = focalNodeId;
        showOrthologsRef.current = showOrthologs;
        onNodeClickRef.current = onNodeClick;
        onEdgeClickRef.current = onEdgeClick;

        const scoreRange = useMemo(() => {
            if (edges.length === 0) return { min: 0, max: 1 };

            const weights = edges.map(e => e.weight ?? 0).filter(w => w > 0);
            if (weights.length === 0) return { min: 0, max: 1 };

            const min = Math.min(...weights);
            const max = Math.max(...weights);

            if (min === max) return { min: min * 0.9, max: min * 1.1 };

            return { min, max };
        }, [edges]);

        const cyStyles = useCytoscapeStyles({
            showOrthologs,
            scoreRange,
            currentExpansionLevel,
        });
        cyStylesRef.current = cyStyles as unknown as cytoscape.StylesheetJson;

        const ppiSignature = useMemo(() => ppiSignatureOf(nodes, edges), [nodes, edges]);

        const relayout = useCallback(() => {
            const cy = cyRef.current;
            if (!cy || cy.destroyed()) return;
            if (overlayLayoutTimerRef.current) {
                clearTimeout(overlayLayoutTimerRef.current);
                overlayLayoutTimerRef.current = null;
            }
            runSafeLayout(cy, layoutControlRef, {
                mode: 'reset',
                focalNodeId: focalNodeIdRef.current,
            });
        }, []);

        useImperativeHandle(ref, () => ({
            resetView: relayout,
            fitToNodes: () => {
                if (!cyRef.current || cyRef.current.destroyed()) return;
                const all = cyRef.current.nodes();
                if (all.length > 0) cyRef.current.fit(all, 100);
                else cyRef.current.fit(undefined, 50);
            },
            relayout,
            getCytoscapeInstance: () => cyRef.current,
        }), [relayout]);

        const bindHandlers = (cy: cytoscape.Core) => {
            cy.on('tap', 'node', (event: cytoscape.EventObject) => {
                const tapped = event.target as cytoscape.NodeSingular;
                const nodeData = tapped.data() as { id: string };
                const original = nodesRef.current.find((n) => n.id === nodeData.id);
                if (original) {
                    const originalEvent = event.originalEvent as MouseEvent | undefined;
                    onNodeClickRef.current(original, originalEvent);
                }
            });

            cy.on('tap', 'edge', (event: cytoscape.EventObject) => {
                if (!onEdgeClickRef.current) return;
                const tapped = event.target as cytoscape.EdgeSingular;
                const edgeData = tapped.data() as {
                    id: string;
                    source: string;
                    target: string;
                };

                cy.batch(() => {
                    cy.edges().removeClass('selected');
                    tapped.addClass('selected');
                });

                const originalEdge = edgesRef.current.find((e) =>
                    ((e as { id?: string }).id && (e as { id?: string }).id === edgeData.id) ||
                    (e.source === edgeData.source && e.target === edgeData.target)
                );
                if (originalEdge) {
                    const originalEvent = event.originalEvent as MouseEvent | undefined;
                    onEdgeClickRef.current(originalEdge, originalEvent);
                }
            });

            cy.on('tap', (event: cytoscape.EventObject) => {
                if (event.target === cy) {
                    cy.elements().removeClass('faded');
                    cy.edges().removeClass('selected');
                }
            });

            cy.on('zoom', () => {
                const z = cy.zoom();
                const labelThreshold = 0.5;
                cy.nodes().forEach(node => {
                    const nodeData = node.data();
                    const isPPI = nodeData.nodeType === 'ppi';
                    const isOrtholog = nodeData.nodeType === 'ortholog';

                    if (showOrthologsRef.current && (isPPI || isOrtholog)) {
                        node.style('text-opacity', 1);
                    } else {
                        node.style('text-opacity', z > labelThreshold ? 1 : 0);
                    }
                });
            });
        };

        // Rebuild when the PPI neighborhood changes or Reset is pressed.
        useEffect(() => {
            if (!containerRef.current || nodesRef.current.length === 0) {
                stopLayout(layoutControlRef);
                if (cyRef.current) {
                    try {
                        cyRef.current.destroy();
                    } catch {
                        // ignore
                    }
                    cyRef.current = null;
                }
                ppiSignatureRef.current = '';
                return;
            }

            const initTimeout = setTimeout(() => {
                if (!containerRef.current) return;

                const currentNodes = nodesRef.current;
                const currentEdges = edgesRef.current;
                const hasExpansionLevels = currentNodes.some(
                    (node) => ((node as { expansionLevel?: number }).expansionLevel ?? 0) > 0
                );
                const preparedNodes = prepareNodes(currentNodes, pathNodeIdsRef.current, new Map(), hasExpansionLevels);
                const preparedEdges = prepareEdges(currentEdges, pathNodeIdsRef.current);
                const isReset = layoutRevision > 0 && layoutRevision !== prevLayoutRevisionRef.current;
                prevLayoutRevisionRef.current = layoutRevision;

                try {
                    const cy = cytoscape({
                        container: containerRef.current,
                        elements: [...preparedNodes, ...preparedEdges],
                        style: (cyStylesRef.current ?? []) as cytoscape.StylesheetJson,
                        userPanningEnabled: true,
                        userZoomingEnabled: true,
                        boxSelectionEnabled: false,
                        wheelSensitivity: 0.2,
                    });

                    cyRef.current = cy;
                    ppiSignatureRef.current = ppiSignature;
                    bindHandlers(cy);
                    cy.trigger('zoom');
                    runSafeLayout(cy, layoutControlRef, {
                        mode: isReset ? 'reset' : 'full',
                        focalNodeId: focalNodeIdRef.current,
                    });
                } catch {
                    // Initialization errors are swallowed
                }
            }, 50);

            return () => {
                clearTimeout(initTimeout);
                if (overlayLayoutTimerRef.current) {
                    clearTimeout(overlayLayoutTimerRef.current);
                    overlayLayoutTimerRef.current = null;
                }
                stopLayout(layoutControlRef);
                if (cyRef.current) {
                    try {
                        cyRef.current.destroy();
                    } catch {
                        // ignore
                    }
                    cyRef.current = null;
                }
                ppiSignatureRef.current = '';
            };
        }, [ppiSignature, layoutRevision]);

        // Add / remove overlay elements (orthologs) in place without destroying the PPI graph.
        useEffect(() => {
            const cy = cyRef.current;
            if (!cy || cy.destroyed() || ppiSignature !== ppiSignatureRef.current) return;

            const existingIds = new Set(cy.nodes().map((n) => n.id()));
            const existingEdgeIds = new Set(cy.edges().map((e) => e.id()));
            const currentNodeIds = new Set(nodes.map((n) => n.id));
            const currentEdgeIds = new Set(edges.map((e, i) => incomingEdgeId(e, i)));
            const toRemoveNodes = cy.nodes().filter((n) => !currentNodeIds.has(n.id()));
            const toRemoveEdges = cy.edges().filter((e) => !currentEdgeIds.has(e.id()));
            const toAddNodes = nodes.filter((n) => !existingIds.has(n.id));
            const toAddEdges = edges.filter((e, i) => !existingEdgeIds.has(incomingEdgeId(e, i)));

            const changed =
                toRemoveNodes.length > 0 ||
                toRemoveEdges.length > 0 ||
                toAddNodes.length > 0 ||
                toAddEdges.length > 0;

            if (!changed) {
                cy.style(cyStyles as unknown as cytoscape.StylesheetJson);
                cy.trigger('zoom');
                return;
            }

            stopLayout(layoutControlRef);
            cy.batch(() => {
                toRemoveEdges.remove();
                toRemoveNodes.remove();
            });
            if (toAddNodes.length > 0 || toAddEdges.length > 0) {
                const hasExpansionLevels = nodes.some(
                    (node) => ((node as { expansionLevel?: number }).expansionLevel ?? 0) > 0
                );
                const preparedNewNodes = prepareNodes(toAddNodes, pathNodeIds, new Map(), hasExpansionLevels);
                const preparedNewEdges = prepareEdges(toAddEdges, pathNodeIds);
                cy.add([...preparedNewNodes, ...preparedNewEdges]);
                seedNewNodePositions(cy, toAddNodes.map((n) => n.id), existingIds);
            }
            cy.style(cyStyles as unknown as cytoscape.StylesheetJson);
            cy.trigger('zoom');

            if (overlayLayoutTimerRef.current) {
                clearTimeout(overlayLayoutTimerRef.current);
            }
            overlayLayoutTimerRef.current = setTimeout(() => {
                overlayLayoutTimerRef.current = null;
                const live = cyRef.current;
                if (!live || live.destroyed()) return;
                runSafeLayout(live, layoutControlRef, {
                    mode: 'inPlace',
                    focalNodeId: focalNodeIdRef.current,
                });
            }, 120);
        }, [nodes, edges, ppiSignature, pathNodeIds, focalNodeId, cyStyles]);

        useEffect(() => {
            const cy = cyRef.current;
            if (!cy || cy.destroyed()) return;
            cy.trigger('zoom');
        }, [showOrthologs]);

        useEffect(() => {
            const cy = cyRef.current;
            if (!cy || cy.destroyed()) return;

            cy.batch(() => {
                cy.nodes().removeClass('isSelected');
                if (selectedNode?.id) {
                    const el = cy.getElementById(selectedNode.id);
                    if (el && el.nonempty()) el.addClass('isSelected');
                }
            });
        }, [selectedNode?.id]);

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
