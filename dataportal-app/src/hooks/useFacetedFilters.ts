import React, {useState, useEffect, useCallback, useRef} from 'react';
import {useLocation} from 'react-router-dom';
import {useFilterStore, FacetedFilters, FacetOperators} from '../stores/filterStore';
import {GeneService} from '../services/geneService';
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


    const loadFacets = useCallback(async () => {
        // Prevent duplicate calls
        if (isLoadingFacets.current) {
            console.log('loadFacets already in progress, skipping...');
            return;
        }

        try {
            console.log('loadFacets called with:', {
                selectedSpecies,
                selectedGenomes,
                searchQuery,
                filterStore: filterStore.facetedFilters,
                operators: filterStore.facetOperators
            });

            isLoadingFacets.current = true;
            setLoading(true);
            setError(null);

            const speciesAcronym = selectedSpecies?.[0];
            const isolates = selectedGenomes.map(genome => genome.isolate_name).join(',');
            const apiFilters = getApiFilters();

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

            console.log('API response received:', response);

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

            console.log('Setting facets:', updatedFacets);
            setFacets(updatedFacets);
        } catch (err) {
            console.error('Error loading facets:', err);
            setError('Failed to load filter options');
        } finally {
            setLoading(false);
            isLoadingFacets.current = false;
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

    const handleOperatorChange = useCallback((facetGroup: string, operator: 'AND' | 'OR') => {
        filterStore.updateFacetOperator(facetGroup as keyof FacetOperators, operator);
    }, [filterStore]);

    const refreshFacets = useCallback(async () => {
        await loadFacets();
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
        // Create change detection keys
        const currentGenomeKey = selectedGenomes[0]?.isolate_name || '';
        const currentSpeciesKey = selectedSpecies.join(',');
        const currentFiltersKey = JSON.stringify(filterStore.facetedFilters);
        const currentOperatorsKey = JSON.stringify(filterStore.facetOperators);

        const genomeChanged = currentGenomeKey !== lastGenomeRef.current;
        const speciesChanged = currentSpeciesKey !== lastSpeciesRef.current.join(',');
        const searchQueryChanged = searchQuery !== lastSearchQueryRef.current;
        const filtersChanged = currentFiltersKey !== lastFiltersRef.current;
        const operatorsChanged = currentOperatorsKey !== lastOperatorsRef.current;

        if (genomeChanged && isLoadingFacets.current) {
            console.log('Genome changed while loading, resetting loading flag');
            isLoadingFacets.current = false;
        }

        console.log('useFacetedFilters useEffect:', {
            currentGenomeKey,
            currentSpeciesKey,
            searchQuery,
            searchQueryLength: searchQuery.length,
            isGeneViewerPage,
            filtersAreInitial,
            genomeChanged,
            speciesChanged,
            searchQueryChanged,
            filtersChanged,
            operatorsChanged,
            hasLoadedInitialFacets: hasLoadedInitialFacets.current,
            isInitialMount: isInitialMount.current,
            selectedGenomes: selectedGenomes,
            selectedGenomesLength: selectedGenomes.length
        });

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
        // Case 3: User interaction (search query, facet changes, etc.) - for queries >= 2 characters OR when query becomes empty
        else if ((searchQueryChanged && (searchQuery.length >= 2 || searchQuery.length === 0)) || filtersChanged || operatorsChanged) {
            shouldLoadFacets = true;
            console.log('Case 3: User interaction');
        }
        // Case 4: Special case for GeneViewerPage - when genome data becomes available after initial mount
        else if (isGeneViewerPage && !hasLoadedInitialFacets.current && selectedGenomes.length > 0) {
            shouldLoadFacets = true;
            hasLoadedInitialFacets.current = true;
            console.log('Case 4: GeneViewerPage genome data became available');
        }

        // Load facets if needed
        if (shouldLoadFacets) {
            console.log('Loading facets...');
            // Call loadFacets directly instead of using setTimeout
            loadFacets();
        } else {
            console.log('No facets loading needed');
        }
    }, [
        selectedSpecies,
        selectedGenomes,
        searchQuery,
        filterStore.facetedFilters,
        filterStore.facetOperators,
        isGeneViewerPage,
        filtersAreInitial,
        loadFacets
    ]);

    return {
        facets,
        loading,
        error,
        handleToggleFacet,
        handleOperatorChange,
        refreshFacets,
    };
}; 