import { useState, useEffect, useCallback, useRef } from 'react';
import { PPIService } from '../services/interactions/ppiService';
import { OrthologService } from '../services/interactions/orthologService';
import { PPINetworkData, PPINetworkQuery, PPINetworkProperties } from '../interfaces/PPI';
import { OrthologRelationship } from '../interfaces/Ortholog';

export type NetworkLimitMode = 'threshold' | 'topN';
export type SpeciesScope = 'current' | 'all';

// NOTE: Data source selection for the main NetworkView is handled at the
// component level (NetworkView.tsx) where multiple sources (local + STRING)
// can be merged. This hook currently fetches the canonical local ES network.

interface UseNetworkDataProps {
  speciesAcronym?: string;
  isolateName?: string;
  locusTag?: string; // Optional: Filter to PPIs involving this locus_tag (creates neighborhood view)
  scoreType?: string;
  scoreThreshold?: number;
  /** When limitMode is 'topN', show this many top interactors (neighborhood API). */
  topN?: number;
  limitMode?: NetworkLimitMode;
  /** 'current' = filter by species_acronym; 'all' = no species filter. */
  speciesScope?: SpeciesScope;
  showOrthologs?: boolean;
  /** Extra locus tags (e.g. from expanded nodes) to include when fetching orthologs. */
  extraLocusTagsForOrthologs?: string[];
  enabled?: boolean;
}

interface UseNetworkDataReturn {
  networkData: PPINetworkData | null;
  networkProperties: PPINetworkProperties | null;
  orthologMap: Map<string, OrthologRelationship[]>;
  loading: boolean;
  error: string | null;
  refreshNetwork: () => Promise<void>;
  availableScoreTypes: string[];
}

/**
 * Hook for fetching and managing PPI network data with optional ortholog enrichment
 */
