import { useState, useEffect, useCallback } from 'react';
import { useFilterStore, FacetedFilters, FacetOperators } from '../stores/filterStore';
import { GeneService } from '../services/geneService';
import { GeneFacetResponse } from '../interfaces/Gene';

interface UseFacetedFiltersProps {
  selectedSpecies: string[];
  selectedGenomes: Array<{ isolate_name: string }>;
  searchQuery: string;
}

interface UseFacetedFiltersReturn {
  facets: GeneFacetResponse;
  loading: boolean;
  error: string | null;
  handleToggleFacet: (facetGroup: string, value: string | boolean) => void;
  handleOperatorChange: (facetGroup: string, operator: 'AND' | 'OR') => void;
  refreshFacets: () => Promise<void>;
}

export const useFacetedFilters = ({
  selectedSpecies,
  selectedGenomes,
  searchQuery,
}: UseFacetedFiltersProps): UseFacetedFiltersReturn => {
  const filterStore = useFilterStore();
  const [facets, setFacets] = useState<GeneFacetResponse>({ total_hits: 0, operators: {} });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Convert faceted filters to API format
  const getApiFilters = useCallback(() => {
    const filters = filterStore.facetedFilters;
    return {
      essentiality: filters.essentiality?.join(','),
      has_amr_info: filters.has_amr_info?.map(v => String(v)).join(','),
      pfam: filters.pfam?.join(','),
      interpro: filters.interpro?.join(','),
      kegg: filters.kegg?.join(','),
      cog_funcats: filters.cog_funcats?.join(','),
      cog_id: filters.cog_id?.join(','),
      go_term: filters.go_term?.join(','),
    };
  }, [filterStore.facetedFilters]);

  // Load facets with current filters applied
  const loadFacets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const speciesAcronym = selectedSpecies?.[0];
      const isolates = selectedGenomes.map(genome => genome.isolate_name).join(',');
      const apiFilters = getApiFilters();

      const response = await GeneService.fetchGeneFacets(
        searchQuery,
        speciesAcronym,
        isolates,
        apiFilters.essentiality,
        apiFilters.cog_id,
        apiFilters.cog_funcats,
        apiFilters.kegg,
        apiFilters.go_term,
        apiFilters.pfam,
        apiFilters.interpro,
        apiFilters.has_amr_info,
        filterStore.facetOperators as Record<string, 'AND' | 'OR'>
      );

      // Process facets to mark selected items
      const updatedFacets: GeneFacetResponse = {
        total_hits: response.total_hits || 0,
        operators: response.operators || {},
      };

      for (const [facetGroup, items] of Object.entries(response)) {
        if (
          facetGroup === 'total_hits' ||
          facetGroup === 'operators' ||
          !Array.isArray(items)
        ) continue;

        const selectedValues = filterStore.facetedFilters[facetGroup as keyof FacetedFilters] || [];

        const responseMap = new Map(items.map(item => [item.value, {
          ...item,
          selected: selectedValues.some(v => String(v) === String(item.value)),
        }]));

        // Add selected values that might not be in the response
        selectedValues.forEach(sel => {
          const selStr = String(sel);
          if (!responseMap.has(selStr)) {
            responseMap.set(selStr, {
              value: selStr,
              count: 0,
              selected: true,
            });
          }
        });

        updatedFacets[facetGroup] = Array.from(responseMap.values());
      }

      setFacets(updatedFacets);
    } catch (err) {
      console.error('Error loading facets:', err);
      setError('Failed to load filter options');
    } finally {
      setLoading(false);
    }
  }, [selectedSpecies, selectedGenomes, filterStore.facetedFilters, filterStore.facetOperators, getApiFilters, searchQuery]);

  // Handle facet toggle
  const handleToggleFacet = useCallback((facetGroup: string, value: string | boolean) => {
    const currentFilters = filterStore.facetedFilters;
    const currentValues = currentFilters[facetGroup as keyof FacetedFilters] || [];
    
    // Handle different filter types
    if (facetGroup === 'has_amr_info') {
      const boolValues = currentValues as boolean[];
      const boolValue = value as boolean;
      const newValues = boolValues.includes(boolValue) 
        ? boolValues.filter(v => v !== boolValue)
        : [...boolValues, boolValue];
      filterStore.updateFacetedFilter('has_amr_info', newValues);
    } else {
      const stringValues = currentValues as string[];
      const stringValue = String(value);
      const newValues = stringValues.includes(stringValue)
        ? stringValues.filter(v => v !== stringValue)
        : [...stringValues, stringValue];
      
      filterStore.updateFacetedFilter(facetGroup as keyof FacetedFilters, newValues);
    }
  }, [filterStore]);

  // Handle operator change
  const handleOperatorChange = useCallback((facetGroup: string, operator: 'AND' | 'OR') => {
    filterStore.updateFacetOperator(facetGroup as keyof FacetOperators, operator);
  }, [filterStore]);

  // Refresh facets manually
  const refreshFacets = useCallback(async () => {
    await loadFacets();
  }, [loadFacets]);

  // Load facets when dependencies change
  useEffect(() => {
    // Add a small delay to ensure URL sync happens first
    const timer = setTimeout(() => {
      loadFacets();
    }, 100);
    
    return () => clearTimeout(timer);
  }, [loadFacets]);

  return {
    facets,
    loading,
    error,
    handleToggleFacet,
    handleOperatorChange,
    refreshFacets,
  };
}; 