import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import { useNetworkData } from '../../../../hooks/useNetworkData';
import { useAuth } from '../../../../hooks/useAuth';
import { PPINetworkNode, PPINetworkEdge } from '../../../../interfaces/PPI';
import TokenInput from '../../../shared/TokenInput/TokenInput';
import styles from './NetworkView.module.scss';

interface NetworkViewProps {
  speciesAcronym?: string;
  isolateName?: string;
  selectedLocusTag?: string | null; // Optional locus_tag to filter network to neighborhood view
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
  onFeatureSelect,
}) => {
  const { isAuthenticated } = useAuth();
  const [scoreType, setScoreType] = useState<string>('ds_score');
  const [scoreThreshold, setScoreThreshold] = useState<number>(0.8);
  const [showOrthologs, setShowOrthologs] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<PPINetworkNode | null>(null);
  const [showTokenInput, setShowTokenInput] = useState<boolean>(false);

  const {
    networkData,
    networkProperties,
    orthologMap,
    loading,
    error,
    refreshNetwork,
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
  React.useEffect(() => {
    if (setLoading) {
      setLoading(loading);
    }
  }, [loading, setLoading]);

  // Enrich nodes with ortholog information and add ortholog nodes/edges
  const { enrichedNodes, enrichedEdges } = useMemo(() => {
    if (!networkData?.nodes) return { enrichedNodes: [], enrichedEdges: networkData?.edges || [] };

    const ppiNodes = networkData.nodes.map((node) => {
      const orthologs = node.locus_tag ? orthologMap.get(node.locus_tag) || [] : [];
      return {
        ...node,
        hasOrthologs: orthologs.length > 0,
        orthologCount: orthologs.length,
        nodeType: 'ppi' as const,
      };
    });

    // If showOrthologs is enabled, add ortholog nodes and edges
    if (showOrthologs && orthologMap.size > 0) {
      const orthologNodeMap = new Map<string, PPINetworkNode & { nodeType: 'ortholog' }>();
      const orthologEdges: PPINetworkEdge[] = [];

      // Process orthologs and create nodes/edges
      orthologMap.forEach((orthologs, sourceLocusTag) => {
        // Find the source PPI node ID (could be locus_tag or uniprot_id)
        const sourceNode = ppiNodes.find(n => n.locus_tag === sourceLocusTag);
        if (!sourceNode) return; // Skip if source node not found

        orthologs.forEach((ortholog) => {
          const orthologLocusTag = ortholog.locus_tag_b;
          
          // Create ortholog node if it doesn't exist and isn't already a PPI node
          if (!orthologNodeMap.has(orthologLocusTag) && 
              !ppiNodes.find(n => n.locus_tag === orthologLocusTag)) {
            orthologNodeMap.set(orthologLocusTag, {
              id: orthologLocusTag,
              label: orthologLocusTag,
              locus_tag: orthologLocusTag,
              nodeType: 'ortholog',
            });
          }

          // Create edge from PPI node to ortholog node (use node IDs)
          const targetNodeId = orthologNodeMap.get(orthologLocusTag)?.id || orthologLocusTag;
          orthologEdges.push({
            source: sourceNode.id,
            target: targetNodeId,
            weight: ortholog.confidence_score || 1,
            edgeType: 'ortholog',
            orthology_type: ortholog.orthology_type,
          } as PPINetworkEdge & { edgeType: string; orthology_type?: string });
        });
      });

      return {
        enrichedNodes: [...ppiNodes, ...Array.from(orthologNodeMap.values())],
        enrichedEdges: [...networkData.edges, ...orthologEdges],
      };
    }

    return {
      enrichedNodes: ppiNodes.map(n => ({ ...n, nodeType: 'ppi' as const })),
      enrichedEdges: networkData.edges,
    };
  }, [networkData?.nodes, networkData?.edges, orthologMap, showOrthologs]);

  // Handle node click
  const handleNodeClick = useCallback(
    (node: PPINetworkNode) => {
      setSelectedNode(node);
      if (onFeatureSelect && node.locus_tag) {
        // Create a feature-like object for the feature panel
        onFeatureSelect({
          data: {
            locus_tag: node.locus_tag,
            gene_name: node.name,
            product: node.product,
            uniprot_id: node.uniprot_id,
            isolate_name: isolateName,
            species_acronym: speciesAcronym,
          },
        });
      }
    },
    [onFeatureSelect, isolateName, speciesAcronym]
  );

  // Handle score type change
  const handleScoreTypeChange = useCallback((newScoreType: string) => {
    setScoreType(newScoreType);
  }, []);

  // Handle threshold change
  const handleThresholdChange = useCallback((newThreshold: number) => {
    setScoreThreshold(newThreshold);
  }, []);

  // Handle ortholog toggle
  const handleOrthologToggle = useCallback((enabled: boolean) => {
    setShowOrthologs(enabled);
  }, []);

  if (!speciesAcronym) {
    return (
      <div className={styles.networkViewEmpty}>
        <p>Please select a species to view the network.</p>
      </div>
    );
  }

  // Check if authentication token is required and missing
  if (!isAuthenticated) {
    return (
      <>
        <div className={styles.networkViewAuthRequired}>
          <div className={styles.authMessage}>
            <div className={styles.authIcon}>🔒</div>
            <div className={styles.authContent}>
              <h3>Authentication Required</h3>
              <p>
                A JWT token is required to access network data (PPI interactions and orthologs).
                This is a temporary requirement that will be removed once data stabilizes (2-3 months).
              </p>
              <button
                className={styles.authButton}
                onClick={() => setShowTokenInput(true)}
              >
                Set Authentication Token
              </button>
            </div>
          </div>
        </div>

        {showTokenInput && (
          <div className={styles.modalOverlay} onClick={() => setShowTokenInput(false)}>
            <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
              <button
                className={styles.closeButton}
                onClick={() => setShowTokenInput(false)}
                aria-label="Close"
              >
                ×
              </button>
              <TokenInput
                onClose={() => setShowTokenInput(false)}
                onTokenSet={() => setShowTokenInput(false)}
              />
            </div>
          </div>
        )}
      </>
    );
  }

  // Check if a gene (locus_tag) is selected
  if (!selectedLocusTag) {
    return (
      <div className={styles.networkViewEmpty}>
        <div className={styles.selectGeneMessage}>
          <div className={styles.selectGeneIcon}>🧬</div>
          <div className={styles.selectGeneContent}>
            <h3>Select a Gene to View Network</h3>
            <p>
              Please select a gene from the search results or genomic context view to visualize its protein-protein interaction network.
            </p>
            <p className={styles.selectGeneHint}>
              The network will show interactions for the selected gene and its immediate neighbors.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.networkViewError}>
        <p>Error loading network data: {error}</p>
        <button onClick={refreshNetwork} className={styles.retryButton}>
          Retry
        </button>
      </div>
    );
  }

  if (loading && !networkData) {
    return (
      <div className={styles.networkViewLoading}>
        <p>Loading network data...</p>
      </div>
    );
  }

  if (!networkData || networkData.nodes.length === 0) {
    return (
      <div className={styles.networkViewEmpty}>
        <p>No network data available for this species.</p>
        <p className={styles.emptyHint}>
          Try adjusting the score threshold or selecting a different score type.
        </p>
      </div>
    );
  }

  return (
    <div className={styles.networkView}>
      {/* Controls */}
      <div className={styles.networkControls}>
        <div className={styles.controlGroup}>
          <label htmlFor="score-type">Score Type:</label>
          <select
            id="score-type"
            value={scoreType}
            onChange={(e) => handleScoreTypeChange(e.target.value)}
            className={styles.select}
          >
            {availableScoreTypes.map((type) => (
              <option key={type} value={type}>
                {type.replace('_score', '').replace('_', ' ').toUpperCase()}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.controlGroup}>
          <label htmlFor="threshold">
            Threshold: {scoreThreshold.toFixed(2)}
          </label>
          <input
            id="threshold"
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={scoreThreshold}
            onChange={(e) => handleThresholdChange(parseFloat(e.target.value))}
            className={styles.slider}
          />
        </div>

        <div className={styles.controlGroup}>
          <label>
            <input
              type="checkbox"
              checked={showOrthologs}
              onChange={(e) => handleOrthologToggle(e.target.checked)}
              className={styles.checkbox}
            />
            Show Orthologs
          </label>
        </div>

        <button onClick={refreshNetwork} className={styles.analyzeButton}>
          Analyse
        </button>
      </div>

      {/* Network Stats */}
      {networkProperties && (
        <div className={styles.networkStats}>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Nodes:</span>
            <span className={styles.statValue}>{networkProperties.num_nodes}</span>
          </div>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>Edges:</span>
            <span className={styles.statValue}>{networkProperties.num_edges}</span>
          </div>
          {networkProperties.internal_only_edges !== undefined && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Internal-only edges:</span>
              <span className={styles.statValue}>{networkProperties.internal_only_edges}</span>
            </div>
          )}
          {networkProperties.avg_degree !== undefined && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Avg. degree:</span>
              <span className={styles.statValue}>{networkProperties.avg_degree.toFixed(1)}</span>
            </div>
          )}
          {networkProperties.cross_species_edges !== undefined && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>Cross-species edges:</span>
              <span className={styles.statValue}>{networkProperties.cross_species_edges}</span>
            </div>
          )}
          {networkProperties.ppi_enrichment_p_value !== undefined && (
            <div className={styles.statItem}>
              <span className={styles.statLabel}>PPI enrichment p-value:</span>
              <span className={styles.statValue}>
                {networkProperties.ppi_enrichment_p_value.toExponential(1)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Network Visualization */}
      <div className={styles.networkVisualization}>
        <NetworkGraph
          nodes={enrichedNodes}
          edges={enrichedEdges}
          showOrthologs={showOrthologs}
          onNodeClick={handleNodeClick}
          selectedNode={selectedNode}
        />
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendColor} style={{ backgroundColor: '#4A90E2' }}></span>
          <span>PPI Interaction</span>
        </div>
        {showOrthologs && (
          <>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ backgroundColor: '#50C878', border: '2px solid #333' }}></span>
              <span>PPI Node with Orthologs</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ backgroundColor: '#FF9800', border: '1px solid #E65100', clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)', width: '12px', height: '12px' }}></span>
              <span>Ortholog Node</span>
            </div>
            <div className={styles.legendItem}>
              <span className={styles.legendColor} style={{ borderTop: '2px dashed #FF9800', width: '20px', height: '0' }}></span>
              <span>Ortholog Relationship</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * NetworkGraph component - Cytoscape.js graph visualization
 */
interface NetworkGraphProps {
  nodes: Array<PPINetworkNode & { hasOrthologs?: boolean; orthologCount?: number; nodeType?: 'ppi' | 'ortholog' }>;
  edges: PPINetworkEdge[];
  showOrthologs: boolean;
  onNodeClick: (node: PPINetworkNode) => void;
  selectedNode: PPINetworkNode | null;
}

const NetworkGraph: React.FC<NetworkGraphProps> = ({
  nodes,
  edges,
  showOrthologs,
  onNodeClick,
  selectedNode,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    // Prepare nodes data for Cytoscape
    const cyNodes = nodes.map((node) => {
      const { id, x, y, ...nodeData } = node;
      return {
        data: {
          id,
          label: node.locus_tag || node.label || id,
          ...nodeData,
        },
        position: x && y ? { x, y } : undefined,
      };
    });

    // Prepare edges data for Cytoscape
    const cyEdges = edges.map((edge, index) => {
      const edgeData = edge as PPINetworkEdge & { edgeType?: string; orthology_type?: string };
      return {
        data: {
          id: `edge-${index}`,
          source: edge.source,
          target: edge.target,
          weight: edge.weight || 1,
          edgeType: edgeData.edgeType || 'ppi',
          orthology_type: edgeData.orthology_type,
        },
      };
    });

    // Initialize Cytoscape
    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyNodes, ...cyEdges],
      style: [
        // PPI Edge styles
        {
          selector: 'edge[edgeType = "ortholog"]',
          style: {
            width: 2,
            'line-color': '#FF9800',
            'target-arrow-color': '#FF9800',
            'curve-style': 'straight',
            opacity: 0.5,
            'line-style': 'dashed',
          },
        },
        // Ortholog edge styles (dashed orange lines)
        {
          selector: 'edge',
          style: {
            width: (edge: cytoscape.EdgeSingular) => Math.sqrt(edge.data('weight') || 1) * 2,
            'line-color': '#999',
            'target-arrow-color': '#999',
            'curve-style': 'straight',
            opacity: 0.6,
          },
        },
        // Ortholog node styles (orange/diamond shape)
        {
          selector: 'node[nodeType = "ortholog"]',
          style: {
            label: 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 8,
            'font-size': '10px',
            width: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 20 : 14),
            height: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 20 : 14),
            shape: 'diamond',
            'background-color': '#FF9800',
            'border-width': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 3 : 1),
            'border-color': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? '#FF6B6B' : '#E65100'),
          },
        },
        // PPI Node styles
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 8,
            'font-size': '10px',
            width: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 24 : 16),
            height: (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 24 : 16),
            shape: 'ellipse',
            'background-color': (node: cytoscape.NodeSingular) => {
              const nodeData = node.data() as { hasOrthologs?: boolean; nodeType?: string };
              // Don't color PPI nodes green if we're showing ortholog nodes separately
              if (nodeData.nodeType === 'ortholog') return '#FF9800';
              if (showOrthologs && nodeData.hasOrthologs) return '#50C878';
              return '#4A90E2';
            },
            'border-width': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? 3 : 1),
            'border-color': (node: cytoscape.NodeSingular) => (selectedNode?.id === node.id() ? '#FF6B6B' : '#333'),
          },
        },
      ],
      layout: {
        name: 'cose',
        // Force-directed layout similar to D3
        idealEdgeLength: (edge: cytoscape.EdgeSingular) => 100 / (edge.data('weight') || 1),
        nodeRepulsion: 3000,
        nodeOverlap: 20,
        nestingFactor: 0.1,
        gravity: 0.25,
        numIter: 2500,
        animate: true,
        animationDuration: 1000,
        animationEasing: 'ease-out',
      },
      userPanningEnabled: true,
      userZoomingEnabled: true,
      boxSelectionEnabled: false,
    });

    // Store cytoscape reference
    cyRef.current = cy;

    // Handle node clicks
    cy.on('tap', 'node', (event: cytoscape.EventObject) => {
      const node = event.target;
      const nodeData = node.data() as { id: string };
      // Find the original node data
      const originalNode = nodes.find((n) => n.id === nodeData.id);
      if (originalNode) {
        onNodeClick(originalNode);
      }
    });

    // Cleanup on unmount
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [nodes, edges, showOrthologs, selectedNode, onNodeClick]);

  return (
    <div className={styles.graphContainer}>
      <div ref={containerRef} className={styles.cytoscapeContainer} />
    </div>
  );
};

export default NetworkView;

