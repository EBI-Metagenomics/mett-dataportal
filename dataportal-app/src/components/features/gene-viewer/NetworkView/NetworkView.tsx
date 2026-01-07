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
  const thresholdDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const graphRef = useRef<NetworkGraphRef>(null);
  const originalNodesRef = useRef<PPINetworkNode[]>([]);
  const originalEdgesRef = useRef<PPINetworkEdge[]>([]);

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
    showOrthologs,
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

  // Store original nodes/edges when network data changes
  // Also initialize expansion path with the starting node
  useEffect(() => {
    if (networkData && selectedLocusTag) {
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
    }
  }, [networkData, orthologMap, showOrthologs, selectedLocusTag]);

  // Enrich nodes with ortholog information and merge with expansions
  const { enrichedNodes, enrichedEdges } = useMemo(() => {
    const baseEnriched = enrichNetworkData(networkData, orthologMap, showOrthologs);
    
    // If there are expansions, merge them with base network
    if (expansionState.allExpandedNodes.size > 0) {
      // Merge base nodes with expanded nodes
      const allNodes = new Map<string, PPINetworkNode>();
      
      // Add base nodes
      baseEnriched.enrichedNodes.forEach(node => {
        allNodes.set(node.id, node);
      });
      
      // Add expanded nodes (they override base if same ID)
      expansionState.allExpandedNodes.forEach((node: PPINetworkNode & { expansionLevel?: number }, id: string) => {
        allNodes.set(id, node);
      });
      
      // Merge edges (keep unique, highest weight wins)
      // Tag base edges with expansionLevel 0 if not already set
      const baseEdgesWithLevel = baseEnriched.enrichedEdges.map(edge => ({
        ...edge,
        expansionLevel: (edge as PPINetworkEdge & { expansionLevel?: number }).expansionLevel ?? 0,
      }));
      
      const edgeMap = new Map<string, PPINetworkEdge & { expansionLevel?: number }>();
      [...baseEdgesWithLevel, ...expansionState.allExpandedEdges].forEach(edge => {
        const key = `${edge.source}-${edge.target}`;
        const existing = edgeMap.get(key);
        if (!existing || (edge.weight ?? 0) > (existing.weight ?? 0)) {
          edgeMap.set(key, edge);
        }
      });
      
      return {
        enrichedNodes: Array.from(allNodes.values()),
        enrichedEdges: Array.from(edgeMap.values()),
      };
    }
    
    return baseEnriched;
  }, [networkData, orthologMap, showOrthologs, expansionState]);

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
