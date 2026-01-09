import { useState, useEffect, useCallback, useRef } from 'react';
import { PPIService } from '../services/interactions/ppiService';
import { OrthologService } from '../services/interactions/orthologService';
import { PPINetworkData, PPINetworkQuery, PPINetworkProperties } from '../interfaces/PPI';
import { OrthologRelationship } from '../interfaces/Ortholog';

interface UseNetworkDataProps {
  speciesAcronym?: string;
  isolateName?: string;
  locusTag?: string; // Optional: Filter to PPIs involving this locus_tag (creates neighborhood view)
  scoreType?: string;
  scoreThreshold?: number;
  showOrthologs?: boolean;
  enabled?: boolean;
  useLightweight?: boolean; // Use lightweight endpoint for global cloud view (avoids timeouts)
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
  scoreThreshold = 0.8,
  showOrthologs = false,
  enabled = true,
  useLightweight = false,
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

    const baseFetchKey = `${speciesAcronym}-${isolateName}-${locusTag}-${scoreType}-${scoreThreshold}-${useLightweight ? 'lightweight' : 'full'}`;
    const fetchKey = `${baseFetchKey}-${showOrthologs}`;
    
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
        if (useLightweight) {
          // Use lightweight endpoint for global cloud view
          network = await PPIService.getLightweightNetworkData({
            score_type: scoreType,
            score_threshold: scoreThreshold,
            species_acronym: speciesAcronym,
            isolate_name: isolateName,
            max_interactions: 50000, // Reasonable limit to avoid timeouts
          });
        } else {
          // Use full endpoint for focused/neighborhood view
          const query: PPINetworkQuery = {
            score_type: scoreType,
            score_threshold: scoreThreshold,
            species_acronym: speciesAcronym,
            isolate_name: isolateName,
            locus_tag: locusTag,
            include_properties: true,
          };

          network = await PPIService.getNetworkData(query);
        }
        setNetworkData(network);
        networkDataRef.current = network;

        // Extract properties if available (only for full endpoint)
        if (network.properties) {
          setNetworkProperties(network.properties);
        } else if (!useLightweight) {
          // Fetch properties separately if not included (only for full endpoint)
          // For lightweight endpoint, we skip properties to save time
          const properties = await PPIService.getNetworkProperties({
            score_type: scoreType,
            score_threshold: scoreThreshold,
            species_acronym: speciesAcronym,
            isolate_name: isolateName,
          });
          setNetworkProperties(properties);
        } else {
          // For lightweight endpoint, set minimal properties based on actual data
          setNetworkProperties({
            num_nodes: network.nodes.length,
            num_edges: network.edges.length,
            density: 0, // Not calculated for lightweight
            avg_clustering_coefficient: 0, // Not calculated for lightweight
            degree_distribution: [],
          });
        }
      }

      // Fetch ortholog data if enabled (always fetch when showOrthologs is true and we don't have data)
      if (showOrthologs && network && network.nodes) {
        const locusTags = network.nodes
          .map((node) => node.locus_tag)
          .filter((tag): tag is string => !!tag);
        
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
  }, [enabled, speciesAcronym, isolateName, locusTag, scoreType, scoreThreshold, showOrthologs, useLightweight, fetchOrthologData]);

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

