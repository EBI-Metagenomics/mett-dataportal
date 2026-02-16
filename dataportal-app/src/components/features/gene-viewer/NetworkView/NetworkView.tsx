import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import { useNetworkData, type NetworkLimitMode, type SpeciesScope } from '../../../../hooks/useNetworkData';
import { useAuth } from '../../../../hooks/useAuth';
import { PPINetworkNode, PPINetworkEdge, PPINetworkData, PPIDataSource } from '../../../../interfaces/PPI';
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
  const [dataSource, setDataSource] = useState<PPIDataSource>('local');
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

  // STRING DB network state (for STRING-only or combined views)
  const [stringNetwork, setStringNetwork] = useState<PPINetworkData | null>(null);
  const [stringFocalPreferredName, setStringFocalPreferredName] = useState<string | null>(null);
  const [stringLoading, setStringLoading] = useState<boolean>(false);
  const [stringError, setStringError] = useState<string | null>(null);

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

  // Fetch STRING DB network when requested by dataSource.
  useEffect(() => {
    const shouldUseString = dataSource === 'stringdb' || dataSource === 'both';

    if (!shouldUseString) {
      setStringNetwork(null);
      setStringFocalPreferredName(null);
      setStringError(null);
      return;
    }

    if (!speciesAcronym || !selectedLocusTag) {
      setStringNetwork(null);
      setStringFocalPreferredName(null);
      setStringError(null);
      return;
    }

    const fetchStringNetwork = async () => {
      try {
        setStringLoading(true);
        setStringError(null);

        const effectiveSpecies = speciesScope === 'all' ? undefined : speciesAcronym;

        // Paginated PPI search returns the data array directly from ApiService.get, not { data, pagination }.
        const searchWithString = await PPIService.searchInteractions({
          species_acronym: effectiveSpecies ?? undefined,
          locus_tag: selectedLocusTag,
          has_string: true,
          per_page: 5,
        });
        const listWithString = Array.isArray(searchWithString)
          ? searchWithString
          : (searchWithString as { data?: unknown[] })?.data ?? [];

        let interaction =
          listWithString.length > 0 ? (listWithString[0] as { pair_id?: string }) : null;

        // Fallback: if no interaction has STRING evidence, try any interaction for this gene
        // (backend will use string_protein_* from ES if present, or return a clear error).
        if (!interaction?.pair_id) {
          const searchAny = await PPIService.searchInteractions({
            species_acronym: effectiveSpecies ?? undefined,
            locus_tag: selectedLocusTag,
            per_page: 10,
          });
          const listAny = Array.isArray(searchAny)
            ? searchAny
            : (searchAny as { data?: unknown[] })?.data ?? [];
          interaction =
            listAny.length > 0 ? (listAny[0] as { pair_id?: string }) : null;
        }

        if (!interaction?.pair_id) {
          setStringNetwork(null);
          setStringError('No PPI interactions found for this gene.');
          return;
        }

        // STRING required_score is 0–1000. Use a permissive range (150–500) so we get results;
        // STRING TSV scores are often 0–1 scale, so 900 would filter out most edges.
        const requiredScore = Math.round(Math.max(150, Math.min(500, 100 + scoreThreshold * 400)));

        const stringRaw = await PPIService.getStringNetwork({
          pair_id: interaction.pair_id,
          locus_tag: selectedLocusTag,
          species_acronym: effectiveSpecies ?? undefined,
          required_score: requiredScore,
          network_type: 'physical',
        });

        if (stringRaw.error) {
          setStringNetwork(null);
          const msg = stringRaw.error || 'Failed to load STRING DB network.';
          setStringError(
            msg.includes('STRING protein IDs not available') || msg.includes('missing string_protein')
              ? 'This gene has no STRING DB identifiers in the database. Try Local (ES) or another gene.'
              : msg
          );
          return;
        }

        // Convert STRING DB response to PPINetworkData shape. Use locus tags when available so nodes align with local ES.
        const rows = Array.isArray(stringRaw.network) ? stringRaw.network : [];
        const nodeMap = new Map<string, PPINetworkNode>();
        const edges: PPINetworkEdge[] = [];
        const preferredToLocus = stringRaw.preferred_name_to_locus_tag ?? {};

        rows.forEach((row: Record<string, unknown>) => {
          const sourcePreferred =
            (row.preferredName_A as string | undefined) ||
            (row.preferredName1 as string | undefined) ||
            (row.protein1 as string | undefined);
          const targetPreferred =
            (row.preferredName_B as string | undefined) ||
            (row.preferredName2 as string | undefined) ||
            (row.protein2 as string | undefined);

          if (!sourcePreferred || !targetPreferred) {
            return;
          }

          const sourceId = preferredToLocus[sourcePreferred] ?? sourcePreferred;
          const targetId = preferredToLocus[targetPreferred] ?? targetPreferred;

          let rawScore: number | string | undefined =
            (row.score as number | string | undefined) ??
            (row.combined_score as number | string | undefined) ??
            (row.combinedScore as number | string | undefined);

          if (typeof rawScore === 'string') {
            const parsed = parseFloat(rawScore);
            rawScore = Number.isNaN(parsed) ? undefined : parsed;
          }

          const normalized =
            typeof rawScore === 'number'
              ? rawScore > 1
                ? rawScore / 1000
                : rawScore
              : undefined;

          if (!nodeMap.has(sourceId)) {
            nodeMap.set(sourceId, {
              id: sourceId,
              label: sourceId,
              locus_tag: preferredToLocus[sourcePreferred] ? sourceId : undefined,
            });
          }
          if (!nodeMap.has(targetId)) {
            nodeMap.set(targetId, {
              id: targetId,
              label: targetId,
              locus_tag: preferredToLocus[targetPreferred] ? targetId : undefined,
            });
          }

          edges.push({
            source: sourceId,
            target: targetId,
            weight: normalized,
            score_type: 'stringdb',
            dataSource: 'stringdb',
          });
        });

        const nodes = Array.from(nodeMap.values());
        const nNodes = nodes.length;
        const nEdges = edges.length;
        const density = nNodes > 1 ? (2 * nEdges) / (nNodes * (nNodes - 1)) : 0;

        const network: PPINetworkData = {
          nodes,
          edges,
          properties: {
            num_nodes: nNodes,
            num_edges: nEdges,
            density,
            avg_clustering_coefficient: 0,
            degree_distribution: [],
          },
        };

        setStringNetwork(network);
        setStringFocalPreferredName(stringRaw.focal_preferred_name ?? null);
      } catch (err: any) {
        console.error('Error fetching STRING DB network:', err);
        setStringNetwork(null);
        setStringError(err.message || 'Failed to load STRING DB network.');
      } finally {
        setStringLoading(false);
      }
    };

    fetchStringNetwork();
  }, [dataSource, speciesAcronym, selectedLocusTag, speciesScope, scoreThreshold]);

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

  // When switching to STRING or Both, clear expansion so we don't show two graphs (stale expansion or local+STRING split).
  useEffect(() => {
    if (dataSource === 'stringdb' || dataSource === 'both') {
      setExpansionState(createInitialExpansionState());
    }
  }, [dataSource]);

  // Store original nodes/edges and init expansion path when base network changes only.
  // Only run when we're using local data (local or both) so STRING-only view is not overwritten by local expansion.
  useEffect(() => {
    if (dataSource === 'stringdb') return;
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkData, dataSource]);

  // When path is still empty but we have networkData + selectedLocusTag (e.g. selectedLocusTag set after load), set initial path with starting node
  useEffect(() => {
    if (dataSource === 'stringdb' || !networkData || !selectedLocusTag || expansionState.path.nodes.length > 0) return;
    const enriched = enrichNetworkData(networkData, orthologMap, showOrthologs);
    const startingNode = enriched.enrichedNodes.find(
      node => node.locus_tag === selectedLocusTag || node.id === selectedLocusTag
    );
    if (!startingNode) return;
    const initialState = createInitialExpansionState();
    initialState.allExpandedNodes = new Map(
      enriched.enrichedNodes.map(node => [node.id, { ...node, expansionLevel: 0 }])
    );
    initialState.allExpandedEdges = enriched.enrichedEdges.map(edge => ({ ...edge, expansionLevel: 0 }));
    initialState.path.nodes = [{
      locusTag: startingNode.locus_tag || startingNode.id,
      nodeId: startingNode.id,
      node: startingNode,
      expandedAt: Date.now(),
      level: 0,
    }];
    initialState.path.currentLevel = 0;
    setExpansionState(initialState);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkData, selectedLocusTag, expansionState.path.nodes.length]);

  // Combine local ES and STRING DB networks based on selected data source
  const baseNetwork: PPINetworkData | null = useMemo(() => {
    if (dataSource === 'local' || !stringNetwork) {
      return networkData ?? null;
    }
    if (dataSource === 'stringdb' || !networkData) {
      return stringNetwork ?? null;
    }

    // dataSource === 'both': single graph with multiple edges. Normalize STRING focal node to local id so they merge.
    const nodeMap = new Map<string, PPINetworkNode>();
    const edgesList: (PPINetworkEdge & { dataSource?: string })[] = [];

    // Local API uses UniProt as node.id; we need one canonical id for the selected gene so STRING and local merge.
    const localFocalNode = networkData?.nodes.find(
      (n) => n.locus_tag === selectedLocusTag || n.id === selectedLocusTag
    );
    const localFocalId = localFocalNode?.id ?? selectedLocusTag ?? null;
    const focalStr = stringFocalPreferredName?.trim() || null;

    if (networkData) {
      networkData.nodes.forEach((n) => nodeMap.set(n.id, { ...n }));
      networkData.edges.forEach((e) =>
        edgesList.push({ ...e, dataSource: 'local' })
      );
    }

    if (stringNetwork) {
      // Map STRING focal node to local id: both gene name (focalStr) and locus tag (selectedLocusTag) must become localFocalId.
      const norm = (id: string) => {
        if (!localFocalId) return id;
        if (id === focalStr || id === selectedLocusTag) return localFocalId;
        return id;
      };
      stringNetwork.nodes.forEach((n) => {
        const id = norm(n.id);
        if (!nodeMap.has(id)) {
          nodeMap.set(id, { ...n, id, label: n.label ?? n.id });
        }
      });
      stringNetwork.edges.forEach((e) => {
        const source = norm(e.source);
        const target = norm(e.target);
        edgesList.push({
          ...e,
          source,
          target,
          dataSource: 'stringdb',
        });
      });
    }

    return {
      nodes: Array.from(nodeMap.values()),
      edges: edgesList,
      properties: networkData?.properties ?? stringNetwork?.properties,
    };
  }, [dataSource, networkData, stringNetwork, stringFocalPreferredName, selectedLocusTag]);

  const hasData = baseNetwork && baseNetwork.nodes.length > 0;

  // Enrich nodes with ortholog information and merge with expansions.
  // When dataSource is STRING only, show only baseNetwork (no expansion merge) so we don't show two graphs.
  const { enrichedNodes, enrichedEdges } = useMemo(() => {
    if (!baseNetwork?.nodes) {
      return { enrichedNodes: [], enrichedEdges: [] as PPINetworkEdge[] };
    }

    const baseNodes = baseNetwork.nodes;
    const baseEdges = baseNetwork.edges || [];

    if (dataSource === 'stringdb' || expansionState.allExpandedNodes.size === 0) {
      return enrichNetworkData(baseNetwork, orthologMap, showOrthologs);
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

    // Keep all base edges (for "both" there can be multiple edges per pair: local + STRING).
    const mergedPpiEdges: (PPINetworkEdge & { expansionLevel?: number })[] = baseEdges.map(e => ({ ...e, expansionLevel: 0 }));
    expansionState.allExpandedEdges.forEach(e => {
      mergedPpiEdges.push({
        ...e,
        expansionLevel: (e as PPINetworkEdge & { expansionLevel?: number }).expansionLevel ?? 0,
      });
    });

    const mergedNetwork = {
      nodes: Array.from(mergedPpiNodes.values()),
      edges: mergedPpiEdges,
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

    // Use a unique key per edge so we keep multiple edges per pair (e.g. local + STRING when dataSource is 'both').
    const edgeMap = new Map<string, PPINetworkEdge & { expansionLevel?: number }>();
    fullEnriched.enrichedEdges.forEach((e, i) => {
      const dataSource = (e as { dataSource?: string }).dataSource ?? 'local';
      const key = (e as { id?: string }).id ?? `${dataSource}-${e.source}-${e.target}-${i}`;
      const fromState = expansionState.allExpandedEdges.find(
        edge => (edge.source === e.source && edge.target === e.target) || (edge.source === e.target && edge.target === e.source)
      ) as (PPINetworkEdge & { expansionLevel?: number }) | undefined;
      const level = fromState?.expansionLevel ?? (e as PPINetworkEdge & { expansionLevel?: number }).expansionLevel ?? 0;
      edgeMap.set(key, { ...e, expansionLevel: level });
    });
    expansionState.allExpandedEdges.forEach((e, i) => {
      const key = `expansion-${e.source}-${e.target}-${i}`;
      if (!edgeMap.has(key)) {
        edgeMap.set(key, { ...e, expansionLevel: (e as PPINetworkEdge & { expansionLevel?: number }).expansionLevel ?? 0 });
      }
    });

    return {
      enrichedNodes: Array.from(nodeMap.values()),
      enrichedEdges: Array.from(edgeMap.values()),
    };
  }, [baseNetwork, orthologMap, showOrthologs, expansionState, dataSource]);

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

  return (
    <div className={styles.networkView}>
      {/* Controls - Always visible */}
        <NetworkControls
          dataSource={dataSource}
          scoreType={scoreType}
          displayThreshold={displayThreshold}
          limitMode={limitMode}
          topN={topN}
          speciesScope={speciesScope}
          showOrthologs={showOrthologs}
          availableScoreTypes={availableScoreTypes}
          onDataSourceChange={setDataSource}
          onScoreTypeChange={handleScoreTypeChange}
          onThresholdChange={handleThresholdChange}
          onLimitModeChange={handleLimitModeChange}
          onTopNChange={handleTopNChange}
          onSpeciesScopeChange={handleSpeciesScopeChange}
          onOrthologToggle={handleOrthologToggle}
          onResetView={handleResetView}
        />

      {/* Error Message */}
      {(error || stringError) && (
        <div className={styles.networkViewError}>
          <p>Error loading network data: {error || stringError}</p>
        </div>
      )}

      {/* Loading State */}
      {(loading || stringLoading) && !hasData && !(error || stringError) && (
        <div className={styles.networkViewLoading}>
          <p>Loading network data...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !stringLoading && !(error || stringError) && !hasData && <EmptyState />}

      {/* Network Stats (use enriched counts so expansion increases node/edge count) */}
      {hasData && (
        <NetworkStats
          properties={networkProperties ?? baseNetwork?.properties ?? null}
          nodeCount={enrichedNodes.length}
          edgeCount={enrichedEdges.length}
          showOrthologs={showOrthologs}
          dataSource={dataSource}
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
      {hasData && !(error || stringError) && (
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
