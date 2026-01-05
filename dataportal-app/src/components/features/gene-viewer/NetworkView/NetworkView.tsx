import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useNetworkData } from '../../../../hooks/useNetworkData';
import { useAuth } from '../../../../hooks/useAuth';
import { PPINetworkNode } from '../../../../interfaces/PPI';
import { NetworkGraph, NetworkGraphRef } from './NetworkGraph';
import { NetworkControls } from './NetworkControls';
import { NetworkStats } from './NetworkStats';
import { NetworkLegend } from './NetworkLegend';
import { EmptyState } from './EmptyState';
import { AuthRequired } from './AuthRequired';
import { NodeInfoPopup } from './NodeInfoPopup';
import { enrichNetworkData } from './utils/enrichNodes';
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
  const thresholdDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const graphRef = useRef<NetworkGraphRef>(null);

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
  useEffect(() => {
    if (setLoading) {
      setLoading(loading);
    }
  }, [loading, setLoading]);

  // Sync displayThreshold with scoreThreshold when it changes externally
  useEffect(() => {
    setDisplayThreshold(scoreThreshold);
  }, [scoreThreshold]);

  // Enrich nodes with ortholog information
  const { enrichedNodes, enrichedEdges } = useMemo(() => {
    return enrichNetworkData(networkData, orthologMap, showOrthologs);
  }, [networkData, orthologMap, showOrthologs]);

  // Handle node click - only show popup, don't change view
  const handleNodeClick = useCallback(
    (node: PPINetworkNode, event?: MouseEvent) => {
      setSelectedNode(node);
      
      // Show popup at click position
      if (event) {
        setPopupNode({ node, x: event.clientX, y: event.clientY });
      }
      
      // Note: We intentionally don't call onFeatureSelect here to avoid
      // changing the view and keeping JBrowse and network view in sync
    },
    []
  );

  // Handle reset view
  const handleResetView = useCallback(() => {
    if (graphRef.current) {
      graphRef.current.resetView();
    }
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
        onRefresh={refreshNetwork}
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
        <NetworkStats properties={networkProperties} />
      )}

      {/* Network Visualization */}
      {hasData && !error && (
        <>
          <div className={styles.networkVisualization}>
            <NetworkGraph
              ref={graphRef}
              nodes={enrichedNodes}
              edges={enrichedEdges}
              showOrthologs={showOrthologs}
              onNodeClick={handleNodeClick}
              selectedNode={selectedNode}
            />
          </div>
          <NetworkLegend showOrthologs={showOrthologs} />
        </>
      )}

      {/* Node Info Popup */}
      {popupNode && (
        <NodeInfoPopup
          node={popupNode.node}
          x={popupNode.x}
          y={popupNode.y}
          onClose={() => setPopupNode(null)}
        />
      )}
    </div>
  );
};

export default NetworkView;
