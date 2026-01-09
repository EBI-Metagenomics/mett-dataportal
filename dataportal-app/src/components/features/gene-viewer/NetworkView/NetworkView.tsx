import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useNetworkData } from '../../../../hooks/useNetworkData';
import { useAuth } from '../../../../hooks/useAuth';
import { PPINetworkNode, PPINetworkEdge } from '../../../../interfaces/PPI';
import { PPIService } from '../../../../services/interactions/ppiService';
import { NetworkGraph, NetworkGraphRef } from './NetworkGraph';
import { NetworkControls } from './NetworkControls';
import { NetworkStats } from './NetworkStats';
import { EmptyState } from './EmptyState';
import { AuthRequired } from './AuthRequired';
import { NodeInfoPopup } from './NodeInfoPopup';
import { EdgeInfoPopup } from './EdgeInfoPopup';
import { ExpansionBreadcrumb } from './ExpansionBreadcrumb';
import { enrichNetworkData } from './utils/enrichNodes';
import { 
  createInitialExpansionState, 
  canExpandNode, 
  isNodeExpanded,
  mergeExpansionData,
  clearExpansions,
  navigateToPathLevel,
} from './utils/expansionUtils';
import type { ExpansionState } from './utils/expansionUtils';
import { exportExpansionPathJSON, exportNetworkImage } from './utils/exportUtils';
import { ViewStateUtils, type ViewState } from './types/viewMode';
import styles from './NetworkView.module.scss';

interface NetworkViewProps {
  speciesAcronym?: string;
  isolateName?: string;
  selectedLocusTag?: string | null;
  setLoading?: React.Dispatch<React.SetStateAction<boolean>>;
  onFeatureSelect?: (feature: { data: { locus_tag?: string; gene_name?: string; product?: string; uniprot_id?: string; isolate_name?: string; species_acronym?: string } }) => void;
}

/**
 * NetworkView component displays PPI network with optional ortholog enrichment
 * 
 * Architecture notes:
 * - Extensible: Can easily add new data sources by extending the data fetching logic
 * - Modular: Network visualization can be replaced with different libraries
 * - Flexible: Ortholog display can be toggled or extended with more metadata
 */