export const useNetworkData = ({
  speciesAcronym,
  isolateName,
  locusTag,
  scoreType = 'ds_score',
  scoreThreshold = 0.9,
  topN = 10,
  limitMode = 'threshold',
  speciesScope = 'current',
  showOrthologs = false,
  extraLocusTagsForOrthologs,
  enabled = true,
}: UseNetworkDataProps): UseNetworkDataReturn => {
  const [networkData, setNetworkData] = useState<PPINetworkData | null>(null);
  const [networkProperties, setNetworkProperties] = useState<PPINetworkProperties | null>(null);
  const [orthologMap, setOrthologMap] = useState<Map<string, OrthologRelationship[]>>(new Map());
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [availableScoreTypes, setAvailableScoreTypes] = useState<string[]>([]);

  const lastFetchRef = useRef<string>('');
  const isFetchingRef = useRef(false);
  const networkDataRef = useRef<PPINetworkData | null>(null);
  const orthologMapRef = useRef<Map<string, OrthologRelationship[]>>(new Map());

  // Keep refs in sync with state
  useEffect(() => {
    networkDataRef.current = networkData;
  }, [networkData]);

  useEffect(() => {
    orthologMapRef.current = orthologMap;
  }, [orthologMap]);

  // Fetch available score types on mount
  useEffect(() => {
    const fetchScoreTypes = async () => {
      try {
        const response = await PPIService.getAvailableScoreTypes();
        setAvailableScoreTypes(response.score_types || []);
      } catch (err) {
        console.error('Error fetching available score types:', err);
      }
    };
    fetchScoreTypes();
  }, []);

  // Fetch ortholog data for network nodes
  const fetchOrthologData = useCallback(
    async (locusTags: string[]) => {
      if (!showOrthologs || locusTags.length === 0) {
        return new Map<string, OrthologRelationship[]>();
      }

      try {
        // Don't filter by speciesAcronym - orthologs are cross-species relationships
        // and we want to see orthologs from all species, not just the current one
        const orthologs = await OrthologService.getBatchOrthologs(locusTags, undefined);
        return orthologs;
      } catch (err) {
        console.error('Error fetching ortholog data:', err);
        return new Map<string, OrthologRelationship[]>();
      }
    },
    [showOrthologs]
  );

  // Fetch network data
  const fetchNetworkData = useCallback(async () => {
    if (!enabled || !speciesAcronym) {
      return;
    }

    const effectiveSpecies = speciesScope === 'all' ? undefined : speciesAcronym;
    const baseFetchKey = limitMode === 'topN'
      ? `${effectiveSpecies ?? 'all'}-${isolateName}-${locusTag}-topN-${topN}-${scoreType}-${scoreThreshold}`
      : `${effectiveSpecies ?? 'all'}-${isolateName}-${locusTag}-${scoreType}-${scoreThreshold}`;
    const extraKey = (extraLocusTagsForOrthologs ?? []).slice().sort().join(',');
    const fetchKey = `${baseFetchKey}-${showOrthologs}-${extraKey}`;

    // Check if we need to fetch PPI data or just ortholog data
    const needsPPIData = lastFetchRef.current === '' || !lastFetchRef.current.startsWith(baseFetchKey);
    const needsOrthologData = showOrthologs && (orthologMapRef.current.size === 0 || lastFetchRef.current !== fetchKey);
    
    // Prevent duplicate fetches only if we already have the exact data we need
    if (!needsPPIData && !needsOrthologData && isFetchingRef.current) {
      return;
    }

    try {
      isFetchingRef.current = true;
      setLoading(true);
      setError(null);

      let network = networkDataRef.current;

      // Fetch PPI network data if needed
      if (needsPPIData) {
        if (limitMode === 'topN' && locusTag) {
          // Top N mode: only n and score_type (for ranking). No min score filter so we get up to N nodes.
          const neighborhood = await PPIService.getProteinNeighborhood({
            locus_tag: locusTag,
            species_acronym: effectiveSpecies ?? undefined,
            n: topN,
            score_type: scoreType,
            score_threshold: 0,
          });
          network = neighborhood.network_data;
          // Ensure focal node shows locus tag: API may return protein_id as UniProt; set locus_tag so display is consistent
          if (network?.nodes && locusTag && neighborhood.protein_id) {
            network.nodes.forEach((n) => {
              if (n.id === neighborhood.protein_id && !n.locus_tag) {
                n.locus_tag = locusTag;
              }
            });
          }
          setNetworkData(network);
          networkDataRef.current = network;
          // Neighborhood API does not return properties; derive from nodes/edges so stats display
          const nNodes = network.nodes?.length ?? 0;
          const nEdges = network.edges?.length ?? 0;
          const density = nNodes > 1 ? (2 * nEdges) / (nNodes * (nNodes - 1)) : 0;
          setNetworkProperties({
            num_nodes: nNodes,
            num_edges: nEdges,
            density,
            avg_clustering_coefficient: 0,
            degree_distribution: [],
          });
        } else {
          const query: PPINetworkQuery = {
            score_type: scoreType,
            score_threshold: scoreThreshold,
            species_acronym: effectiveSpecies,
            isolate_name: isolateName,
            locus_tag: locusTag,
            include_properties: true,
          };

          network = await PPIService.getNetworkData(query);
          // Ensure focal node has locus_tag when we requested by locus_tag (API may use UniProt id)
          if (network?.nodes && locusTag) {
            network.nodes.forEach((n) => {
              if (n.id === locusTag && !n.locus_tag) {
                n.locus_tag = locusTag;
              }
            });
          }
          setNetworkData(network);
          networkDataRef.current = network;

          if (network.properties) {
            setNetworkProperties(network.properties);
          } else {
            const properties = await PPIService.getNetworkProperties({
              score_type: scoreType,
              score_threshold: scoreThreshold,
              species_acronym: effectiveSpecies ?? undefined,
              isolate_name: isolateName,
            });
            setNetworkProperties(properties);
          }
        }
      }

      // Fetch ortholog data if enabled (base nodes + expanded nodes so orthologs show for all)
      if (showOrthologs && network && network.nodes) {
        const baseTags = network.nodes
          .map((node) => node.locus_tag)
          .filter((tag): tag is string => !!tag);
        const extra = extraLocusTagsForOrthologs ?? [];
        const locusTags = Array.from(new Set([...baseTags, ...extra]));
        if (locusTags.length > 0) {
          const orthologs = await fetchOrthologData(locusTags);
          setOrthologMap(orthologs);
          orthologMapRef.current = orthologs;
        }
      } else if (!showOrthologs) {
        const emptyMap = new Map<string, OrthologRelationship[]>();
        setOrthologMap(emptyMap);
        orthologMapRef.current = emptyMap;
      }

      lastFetchRef.current = fetchKey;
    } catch (err: any) {
      console.error('Error fetching network data:', err);
      setError(err.message || 'Failed to load network data');
    } finally {
      isFetchingRef.current = false;
      setLoading(false);
    }
  }, [enabled, speciesAcronym, isolateName, locusTag, scoreType, scoreThreshold, topN, limitMode, speciesScope, showOrthologs, extraLocusTagsForOrthologs, fetchOrthologData]);

  // Refresh network data
  const refreshNetwork = useCallback(async () => {
    lastFetchRef.current = '';
    await fetchNetworkData();
  }, [fetchNetworkData]);

  // Fetch data when dependencies change
  useEffect(() => {
    fetchNetworkData();
  }, [fetchNetworkData]);

  return {
    networkData,
    networkProperties,
    orthologMap,
    loading,
    error,
    refreshNetwork,
    availableScoreTypes,
  };
};

