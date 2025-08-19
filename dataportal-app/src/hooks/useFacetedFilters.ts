import React, {useState, useEffect, useCallback, useRef} from 'react';
import {useLocation} from 'react-router-dom';
import {useFilterStore, FacetedFilters, FacetOperators} from '../stores/filterStore';
import {GeneService} from '../services/gene';
import {GeneFacetResponse} from '../interfaces/Gene';

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
                
                // Update the selected state for each item
                items.forEach(item => {
                    const wasSelected = item.selected;
                    const isSelected = selectedValues.some(v => String(v) === String(item.value));
                    
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
    const handleToggleFacet = useCallback((facetGroup: string, value: string | boolean) => {
        console.log('handleToggleFacet called:', { facetGroup, value });
        
        const currentFilters = filterStore.facetedFilters;
        const currentValues = currentFilters[facetGroup as keyof FacetedFilters] || [];

        console.log('Current filter state:', { currentFilters, currentValues });

        // Handle different filter types
        if (facetGroup === 'has_amr_info') {
            const boolValues = currentValues as boolean[];
            const boolValue = value as boolean;
            const newValues = boolValues.includes(boolValue)
                ? boolValues.filter(v => v !== boolValue)
                : [...boolValues, boolValue];
            console.log('Updating has_amr_info filter:', { boolValues, boolValue, newValues });
            filterStore.updateFacetedFilter('has_amr_info', newValues);
        } else {
            const stringValues = currentValues as string[];
            const stringValue = String(value);
            const newValues = stringValues.includes(stringValue)
                ? stringValues.filter(v => v !== stringValue)
                : [...stringValues, stringValue];
            console.log('Updating filter:', { facetGroup, stringValues, stringValue, newValues });
            filterStore.updateFacetedFilter(facetGroup as keyof FacetedFilters, newValues);
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