const NetworkView: React.FC<NetworkViewProps> = ({
  speciesAcronym,
  isolateName,
  selectedLocusTag,
  setLoading,
}) => {
  const { isAuthenticated } = useAuth();
  const [scoreType, setScoreType] = useState<string>('ds_score');
  const [scoreThreshold, setScoreThreshold] = useState<number>(0.8);
  const [displayThreshold, setDisplayThreshold] = useState<number>(0.8);
  const [showOrthologs, setShowOrthologs] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<PPINetworkNode | null>(null);
  const [popupNode, setPopupNode] = useState<{ node: PPINetworkNode; x: number; y: number } | null>(null);
  const [popupEdge, setPopupEdge] = useState<{ 
    edge: PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number }; 
    x: number; 
    y: number;
  } | null>(null);
  const [expansionState, setExpansionState] = useState<ExpansionState>(createInitialExpansionState());
  const [expandingNodeId, setExpandingNodeId] = useState<string | null>(null);
  const [viewState, setViewState] = useState<ViewState>(ViewStateUtils.createGlobal());
  const thresholdDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const graphRef = useRef<NetworkGraphRef>(null);
  const originalNodesRef = useRef<PPINetworkNode[]>([]);
  const originalEdgesRef = useRef<PPINetworkEdge[]>([]);
  const globalNetworkDataRef = useRef<{ nodes: PPINetworkNode[]; edges: PPINetworkEdge[] } | null>(null);
  const lastStableDataRef = useRef<{ enrichedNodes: PPINetworkNode[]; enrichedEdges: PPINetworkEdge[] } | null>(null);

  // Determine if we're in global mode
  const isGlobalMode = ViewStateUtils.isGlobal(viewState);
  
  // For global mode: use lightweight endpoint to avoid timeouts
  // For focused mode: fetch full data for selected node (with locus tag filter)
  // When in focused mode, viewState.selectedNodeId should be a locus_tag
  const {
    networkData,
    networkProperties,
    orthologMap,
    loading,
    error,
    availableScoreTypes,
  } = useNetworkData({
    speciesAcronym,
    isolateName,
    locusTag: isGlobalMode ? undefined : (ViewStateUtils.isFocused(viewState) ? (viewState as { selectedNodeId: string }).selectedNodeId : selectedLocusTag || undefined),
    scoreType,
    scoreThreshold,
    showOrthologs,
    enabled: !!speciesAcronym && isAuthenticated,
    useLightweight: isGlobalMode, // Use lightweight endpoint in global mode, full endpoint in focused mode
  });

  // Store global network data when fetched
  useEffect(() => {
    if (isGlobalMode && networkData && networkData.nodes.length > 0) {
      const enriched = enrichNetworkData(networkData, orthologMap, showOrthologs);
      globalNetworkDataRef.current = {
        nodes: enriched.enrichedNodes,
        edges: enriched.enrichedEdges,
      };
    }
  }, [isGlobalMode, networkData, orthologMap, showOrthologs]);

  // Sync loading state with parent
  useEffect(() => {
    if (setLoading) {
      setLoading(loading);
    }
  }, [loading, setLoading]);

  // Sync displayThreshold with scoreThreshold when it changes externally
  useEffect(() => {
    setDisplayThreshold(scoreThreshold);
  }, [scoreThreshold]);

  // Store original nodes/edges when network data changes
  // Also initialize expansion path with the starting node
  // Only initialize when we have a selectedLocusTag from props (initial load) or when explicitly needed
  // Don't reset when switching from global to focused mode via node click
  const previousSelectedLocusTagRef = useRef<string | null | undefined>(selectedLocusTag);
  useEffect(() => {
    // Only initialize expansion state when:
    // 1. We have networkData and selectedLocusTag from props (initial load)
    // 2. The selectedLocusTag actually changed (not just networkData)
    // 3. We're not in global mode (global mode doesn't need expansion initialization)
    const shouldInitialize = networkData && 
                            selectedLocusTag && 
                            selectedLocusTag !== previousSelectedLocusTagRef.current &&
                            !isGlobalMode;
    
    if (shouldInitialize) {
      previousSelectedLocusTagRef.current = selectedLocusTag;
      const enriched = enrichNetworkData(networkData, orthologMap, showOrthologs);
      originalNodesRef.current = enriched.enrichedNodes;
      originalEdgesRef.current = enriched.enrichedEdges;
      
      // Find the starting node and initialize path with it
      const startingNode = enriched.enrichedNodes.find(
        node => node.locus_tag === selectedLocusTag || node.id === selectedLocusTag
      );
      
      if (startingNode) {
        const initialState = createInitialExpansionState();
        initialState.allExpandedNodes = new Map(
          enriched.enrichedNodes.map(node => [node.id, { ...node, expansionLevel: 0 }])
        );
        // Tag original edges with expansionLevel 0
        initialState.allExpandedEdges = enriched.enrichedEdges.map(edge => ({
          ...edge,
          expansionLevel: 0,
        }));
        
        // Add starting node to path as level 0
        initialState.path.nodes = [{
          locusTag: startingNode.locus_tag || startingNode.id,
          nodeId: startingNode.id,
          node: startingNode,
          expandedAt: Date.now(),
          level: 0,
        }];
        initialState.path.currentLevel = 0;
        
        setExpansionState(initialState);
      } else {
        // Reset expansion state when base network changes
        setExpansionState(createInitialExpansionState());
      }
    } else if (networkData && !selectedLocusTag && !isGlobalMode) {
      // Update original nodes/edges ref even if we don't initialize expansion state
      // (e.g., when switching to focused mode from global)
      const enriched = enrichNetworkData(networkData, orthologMap, showOrthologs);
      originalNodesRef.current = enriched.enrichedNodes;
      originalEdgesRef.current = enriched.enrichedEdges;
    }
  }, [networkData, orthologMap, showOrthologs, selectedLocusTag, isGlobalMode]);

  // Determine which nodes/edges to display based on view mode
  // Memoize based on stable dependencies to prevent unnecessary recalculations
  // Only recalculate when loading is complete to prevent multiple renders during data fetching
  const { enrichedNodes, enrichedEdges } = useMemo(() => {
    // During loading, return last stable data to prevent flickering
    // Only return empty if we have no previous data
    if (loading) {
      if (lastStableDataRef.current) {
        return lastStableDataRef.current;
      }
      return { enrichedNodes: [], enrichedEdges: [] };
    }
    
    // In global mode: show all nodes from global network data
    if (isGlobalMode) {
      if (globalNetworkDataRef.current) {
        const result = {
          enrichedNodes: globalNetworkDataRef.current.nodes,
          enrichedEdges: globalNetworkDataRef.current.edges,
        };
        lastStableDataRef.current = result;
        return result;
      }
      // Fallback to current network data if global not loaded yet
      if (networkData) {
        const result = enrichNetworkData(networkData, orthologMap, showOrthologs);
        lastStableDataRef.current = result;
        return result;
      }
      return { enrichedNodes: [], enrichedEdges: [] };
    }
    
    // In focused mode: show only selected node and its interactions
    // Only process if we have network data and not loading
    if (!networkData || !ViewStateUtils.isFocused(viewState)) {
      return { enrichedNodes: [], enrichedEdges: [] };
    }
    
    const baseEnriched = enrichNetworkData(networkData, orthologMap, showOrthologs);
    // Type narrowing: we know viewState is FocusedViewState here
    const focusedViewState = viewState as { mode: 'focused'; selectedNodeId: string };
    const selectedNodeId = focusedViewState.selectedNodeId;
    
    // Find the selected node (could be matched by id or locus_tag)
    const selectedNode = baseEnriched.enrichedNodes.find(n => 
      n.id === selectedNodeId || n.locus_tag === selectedNodeId
    );
    
    if (!selectedNode) {
      // If node not found, return empty (this can happen during initial data loading)
      return { enrichedNodes: [], enrichedEdges: [] };
    }
    
    // Build set of connected node IDs (using protein IDs for matching edges)
    const connectedNodeIds = new Set<string>([selectedNode.id]);
    
    // Find all nodes connected to the selected node (match by protein ID in edges)
    baseEnriched.enrichedEdges.forEach(edge => {
      if (edge.source === selectedNode.id) {
        connectedNodeIds.add(edge.target);
      } else if (edge.target === selectedNode.id) {
        connectedNodeIds.add(edge.source);
      }
    });
    
    // Filter nodes and edges
    const filteredNodes = baseEnriched.enrichedNodes.filter(n => connectedNodeIds.has(n.id));
    const filteredEdges = baseEnriched.enrichedEdges.filter(e => 
      connectedNodeIds.has(e.source) && connectedNodeIds.has(e.target)
    );
      
    // If there are expansions, merge them
    if (expansionState.allExpandedNodes.size > 0) {
      const allNodes = new Map<string, PPINetworkNode>();
      filteredNodes.forEach(node => {
        allNodes.set(node.id, node);
      });
      expansionState.allExpandedNodes.forEach((node: PPINetworkNode & { expansionLevel?: number }, id: string) => {
        allNodes.set(id, node);
      });
      
      const edgeMap = new Map<string, PPINetworkEdge & { expansionLevel?: number }>();
      filteredEdges.forEach(edge => {
        const key = `${edge.source}-${edge.target}`;
        const edgeWithLevel = edge as PPINetworkEdge & { expansionLevel?: number };
        edgeMap.set(key, { 
          ...edge, 
          expansionLevel: edgeWithLevel.expansionLevel ?? 0 
        } as PPINetworkEdge & { expansionLevel?: number });
      });
      expansionState.allExpandedEdges.forEach(edge => {
        const key = `${edge.source}-${edge.target}`;
        const existing = edgeMap.get(key);
        if (!existing || (edge.weight ?? 0) > (existing.weight ?? 0)) {
          edgeMap.set(key, edge);
        }
      });
      
      const result = {
        enrichedNodes: Array.from(allNodes.values()),
        enrichedEdges: Array.from(edgeMap.values()),
      };
      lastStableDataRef.current = result;
      return result;
    }
      
    // No expansions - return filtered nodes/edges
    const result = {
      enrichedNodes: filteredNodes,
      enrichedEdges: filteredEdges,
    };
    lastStableDataRef.current = result;
    return result;
  }, [
    loading, // Wait for loading to complete before recalculating
    networkData, 
    orthologMap, 
    showOrthologs, 
    expansionState.allExpandedNodes.size, // Only depend on size, not the entire map (prevents unnecessary recalculations)
    expansionState.allExpandedEdges.length, // Only depend on length, not the entire array (prevents unnecessary recalculations)
    isGlobalMode, 
    viewState, // Depend on entire viewState object for proper change detection
  ]);

  // Stabilize nodes/edges arrays to prevent unnecessary graph recreations
  // Use a ref to cache the previous arrays and only update when IDs actually change
  const stableNodesRef = useRef<typeof enrichedNodes>([]);
  const stableEdgesRef = useRef<typeof enrichedEdges>([]);
  const nodesIdKeyRef = useRef<string>('');
  const edgesIdKeyRef = useRef<string>('');

  const stableNodes = useMemo(() => {
    const idKey = `${enrichedNodes.length}-${enrichedNodes.map(n => n.id).sort().join(',')}`;
    if (idKey !== nodesIdKeyRef.current || loading) {
      nodesIdKeyRef.current = idKey;
      stableNodesRef.current = enrichedNodes;
      return enrichedNodes;
    }
    return stableNodesRef.current;
  }, [enrichedNodes, loading]);

  const stableEdges = useMemo(() => {
    const idKey = `${enrichedEdges.length}-${enrichedEdges.map(e => `${e.source}-${e.target}`).sort().join(',')}`;
    if (idKey !== edgesIdKeyRef.current || loading) {
      edgesIdKeyRef.current = idKey;
      stableEdgesRef.current = enrichedEdges;
      return enrichedEdges;
    }
    return stableEdgesRef.current;
  }, [enrichedEdges, loading]);
  
  // Store stable data when not loading to use during future loading states
  // This prevents flickering during mode switches
  useEffect(() => {
    if (!loading && enrichedNodes.length > 0) {
      lastStableDataRef.current = { enrichedNodes, enrichedEdges };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, enrichedNodes.length, enrichedEdges.length]); // Only depend on lengths to prevent unnecessary updates

  // Handle node click - behavior depends on view mode
  const handleNodeClick = useCallback(
    (node: PPINetworkNode, event?: MouseEvent) => {
      setSelectedNode(node);
      setPopupEdge(null); // Close edge popup if open
      
      // In global mode: clicking a node switches to focused mode
      if (isGlobalMode) {
        // Use locus_tag if available, otherwise use node id
        // When switching to focused mode, we need to fetch full network data for this node
        const nodeIdentifier = node.locus_tag || node.id;
        
        // Batch state updates to prevent multiple re-renders
        // First set view state - this will trigger data fetch
        setViewState(ViewStateUtils.createFocused(nodeIdentifier));
        
        // Initialize expansion state with just the selected node
        // This will be updated once the network data is loaded
        const initialState = createInitialExpansionState();
        initialState.allExpandedNodes = new Map(
          [[node.id, { ...node, expansionLevel: 0 }]]
        );
        setExpansionState(initialState);
        
        // Don't show popup in global mode - directly switch to focused
        // The focused view will fetch full network data for this node
        return;
      }
      
      // In focused mode: show popup as before
      if (event) {
        setPopupNode({ node, x: event.clientX, y: event.clientY });
      }
      
      // Note: We intentionally don't call onFeatureSelect here to avoid
      // changing the view and keeping JBrowse and network view in sync
    },
    [isGlobalMode]
  );

  // Handle edge click - show edge information
  const handleEdgeClick = useCallback(
    (edge: PPINetworkEdge & { edgeType?: string; orthology_type?: string; expansionLevel?: number }, event?: MouseEvent) => {
      setPopupNode(null); // Close node popup if open
      
      // Show edge popup at click position
      if (event) {
        setPopupEdge({ edge, x: event.clientX, y: event.clientY });
      }
    },
    []
  );

  // Handle reset expansions
  const handleResetExpansions = useCallback(() => {
    setExpansionState(clearExpansions());
    // Reset view to original
    if (graphRef.current) {
      graphRef.current.resetView();
    }
  }, []);

  // Handle reset view (also resets expansions)
  const handleResetView = useCallback(() => {
    handleResetExpansions();
    // If in focused mode, switch back to global
    if (ViewStateUtils.isFocused(viewState)) {
      setViewState(ViewStateUtils.createGlobal());
      setSelectedNode(null);
      setPopupNode(null);
      setPopupEdge(null);
    }
  }, [handleResetExpansions, viewState]);

  // Handle return to global view
  const handleReturnToGlobal = useCallback(() => {
    setViewState(ViewStateUtils.createGlobal());
    setExpansionState(createInitialExpansionState());
    setSelectedNode(null);
    setPopupNode(null);
    setPopupEdge(null);
  }, []);

  // Handle score type change
  const handleScoreTypeChange = useCallback((newScoreType: string) => {
    setScoreType(newScoreType);
  }, []);

  // Handle threshold change with debounce
  const handleThresholdChange = useCallback((newThreshold: number) => {
    setDisplayThreshold(newThreshold);
    
    if (thresholdDebounceRef.current) {
      clearTimeout(thresholdDebounceRef.current);
    }
    
    thresholdDebounceRef.current = setTimeout(() => {
      setScoreThreshold(newThreshold);
    }, 500);
  }, []);
  
  // Cleanup debounce timeout on unmount
  useEffect(() => {
    return () => {
      if (thresholdDebounceRef.current) {
        clearTimeout(thresholdDebounceRef.current);
      }
    };
  }, []);

  // Handle ortholog toggle
  const handleOrthologToggle = useCallback((enabled: boolean) => {
    setShowOrthologs(enabled);
  }, []);

  // Handle node expansion
  const handleExpandNode = useCallback(async (node: PPINetworkNode) => {
    const locusTag = node.locus_tag || node.id;
    const currentLevel = expansionState.path.currentLevel;

    // Check if we can expand
    if (!canExpandNode(currentLevel)) {
      alert(`Maximum expansion depth (${currentLevel}) reached. Cannot expand further.`);
      return;
    }

    // Check if already expanded
    if (isNodeExpanded(expansionState, locusTag)) {
      // Already expanded, could show a message or do nothing
      return;
    }

    try {
      setExpandingNodeId(node.id);
      
      // Fetch interactions for this node
      const expansionQuery = {
        score_type: scoreType,
        score_threshold: scoreThreshold,
        species_acronym: speciesAcronym,
        isolate_name: isolateName,
        locus_tag: locusTag,
        include_properties: false,
      };

      const expansionData = await PPIService.getNetworkData(expansionQuery);
      
      if (expansionData && expansionData.nodes && expansionData.edges) {
        // Enrich with orthologs if enabled
        const enriched = enrichNetworkData(
          { nodes: expansionData.nodes, edges: expansionData.edges },
          orthologMap,
          showOrthologs
        );

        // Filter to only include nodes DIRECTLY connected to the expanding node (1-hop neighbors)
        // Find all node IDs that are directly connected via edges to the expanding node
        const directNeighborIds = new Set<string>();
        
        // Find direct neighbors: nodes that have an edge with the expanding node
        enriched.enrichedEdges.forEach(edge => {
          if (edge.source === node.id) {
            directNeighborIds.add(edge.target);
          } else if (edge.target === node.id) {
            directNeighborIds.add(edge.source);
          }
        });

        // Only include:
        // 1. The expanding node itself (for reference)
        // 2. Direct neighbors (nodes with edges to the expanding node)
        const connectedNodes = enriched.enrichedNodes.filter(n => {
          return n.id === node.id || directNeighborIds.has(n.id);
        });

        // Filter edges to only include edges where at least one endpoint is a direct neighbor of the expanding node
        // This means: edges from expanding node to neighbors, or edges between neighbors
        const filteredEdges = enriched.enrichedEdges.filter(edge => {
          const sourceIsExpanding = edge.source === node.id;
          const targetIsExpanding = edge.target === node.id;
          const sourceIsNeighbor = directNeighborIds.has(edge.source);
          const targetIsNeighbor = directNeighborIds.has(edge.target);
          const isNotSelfLoop = edge.source !== edge.target;
          
          // Include if:
          // - Edge connects expanding node to a neighbor, OR
          // - Edge connects two neighbors (for context)
          // But exclude self-loops
          return isNotSelfLoop && (
            (sourceIsExpanding && targetIsNeighbor) ||
            (targetIsExpanding && sourceIsNeighbor) ||
            (sourceIsNeighbor && targetIsNeighbor)
          );
        });

        // Merge expansion data
        const newState = mergeExpansionData(
          expansionState,
          {
            nodes: connectedNodes,
            edges: filteredEdges,
          },
          node,
          currentLevel + 1
        );

            setExpansionState(newState);
            
            // Don't reset view - let the graph preserve existing positions
            // The new nodes will be positioned based on their expansion level
            // without disrupting existing node positions
      }
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Error expanding node:', error);
      alert('Failed to expand node interactions. Please try again.');
    } finally {
      setExpandingNodeId(null);
    }
  }, [expansionState, scoreType, scoreThreshold, speciesAcronym, isolateName, orthologMap, showOrthologs]);


  // Early returns for edge cases
  if (!speciesAcronym) {
    return <EmptyState message="Please select a species to view the network." variant="no-species" />;
  }

  if (!isAuthenticated) {
    return <AuthRequired />;
  }

  // Allow global view even without selectedLocusTag
  // if (!selectedLocusTag && !isGlobalMode) {
  //   return <EmptyState variant="select-gene" />;
  // }

  const hasData = networkData && networkData.nodes.length > 0;

  return (
    <div className={styles.networkView}>
      {/* Controls - Always visible */}
        <NetworkControls
          scoreType={scoreType}
          displayThreshold={displayThreshold}
          showOrthologs={showOrthologs}
          availableScoreTypes={availableScoreTypes}
          onScoreTypeChange={handleScoreTypeChange}
          onThresholdChange={handleThresholdChange}
          onOrthologToggle={handleOrthologToggle}
          onResetView={handleResetView}
        />

      {/* Error Message */}
      {error && (
        <div className={styles.networkViewError}>
          <p>Error loading network data: {error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && !networkData && !error && (
        <div className={styles.networkViewLoading}>
          <p>Loading network data...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && !hasData && <EmptyState />}

      {/* Network Stats */}
      {hasData && networkProperties && (
        <NetworkStats properties={networkProperties} showOrthologs={showOrthologs} />
      )}

      {/* Return to Global View button (shown in focused mode) */}
      {ViewStateUtils.isFocused(viewState) && (
        <div className={styles.returnToGlobalContainer}>
          <button
            className={styles.returnToGlobalButton}
            onClick={handleReturnToGlobal}
            title="Return to global network view"
          >
            ← Back to Global View
          </button>
        </div>
      )}

      {/* Expansion Breadcrumb */}
      {!isGlobalMode && expansionState.path.nodes.length > 0 && (
        <ExpansionBreadcrumb
          expansionState={expansionState}
          onNavigateToLevel={(level) => {
            const newState = navigateToPathLevel(
              expansionState,
              level,
              originalNodesRef.current,
              originalEdgesRef.current
            );
            setExpansionState(newState);
          }}
          onClearAll={handleResetExpansions}
        />
      )}

      {/* Export Controls */}
      {expansionState.path.nodes.length > 0 && (
        <div className={styles.exportControls}>
          <button
            className={styles.exportButton}
            onClick={() => {
              exportExpansionPathJSON(expansionState, originalNodesRef.current, originalEdgesRef.current);
            }}
            title="Export expansion path as JSON"
          >
            Export Path (JSON)
          </button>
          <button
            className={styles.exportButton}
            onClick={() => {
              const cy = graphRef.current?.getCytoscapeInstance();
              if (cy) {
                exportNetworkImage(cy);
              } else {
                alert('Graph not ready. Please wait a moment and try again.');
              }
            }}
            title="Export network visualization as PNG"
          >
            Export Image (PNG)
          </button>
        </div>
      )}

      {/* Network Visualization */}
      {hasData && !error && (
        <div className={styles.networkVisualization}>
        <NetworkGraph
          ref={graphRef}
          nodes={stableNodes}
          edges={stableEdges}
            showOrthologs={showOrthologs}
            viewMode={viewState.mode}
            currentExpansionLevel={expansionState.path.currentLevel}
            expansionPath={expansionState.path.nodes.map(p => ({ nodeId: p.nodeId, level: p.level }))}
            onNodeClick={handleNodeClick}
            onEdgeClick={handleEdgeClick}
            selectedNode={selectedNode}
          />
        </div>
      )}

      {/* Node Info Popup */}
      {popupNode && (
        <NodeInfoPopup
          node={popupNode.node}
          x={popupNode.x}
          y={popupNode.y}
          expansionState={expansionState}
          interactions={enrichedEdges.filter(e => 
            e.source === popupNode.node.id || e.target === popupNode.node.id
          )}
          connectedNodes={new Map(enrichedNodes.map(n => [n.id, n]))}
          onClose={() => setPopupNode(null)}
          onExpand={handleExpandNode}
          isExpanding={expandingNodeId === popupNode.node.id}
        />
      )}

      {/* Edge Info Popup */}
      {popupEdge && (
        <EdgeInfoPopup
          edge={popupEdge.edge}
          sourceNode={enrichedNodes.find(n => n.id === popupEdge.edge.source)}
          targetNode={enrichedNodes.find(n => n.id === popupEdge.edge.target)}
          x={popupEdge.x}
          y={popupEdge.y}
          onClose={() => setPopupEdge(null)}
        />
      )}
    </div>
  );
};

export default NetworkView;
