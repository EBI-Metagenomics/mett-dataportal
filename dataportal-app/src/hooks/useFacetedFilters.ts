import React, {useState, useEffect, useCallback, useRef} from 'react';
import {useLocation} from 'react-router-dom';
import {useFilterStore, FacetedFilters, FacetOperators} from '../stores/filterStore';
import {GeneService} from '../services/gene';
import {GeneFacetResponse} from '../interfaces/Gene';
import {normalizeFilterValue, compareFilterValues} from '../utils/common/filterUtils';

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
    const [facets, setFacets] = useState<GeneFacetResponse>({total_hits: 0, operators: {}});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Track if we've loaded initial facets to prevent duplicate calls
    const hasLoadedInitialFacets = useRef(false);
    const lastGenomeRef = useRef<string | null>(null);
    const lastSpeciesRef = useRef<string[]>([]);
    const lastSearchQueryRef = useRef<string>('');
    const lastFiltersRef = useRef<string>('');
    const lastOperatorsRef = useRef<string>('');
    const isInitialMount = useRef(true);
    const isLoadingFacets = useRef(false);
    const debounceTimeoutRef = useRef<number | null>(null);
    const lastApiCallRef = useRef<string>('');

    // Track current facets to prevent infinite loops
    const currentFacetsRef = useRef<GeneFacetResponse>({total_hits: 0, operators: {}});

    // Memoize the API filters to prevent unnecessary recalculations
    const getApiFilters = useCallback(() => {
        const filters = filterStore.facetedFilters;
        // For KEGG: add 'ko:' prefix back for API queries (Elasticsearch stores with prefix)
        const keggValues = filters.kegg?.map(v => {
            const value = String(v);
            // If value doesn't already start with 'ko:', add it
            if (!value.toLowerCase().startsWith('ko:')) {
                return `ko:${value}`;
            }
            return value;
        });
        
        return {
            essentiality: filters.essentiality?.join(','),
            has_amr_info: filters.has_amr_info?.map(v => String(v)).join(','),
            pfam: filters.pfam?.join(','),
            interpro: filters.interpro?.join(','),
            kegg: keggValues?.join(','),
            cog_funcats: filters.cog_funcats?.join(','),
            cog_id: filters.cog_id?.join(','),
            go_term: filters.go_term?.join(','),
        };
    }, [filterStore.facetedFilters]);

    // Update facets when filter store changes to keep checkbox state in sync
    useEffect(() => {
        if (facets && Object.keys(facets).length > 0) {
            const updatedFacets = { ...facets };
            let hasChanges = false;
            
            for (const [facetGroup, items] of Object.entries(updatedFacets)) {
                if (
                    facetGroup === 'total_hits' ||
                    facetGroup === 'operators' ||
                    !Array.isArray(items)
                ) continue;

                const selectedValues = filterStore.facetedFilters[facetGroup as keyof FacetedFilters] || [];
                
                // Normalize values for comparison using utility function
                const normalizedSelectedValues = selectedValues.map(v => normalizeFilterValue(v));
                
                // Update the selected state for each item
                items.forEach(item => {
                    const wasSelected = item.selected;
                    const normalizedItemValue = normalizeFilterValue(item.value);
                    const isSelected = normalizedSelectedValues.some(v => compareFilterValues(v, normalizedItemValue));
                    
                    if (wasSelected !== isSelected) {
                        item.selected = isSelected;
                        hasChanges = true;
                    }
                });
            }
            
            // Only update if there are actual changes
            if (hasChanges) {
                setFacets(updatedFacets);
            }
        }
    }, [filterStore.facetedFilters, filterStore.facetOperators]);

    const loadFacets = useCallback(async (forceRefresh = false) => {
        // Prevent duplicate calls
        if (isLoadingFacets.current && !forceRefresh) {
            console.log('loadFacets already in progress, skipping...');
            return;
        }

        try {
            // console.log('loadFacets called with:', {
            //     selectedSpecies,
            //     selectedGenomes,
            //     searchQuery,
            //     filterStore: filterStore.facetedFilters,
            //     operators: filterStore.facetOperators,
            //     forceRefresh
            // });

            isLoadingFacets.current = true;
            setLoading(true);
            setError(null);

            const speciesAcronym = selectedSpecies?.length === 1 ? selectedSpecies[0] : undefined;
            const isolates = selectedGenomes.map(genome => genome.isolate_name).join(',');
            const apiFilters = getApiFilters();

            // Create a unique key for this API call to prevent duplicates
            const apiCallKey = JSON.stringify({
                searchQuery,
                selectedSpecies,
                isolates,
                apiFilters,
                operators: filterStore.facetOperators
            });

            // Prevent duplicate API calls with the same parameters
            if (apiCallKey === lastApiCallRef.current && !forceRefresh) {
                console.log('Duplicate API call detected, skipping...');
                return;
            }

            console.log('Making API call with params:', {
                searchQuery,
                speciesAcronym,
                isolates,
                apiFilters,
                operators: filterStore.facetOperators
            });

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

            // console.log('API response received:', response);
            lastApiCallRef.current = apiCallKey;

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

                // Normalize values for comparison using utility function
                // For KEGG: also normalize 'ko:' prefix (remove if present) for consistent matching
                let normalizedSelectedValues = selectedValues.map(v => normalizeFilterValue(v));
                if (facetGroup === 'kegg') {
                    normalizedSelectedValues = normalizedSelectedValues.map(v => {
                        if (typeof v === 'string' && v.toLowerCase().startsWith('ko:')) {
                            return v.substring(3); // Remove 'ko:' prefix (case-insensitive)
                        }
                        return v;
                    });
                }

                // Build a Map, handling duplicates by normalizing values (case-insensitive key)
                // Use lowercase key for case-insensitive matching, but preserve original case in value
                // For KEGG: also normalize 'ko:' prefix (remove if present) for consistent matching
                // If multiple items normalize to the same value (case-insensitive), merge intelligently:
                // - Keep the one with highest count
                // - Preserve selected status (if either is selected, the merged item should be selected)
                const responseMap = new Map<string | boolean, any>();
                
                // Helper to normalize KEGG values by removing 'ko:' prefix
                const normalizeKeggValue = (value: string): string => {
                    if (facetGroup === 'kegg' && typeof value === 'string' && value.toLowerCase().startsWith('ko:')) {
                        return value.substring(3); // Remove 'ko:' prefix (case-insensitive)
                    }
                    return value;
                };
                
                items.forEach(item => {
                    let normalizedItemValue = normalizeFilterValue(item.value);
                    // For KEGG, remove 'ko:' prefix if present (matching FeaturePanel normalization)
                    if (facetGroup === 'kegg' && typeof normalizedItemValue === 'string') {
                        normalizedItemValue = normalizeKeggValue(normalizedItemValue);
                    }
                    
                    // Use lowercase key for case-insensitive Map lookup
                    const mapKey = typeof normalizedItemValue === 'string' 
                        ? normalizedItemValue.toLowerCase() 
                        : normalizedItemValue;
                    const isSelected = normalizedSelectedValues.some(v => compareFilterValues(v, normalizedItemValue));
                    
                    const existingItem = responseMap.get(mapKey);
                    if (!existingItem) {
                        // First time seeing this normalized value (case-insensitive)
                        responseMap.set(mapKey, {
                            ...item,
                            value: normalizedItemValue, // Store normalized value (preserves case, without ko: for KEGG)
                            selected: isSelected,
                        });
                    } else {
                        // Duplicate normalized value (case-insensitive) - merge intelligently
                        // Keep the one with highest count, but preserve selected status from either
                        const mergedSelected = existingItem.selected || isSelected;
                        const mergedCount = Math.max(existingItem.count, item.count);
                        
                        // Use the item with the higher count (or the one that's selected if counts are equal)
                        const preferredItem = 
                            item.count > existingItem.count ? item :
                            (item.count === existingItem.count && isSelected && !existingItem.selected) ? item :
                            existingItem;
                        
                        responseMap.set(mapKey, {
                            ...preferredItem,
                            value: normalizedItemValue, // Store normalized value (preserves case, without ko: for KEGG)
                            count: mergedCount, // Use the max count
                            selected: mergedSelected, // Preserve selection if either is selected
                        });
                    }
                });

                // Add selected values that might not be in the response (but only if they're truly missing)
                // Use case-insensitive key to check if value exists (prevents duplicates with different case)
                // For KEGG: also normalize 'ko:' prefix (remove if present) for consistent matching
                selectedValues.forEach(sel => {
                    let normalizedSel = normalizeFilterValue(sel);
                    // For KEGG, remove 'ko:' prefix if present (matching FeaturePanel normalization)
                    if (facetGroup === 'kegg' && typeof normalizedSel === 'string') {
                        normalizedSel = normalizeKeggValue(normalizedSel);
                    }
                    
                    // Use lowercase key for case-insensitive Map lookup
                    const mapKey = typeof normalizedSel === 'string' 
                        ? normalizedSel.toLowerCase() 
                        : normalizedSel;
                    if (!responseMap.has(mapKey)) {
                        responseMap.set(mapKey, {
                            value: normalizedSel, // Preserve original case from store (without ko: for KEGG)
                            count: 0,
                            selected: true,
                        });
                    } else {
                        // Value exists in response, just ensure it's marked as selected
                        const existingItem = responseMap.get(mapKey);
                        if (existingItem && !existingItem.selected) {
                            existingItem.selected = true;
                        }
                    }
                });

                updatedFacets[facetGroup] = Array.from(responseMap.values());
            }

            // console.log('Setting facets:', updatedFacets);
            setFacets(updatedFacets);
        } catch (err) {
            console.error('Error loading facets:', err);
            setError('Failed to load filter options');
        } finally {
            setLoading(false);
            isLoadingFacets.current = false;
        }
    }, [selectedSpecies, selectedGenomes, searchQuery, filterStore.facetOperators, getApiFilters]);

    // Debounced version of loadFacets for filter changes
    const debouncedLoadFacets = useCallback((delay = 500) => {
        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }
        
        debounceTimeoutRef.current = window.setTimeout(() => {
            loadFacets();
        }, delay);
    }, [loadFacets]);

    // Handle facet toggle - this should NOT trigger immediate API calls
    // Single source of truth: filterStore.facetedFilters
    // All comparisons use compareFilterValues for consistency
    const handleToggleFacet = useCallback((facetGroup: string, value: string | boolean) => {
        const currentFilters = filterStore.facetedFilters;
        const currentValues = currentFilters[facetGroup as keyof FacetedFilters] || [];

        // Normalize the incoming value FIRST to ensure consistency
        const normalizedValue = normalizeFilterValue(value);

        // Debug logging for pfam, interpro, kegg
        if (facetGroup === 'pfam' || facetGroup === 'interpro' || facetGroup === 'kegg') {
            console.log(`[useFacetedFilters] handleToggleFacet - ${facetGroup}:`, {
                'facetGroup': facetGroup,
                'value (passed in)': value,
                'value type': typeof value,
                'value length': typeof value === 'string' ? value.length : 'N/A',
                'value JSON': JSON.stringify(value),
                'normalizedValue': normalizedValue,
                'normalizedValue type': typeof normalizedValue,
                'normalizedValue length': typeof normalizedValue === 'string' ? normalizedValue.length : 'N/A',
                'normalizedValue JSON': JSON.stringify(normalizedValue),
                'currentValues (from store)': currentValues,
                'currentValues details': currentValues.map(v => ({
                    value: v,
                    type: typeof v,
                    length: typeof v === 'string' ? v.length : 'N/A',
                    json: JSON.stringify(v),
                    normalized: normalizeFilterValue(v),
                })),
            });
        }

        // Handle different filter types
        if (facetGroup === 'has_amr_info') {
            const boolValues = currentValues as boolean[];
            const boolValue = normalizedValue as boolean;
            // Use compareFilterValues for consistent comparison
            const isSelected = boolValues.some(v => compareFilterValues(v, boolValue));
            const newValues = isSelected
                ? boolValues.filter(v => !compareFilterValues(v, boolValue))
                : [...boolValues, boolValue];
            
            // updateFacetedFilter will normalize and deduplicate
            filterStore.updateFacetedFilter('has_amr_info', newValues);
        } else {
            const stringValues = currentValues as string[];
            // Values in store are already normalized, so compare directly with normalized value
            // Use compareFilterValues for consistent comparison (handles normalization internally)
            const isSelected = stringValues.some(v => compareFilterValues(v, normalizedValue));
            const newValues = isSelected
                ? stringValues.filter(v => !compareFilterValues(v, normalizedValue))
                : [...stringValues, normalizedValue]; // Add normalized value directly
            
            // Debug logging for pfam, interpro, kegg
            if (facetGroup === 'pfam' || facetGroup === 'interpro' || facetGroup === 'kegg' || facetGroup === 'has_amr_info') {
                console.log(`[useFacetedFilters] handleToggleFacet - ${facetGroup} (string):`, {
                    'isSelected': isSelected,
                    'action': isSelected ? 'REMOVING' : 'ADDING',
                    'newValues (before updateFacetedFilter)': newValues,
                    'newValues details': newValues.map(v => ({
                        value: v,
                        type: typeof v,
                        length: typeof v === 'string' ? v.length : 'N/A',
                        json: JSON.stringify(v),
                        normalized: normalizeFilterValue(v),
                    })),
                });
            }
            
            // updateFacetedFilter will normalize and deduplicate (but values should already be normalized)
            filterStore.updateFacetedFilter(facetGroup as keyof FacetedFilters, newValues);
            
            // Debug logging after update
            if (facetGroup === 'pfam' || facetGroup === 'interpro' || facetGroup === 'kegg' || facetGroup === 'has_amr_info') {
                setTimeout(() => {
                    const updatedFilters = filterStore.facetedFilters;
                    const updatedValues = updatedFilters[facetGroup as keyof FacetedFilters] || [];
                    console.log(`[useFacetedFilters] handleToggleFacet - ${facetGroup} (after updateFacetedFilter):`, {
                        'updatedValues (from store)': updatedValues,
                        'updatedValues details': updatedValues.map(v => ({
                            value: v,
                            type: typeof v,
                            length: typeof v === 'string' ? v.length : 'N/A',
                            json: JSON.stringify(v),
                            normalized: normalizeFilterValue(v),
                        })),
                    });
                }, 0);
            }
        }

        // The main useEffect will handle the API call for filter changes
    }, [filterStore]);

    const handleOperatorChange = useCallback((facetGroup: string, operator: 'AND' | 'OR') => {
        filterStore.updateFacetOperator(facetGroup as keyof FacetOperators, operator);
        // The main useEffect will handle the API call for operator changes
    }, [filterStore]);

    const refreshFacets = useCallback(async () => {
        await loadFacets(true); // Force refresh
    }, [loadFacets]);

    const location = useLocation();
    const isGeneViewerPage = React.useMemo(() => {
        // Check if we're on a gene viewer page by URL path
        const isGeneViewerPath = location.pathname.startsWith('/genome/');
        // Also check the traditional logic as fallback
        const hasSelectedGenomes = selectedGenomes.length > 0 && selectedSpecies.length === 0;
        return isGeneViewerPath || hasSelectedGenomes;
    }, [location.pathname, selectedSpecies.length, selectedGenomes.length]);

    const filtersAreInitial = Object.keys(filterStore.facetedFilters).length === 0 && Object.keys(filterStore.facetOperators).length === 0;

    useEffect(() => {
        const currentGenomeKey = selectedGenomes.map(g => g.isolate_name).join(',');
        const currentFiltersKey = JSON.stringify(filterStore.facetedFilters);
        const currentOperatorsKey = JSON.stringify(filterStore.facetOperators);

        const genomeChanged = currentGenomeKey !== lastGenomeRef.current;
        const speciesChanged = JSON.stringify(selectedSpecies) !== JSON.stringify(lastSpeciesRef.current);
        const searchQueryChanged = searchQuery !== lastSearchQueryRef.current;
        const filtersChanged = currentFiltersKey !== lastFiltersRef.current;
        const operatorsChanged = currentOperatorsKey !== lastOperatorsRef.current;

        if (genomeChanged && isLoadingFacets.current) {
            console.log('Skipping facet load - already loading facets for genome change');
            return;
        }

        // console.log('useFacetedFilters useEffect:', {
        //     currentGenomeKey,
        //     selectedSpecies,
        //     searchQuery,
        //     searchQueryLength: searchQuery.length,
        //     isGeneViewerPage,
        //     filtersAreInitial,
        //     genomeChanged,
        //     speciesChanged,
        //     searchQueryChanged,
        //     filtersChanged,
        //     operatorsChanged,
        //     hasLoadedInitialFacets: hasLoadedInitialFacets.current,
        //     isInitialMount: isInitialMount.current,
        //     selectedGenomes: selectedGenomes,
        //     selectedGenomesLength: selectedGenomes.length
        // });

        lastGenomeRef.current = currentGenomeKey;
        lastSpeciesRef.current = selectedSpecies;
        lastSearchQueryRef.current = searchQuery;
        lastFiltersRef.current = currentFiltersKey;
        lastOperatorsRef.current = currentOperatorsKey;

        let shouldLoadFacets = false;

        if (isInitialMount.current) {
            if (isGeneViewerPage && selectedGenomes.length > 0) {
                shouldLoadFacets = true;
                hasLoadedInitialFacets.current = true;
                console.log('Case 0: Initial mount with genome data');
            }
            else if (!isGeneViewerPage && (selectedSpecies.length > 0 || (selectedSpecies.length === 0 && selectedGenomes.length === 0))) {
                shouldLoadFacets = true;
                hasLoadedInitialFacets.current = true;
                console.log('Case 0: Initial mount with species data or default view');
            }
            else if (isGeneViewerPage && selectedGenomes.length === 0) {
                console.log('Case 0: Initial mount on GeneViewerPage but no genome data yet, skipping...');
                hasLoadedInitialFacets.current = false; // Don't mark as loaded so we can load when genome data arrives
            }
            else {
                console.log('Case 0: Initial mount but no data yet, skipping...');
            }
            isInitialMount.current = false;
        }
        // Case 1: Initial load for GeneViewerPage (genome changed and no filters applied)
        else if (isGeneViewerPage && filtersAreInitial && genomeChanged) {
            shouldLoadFacets = true;
            hasLoadedInitialFacets.current = true;
            console.log('Case 1: GeneViewerPage initial load');
        }
        // Case 2: Initial load for HomePage (species changed and no filters applied)
        else if (!isGeneViewerPage && filtersAreInitial && speciesChanged) {
            shouldLoadFacets = true;
            hasLoadedInitialFacets.current = true;
            console.log('Case 2: HomePage initial load');
        }
        // Case 2.5: Species changed on HomePage (with or without filters applied)
        else if (!isGeneViewerPage && speciesChanged) {
            shouldLoadFacets = true;
            console.log('Case 2.5: HomePage species changed');
        }
        // Case 3: User interaction (search query changes) - for queries >= 2 characters OR when query becomes empty
        else if (searchQueryChanged && (searchQuery.length >= 2 || searchQuery.length === 0)) {
            shouldLoadFacets = true;
            console.log('Case 3: Search query changed');
        }
        // Case 4: Special case for GeneViewerPage - when genome data becomes available after initial mount
        else if (isGeneViewerPage && !hasLoadedInitialFacets.current && selectedGenomes.length > 0) {
            shouldLoadFacets = true;
            hasLoadedInitialFacets.current = true;
            console.log('Case 4: GeneViewerPage genome data became available');
        }
        // Case 5: Filter changes (but not initial load)
        else if (!filtersAreInitial && (filtersChanged || operatorsChanged)) {
            shouldLoadFacets = true;
            console.log('Case 5: Filter changes detected');
        }

        // Load facets if needed
        if (shouldLoadFacets) {
            console.log('Loading facets...');
            // Clear any pending debounced calls
            if (debounceTimeoutRef.current) {
                clearTimeout(debounceTimeoutRef.current);
            }
            // Call loadFacets directly for immediate changes
            loadFacets();
        } else {
            // console.log('No facets loading needed');
        }
    }, [
        selectedSpecies,
        selectedGenomes,
        searchQuery,
        isGeneViewerPage,
        filtersAreInitial,
        filterStore.facetedFilters,
        filterStore.facetOperators
    ]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (debounceTimeoutRef.current) {
                clearTimeout(debounceTimeoutRef.current);
            }
        };
    }, []);

    return {
        facets,
        loading,
        error,
        handleToggleFacet,
        handleOperatorChange,
        refreshFacets,
    };
}; 