import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useNetworkData, type NetworkLimitMode, type SpeciesScope } from '../../../../hooks/useNetworkData';
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
import styles from './NetworkView.module.scss';

interface NetworkViewProps {
  speciesAcronym?: string;
  isolateName?: string;
  selectedLocusTag?: string | null;
  setLoading?: React.Dispatch<React.SetStateAction<boolean>>;
  onFeatureSelect?: (feature: { data: { locus_tag?: string; gene_name?: string; product?: string; uniprot_id?: string; isolate_name?: string; species_acronym?: string } }) => void;
  /** Navigate JBrowse to the gene for this locus tag (current genome). Used for "View in JBrowse" from node popup. */
  onViewInJBrowse?: (locusTag: string) => void;
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
  onViewInJBrowse,
}) => {
  const { isAuthenticated } = useAuth();
  const [scoreType, setScoreType] = useState<string>('ds_score');
  const [scoreThreshold, setScoreThreshold] = useState<number>(0.9);
  const [displayThreshold, setDisplayThreshold] = useState<number>(0.9);
  const [limitMode, setLimitMode] = useState<NetworkLimitMode>('topN');
  const [topN, setTopN] = useState<number>(10);
  const [speciesScope, setSpeciesScope] = useState<SpeciesScope>('current');
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
  const thresholdDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const graphRef = useRef<NetworkGraphRef>(null);
  const originalNodesRef = useRef<PPINetworkNode[]>([]);
  const originalEdgesRef = useRef<PPINetworkEdge[]>([]);

  // Locus tags from expanded nodes so orthologs are fetched for them too
  const expandedLocusTags = useMemo(() => {
    const tags: string[] = [];
    expansionState.allExpandedNodes.forEach((node) => {
      const n = node as PPINetworkNode & { nodeType?: string };
      if (n.nodeType !== 'ortholog') {
        const tag = n.locus_tag || n.id;
        if (tag) tags.push(tag);
      }
    });
    return tags;
  }, [expansionState]);

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
    locusTag: selectedLocusTag || undefined,
    scoreType,
    scoreThreshold,
    topN,
    limitMode,
    speciesScope,
    showOrthologs,
    extraLocusTagsForOrthologs: expandedLocusTags.length > 0 ? expandedLocusTags : undefined,
    enabled: !!speciesAcronym && !!selectedLocusTag && isAuthenticated,
  });

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

  // Store original nodes/edges and init expansion path when base network changes only.
  // Do NOT reset when showOrthologs/orthologMap change (toggling orthologs) or when selectedLocusTag
  // changes only (e.g. "View in JBrowse" updates the viewed gene); only reset when networkData changes.
  useEffect(() => {
    if (networkData && selectedLocusTag) {
      const enriched = enrichNetworkData(networkData, orthologMap, showOrthologs);
      originalNodesRef.current = enriched.enrichedNodes;
      originalEdgesRef.current = enriched.enrichedEdges;

      const startingNode = enriched.enrichedNodes.find(
        node => node.locus_tag === selectedLocusTag || node.id === selectedLocusTag
      );

      if (startingNode) {
        const initialState = createInitialExpansionState();
        initialState.allExpandedNodes = new Map(
          enriched.enrichedNodes.map(node => [node.id, { ...node, expansionLevel: 0 }])
        );
        initialState.allExpandedEdges = enriched.enrichedEdges.map(edge => ({
          ...edge,
          expansionLevel: 0,
        }));
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
        setExpansionState(createInitialExpansionState());
      }
    }
    // Only depend on networkData so "View in JBrowse" (which updates selectedLocusTag) does not reset expansion
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkData]);

  // Enrich nodes with ortholog information and merge with expansions.
  // When there are expansions: merge base + expanded PPI nodes, then enrich so orthologs
  // are added for all nodes (including expanded); preserve expansion ortholog nodes and levels.
  const { enrichedNodes, enrichedEdges } = useMemo(() => {
    if (!networkData?.nodes) {
      return { enrichedNodes: [], enrichedEdges: [] as PPINetworkEdge[] };
    }

    const baseNodes = networkData.nodes;
    const baseEdges = networkData.edges || [];

    if (expansionState.allExpandedNodes.size === 0) {
      return enrichNetworkData(networkData, orthologMap, showOrthologs);
    }

    // Merge base + expanded: PPI nodes only for enrichment (enrichNetworkData overwrites nodeType)
    const mergedPpiNodes = new Map<string, PPINetworkNode & { expansionLevel?: number }>();
    baseNodes.forEach(n => mergedPpiNodes.set(n.id, { ...n, expansionLevel: 0 }));
    expansionState.allExpandedNodes.forEach((node, id) => {
      const n = node as PPINetworkNode & { nodeType?: string; expansionLevel?: number };
      if (n.nodeType !== 'ortholog') {
        mergedPpiNodes.set(id, n);
      }
    });

    const mergedPpiEdges = new Map<string, PPINetworkEdge & { expansionLevel?: number }>();
    baseEdges.forEach(e => mergedPpiEdges.set(`${e.source}-${e.target}`, { ...e, expansionLevel: 0 }));
    expansionState.allExpandedEdges.forEach(e => {
      const key = `${e.source}-${e.target}`;
      const existing = mergedPpiEdges.get(key);
      if (!existing || (e.weight ?? 0) > (existing.weight ?? 0)) {
        mergedPpiEdges.set(key, { ...e, expansionLevel: (e as PPINetworkEdge & { expansionLevel?: number }).expansionLevel ?? 0 });
      }
    });

    const mergedNetwork = {
      nodes: Array.from(mergedPpiNodes.values()),
      edges: Array.from(mergedPpiEdges.values()),
    };
    const fullEnriched = enrichNetworkData(mergedNetwork, orthologMap, showOrthologs);

    // Preserve expansionLevel from state and expansion ortholog nodes (from previous expand with showOrthologs on)
    const nodeMap = new Map<string, PPINetworkNode & { expansionLevel?: number }>();
    fullEnriched.enrichedNodes.forEach(n => {
      const expanded = expansionState.allExpandedNodes.get(n.id) as (PPINetworkNode & { expansionLevel?: number }) | undefined;
      const level = expanded?.expansionLevel ?? (n as PPINetworkNode & { expansionLevel?: number }).expansionLevel;
      nodeMap.set(n.id, { ...n, expansionLevel: level });
    });
    expansionState.allExpandedNodes.forEach((node, id) => {
      const n = node as PPINetworkNode & { nodeType?: string; expansionLevel?: number };
      if (n.nodeType === 'ortholog') nodeMap.set(id, n);
    });

    const edgeMap = new Map<string, PPINetworkEdge & { expansionLevel?: number }>();
    fullEnriched.enrichedEdges.forEach(e => {
      const key = `${e.source}-${e.target}`;
      const fromState = expansionState.allExpandedEdges.find(
        edge => (edge.source === e.source && edge.target === e.target) || (edge.source === e.target && edge.target === e.source)
      ) as (PPINetworkEdge & { expansionLevel?: number }) | undefined;
      const level = fromState?.expansionLevel ?? (e as PPINetworkEdge & { expansionLevel?: number }).expansionLevel ?? 0;
      edgeMap.set(key, { ...e, expansionLevel: level });
    });
    expansionState.allExpandedEdges.forEach(e => {
      const key = `${e.source}-${e.target}`;
      if (!edgeMap.has(key)) edgeMap.set(key, { ...e, expansionLevel: (e as PPINetworkEdge & { expansionLevel?: number }).expansionLevel ?? 0 });
    });

    return {
      enrichedNodes: Array.from(nodeMap.values()),
      enrichedEdges: Array.from(edgeMap.values()),
    };
  }, [networkData, orthologMap, showOrthologs, expansionState]);

  // Stable expansion path so NetworkGraph does not re-create on every render (e.g. when only selectedNode changes)
  const expansionPath = useMemo(
    () => expansionState.path.nodes.map(p => ({ nodeId: p.nodeId, level: p.level })),
    [expansionState]
  );

  // Handle node click - only show popup, don't change view
  const handleNodeClick = useCallback(
    (node: PPINetworkNode, event?: MouseEvent) => {
      setSelectedNode(node);
      setPopupEdge(null); // Close edge popup if open
      
      // Show popup at click position
      if (event) {
        setPopupNode({ node, x: event.clientX, y: event.clientY });
      }
      
      // Note: We intentionally don't call onFeatureSelect here to avoid
      // changing the view and keeping JBrowse and network view in sync
    },
    []
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
  }, [handleResetExpansions]);

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

  const handleLimitModeChange = useCallback((mode: NetworkLimitMode) => {
    setLimitMode(mode);
  }, []);

  const handleTopNChange = useCallback((n: number) => {
    setTopN(n);
  }, []);

  const handleSpeciesScopeChange = useCallback((scope: SpeciesScope) => {
    setSpeciesScope(scope);
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

      const effectiveSpecies = speciesScope === 'all' ? undefined : speciesAcronym;

      // Use same API and filters as the main view: Top N → neighborhood, Score threshold → network
      let expansionData: { nodes: PPINetworkNode[]; edges: PPINetworkEdge[] } | null = null;

      if (limitMode === 'topN') {
        const neighborhood = await PPIService.getProteinNeighborhood({
          locus_tag: locusTag,
          species_acronym: effectiveSpecies ?? undefined,
          n: topN,
          score_type: scoreType,
          score_threshold: 0,
        });
        expansionData = neighborhood?.network_data ?? null;
      } else {
        expansionData = await PPIService.getNetworkData({
          score_type: scoreType,
          score_threshold: scoreThreshold,
          species_acronym: effectiveSpecies ?? undefined,
          isolate_name: isolateName ?? undefined,
          locus_tag: locusTag,
          include_properties: false,
        });
      }

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
      console.error('Error expanding node:', error);
      alert('Failed to expand node interactions. Please try again.');
    } finally {
      setExpandingNodeId(null);
    }
  }, [expansionState, limitMode, topN, scoreType, scoreThreshold, speciesAcronym, speciesScope, isolateName, orthologMap, showOrthologs]);


  // Early returns for edge cases
  if (!speciesAcronym) {
    return <EmptyState message="Please select a species to view the network." variant="no-species" />;
  }

  if (!isAuthenticated) {
    return <AuthRequired />;
  }

  if (!selectedLocusTag) {
    return <EmptyState variant="select-gene" />;
  }

  const hasData = networkData && networkData.nodes.length > 0;

  return (
    <div className={styles.networkView}>
      {/* Controls - Always visible */}
        <NetworkControls
          scoreType={scoreType}
          displayThreshold={displayThreshold}
          limitMode={limitMode}
          topN={topN}
          speciesScope={speciesScope}
          showOrthologs={showOrthologs}
          availableScoreTypes={availableScoreTypes}
          onScoreTypeChange={handleScoreTypeChange}
          onThresholdChange={handleThresholdChange}
          onLimitModeChange={handleLimitModeChange}
          onTopNChange={handleTopNChange}
          onSpeciesScopeChange={handleSpeciesScopeChange}
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
      {hasData && (
        <NetworkStats
          properties={networkProperties ?? null}
          nodeCount={networkData?.nodes?.length}
          edgeCount={networkData?.edges?.length}
          showOrthologs={showOrthologs}
        />
      )}

      {/* Expansion Breadcrumb */}
      {expansionState.path.nodes.length > 0 && (
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
            nodes={enrichedNodes}
            edges={enrichedEdges}
            showOrthologs={showOrthologs}
            currentExpansionLevel={expansionState.path.currentLevel}
            expansionPath={expansionPath}
            focalNodeId={expansionState.path.nodes[0]?.nodeId ?? null}
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
          isOrthologNode={(popupNode.node as PPINetworkNode & { nodeType?: string }).nodeType === 'ortholog'}
          onClose={() => setPopupNode(null)}
          onExpand={handleExpandNode}
          isExpanding={expandingNodeId === popupNode.node.id}
          onViewInJBrowse={onViewInJBrowse}
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
