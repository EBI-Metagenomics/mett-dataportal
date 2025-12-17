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
}: UseNetworkDataProps): UseNetworkDataReturn => {
  const [networkData, setNetworkData] = useState<PPINetworkData | null>(null);
  const [networkProperties, setNetworkProperties] = useState<PPINetworkProperties | null>(null);
  const [orthologMap, setOrthologMap] = useState<Map<string, OrthologRelationship[]>>(new Map());
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [availableScoreTypes, setAvailableScoreTypes] = useState<string[]>([]);

  const lastFetchRef = useRef<string>('');
  const isFetchingRef = useRef(false);

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
        const orthologs = await OrthologService.getBatchOrthologs(locusTags, speciesAcronym);
        return orthologs;
      } catch (err) {
        console.error('Error fetching ortholog data:', err);
        return new Map<string, OrthologRelationship[]>();
      }
    },
    [showOrthologs, speciesAcronym]
  );

  // Fetch network data
  const fetchNetworkData = useCallback(async () => {
    if (!enabled || !speciesAcronym) {
      return;
    }

    const baseFetchKey = `${speciesAcronym}-${isolateName}-${locusTag}-${scoreType}-${scoreThreshold}`;
    const fetchKey = `${baseFetchKey}-${showOrthologs}`;
    
    // Check if we need to fetch PPI data or just ortholog data
    const needsPPIData = lastFetchRef.current === '' || !lastFetchRef.current.startsWith(baseFetchKey);
    const needsOrthologData = showOrthologs && (orthologMap.size === 0 || lastFetchRef.current !== fetchKey);
    
    // Prevent duplicate fetches only if we already have the exact data we need
    if (!needsPPIData && !needsOrthologData && isFetchingRef.current) {
      return;
    }

    try {
      isFetchingRef.current = true;
      setLoading(true);
      setError(null);

      let network = networkData;
      
      // Fetch PPI network data if needed
      if (needsPPIData) {
        const query: PPINetworkQuery = {
          score_type: scoreType,
          score_threshold: scoreThreshold,
          species_acronym: speciesAcronym,
          isolate_name: isolateName,
          locus_tag: locusTag,
          include_properties: true,
        };

        network = await PPIService.getNetworkData(query);
        setNetworkData(network);

        // Extract properties if available
        if (network.properties) {
          setNetworkProperties(network.properties);
        } else {
          // Fetch properties separately if not included
          const properties = await PPIService.getNetworkProperties({
            score_type: scoreType,
            score_threshold: scoreThreshold,
            species_acronym: speciesAcronym,
            isolate_name: isolateName,
          });
          setNetworkProperties(properties);
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
        }
      } else if (!showOrthologs) {
        setOrthologMap(new Map());
      }

      lastFetchRef.current = fetchKey;
    } catch (err: any) {
      console.error('Error fetching network data:', err);
      setError(err.message || 'Failed to load network data');
    } finally {
      isFetchingRef.current = false;
      setLoading(false);
    }
  }, [enabled, speciesAcronym, isolateName, locusTag, scoreType, scoreThreshold, showOrthologs, fetchOrthologData, networkData, orthologMap]);

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

