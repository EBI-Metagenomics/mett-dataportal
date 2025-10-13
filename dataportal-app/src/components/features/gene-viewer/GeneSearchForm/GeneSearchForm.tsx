import React, {useCallback, useEffect, useMemo, useState, useRef} from 'react';
import GeneSearchInput from './GeneSearchInput';
import styles from "./GeneSearchForm.module.scss";
import GeneResultsTable from "../GeneResultsHandler/GeneResultsTable";
import Pagination from "@components/molecules/Pagination";
import {GeneService} from '../../../../services/gene';
import {createViewState} from '@jbrowse/react-app2';
import {GeneMeta, GeneSuggestion} from "../../../../interfaces/Gene";
import {LinkData} from "../../../../interfaces/Auxiliary";
import {BaseGenome} from "../../../../interfaces/Genome";
import {
    API_GENE_SEARCH_ADVANCED,
    DEFAULT_PER_PAGE_CNT,
    FACET_INITIAL_VISIBLE_CNT,
    FACET_STEP_CNT
} from "../../../../utils/common/constants";
import {copyToClipboard, generateCurlRequest, generateHttpRequest} from "../../../../utils/api";
import SelectedGenomes from "@components/Filters/SelectedGenomes";
import GeneFacetedFilter from "@components/Filters/GeneFacetedFilter";
import {useFacetedFilters} from '../../../../hooks/useFacetedFilters';
import {useFilterStore} from '../../../../stores/filterStore';
import {convertFacetedFiltersToLegacy, convertFacetOperatorsToLegacy} from "../../../../utils/common/filterUtils";

type ViewModel = ReturnType<typeof createViewState>;

interface GeneSearchFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
    selectedSpecies?: string [];
    results: any[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    sortField: string;
    sortOrder: 'asc' | 'desc';
    selectedGenomes: BaseGenome[];
    linkData: LinkData;
    viewState?: ViewModel;
    handleRemoveGenome: (genomeId: string) => void;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    currentPage?: number;
    totalPages?: number;
    hasPrevious?: boolean;
    hasNext?: boolean;
    totalCount?: number;
    onResultsUpdate?: (results: any[], pagination: any) => void;
    onPageSizeChange?: (newPageSize: number) => void;
    onPageChange?: (page: number) => void;
}

const GeneSearchForm: React.FC<GeneSearchFormProps> = ({
                                                           selectedSpecies,
                                                           onSortClick,
                                                           selectedGenomes,
                                                           linkData,
                                                           viewState,
                                                           sortField,
                                                           sortOrder,
                                                           handleRemoveGenome,
                                                           setLoading,
                                                           searchQuery,
                                                           results: resultsProp,
                                                           currentPage: currentPageProp,
                                                           totalPages: totalPagesProp,
                                                           hasPrevious: hasPreviousProp,
                                                           hasNext: hasNextProp,
                                                           totalCount: totalCountProp,
                                                           onResultsUpdate,
                                                           onPageSizeChange,
                                                           onPageChange,
                                                       }) => {

    const renderCount = useRef(0);
    renderCount.current += 1;

    if (process.env.NODE_ENV === 'development' && renderCount.current % 100 === 0) {
        console.log(`GeneSearchForm render #${renderCount.current}`);
    }

    const [searchInput, setSearchInput] = useState<string>('');
    const [query, setQuery] = useState<string>(searchQuery || '');
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<GeneSuggestion[]>([]);
    const [geneName, setGeneName] = useState<string>('');
    const [results, setResults] = useState<GeneMeta[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);
    const [pageSize, setPageSize] = useState<number>(DEFAULT_PER_PAGE_CNT);
    const [isDownloading, setIsDownloading] = useState(false);
    const [isProcessingSuggestion, setIsProcessingSuggestion] = useState<boolean>(false);
    const [currentLocusTag, setCurrentLocusTag] = useState<string>('');
    const lastPageSizeRef = useRef<number>(DEFAULT_PER_PAGE_CNT);

    useEffect(() => {
        if (resultsProp && resultsProp.length > 0) {
            console.log('GeneSearchForm - Syncing results from props:', resultsProp.length);
            setResults(resultsProp);
            setCurrentPage(currentPageProp || 1);
            setTotalPages(totalPagesProp || 1);
            setHasPrevious(hasPreviousProp || false);
            setHasNext(hasNextProp || false);
        }
    }, [resultsProp, currentPageProp, totalPagesProp, hasPreviousProp, hasNextProp]);

    useEffect(() => {
        if (currentPageProp !== undefined) {
            setCurrentPage(currentPageProp);
        }
        if (totalPagesProp !== undefined) {
            setTotalPages(totalPagesProp);
        }
        if (hasPreviousProp !== undefined) {
            setHasPrevious(hasPreviousProp);
        }
        if (hasNextProp !== undefined) {
            setHasNext(hasNextProp);
        }
    }, [currentPageProp, totalPagesProp, hasPreviousProp, hasNextProp]);

    const facetedFilters = useFilterStore(state => state.facetedFilters);
    const facetOperators = useFilterStore(state => state.facetOperators);
    const setGeneSearchQuery = useFilterStore(state => state.setGeneSearchQuery);
    const setGeneSortField = useFilterStore(state => state.setGeneSortField);
    const setGeneSortOrder = useFilterStore(state => state.setGeneSortOrder);
    const selectedSpeciesFromStore = useFilterStore(state => state.selectedSpecies);

    const {
        facets,
        loading: facetsLoading,
        error: facetsError,
        handleToggleFacet,
        handleOperatorChange,
        refreshFacets
    } = useFacetedFilters({
        selectedSpecies: selectedSpeciesFromStore,
        selectedGenomes,
        searchQuery: isProcessingSuggestion ? currentLocusTag : debouncedSearchQuery, // Use locus tag when processing suggestion
    });

    const [apiRequestDetails, setApiRequestDetails] = useState<{
        url: string;
        method: string;
        headers: any;
        body?: any
    } | null>(null);

    const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newSize = parseInt(event.target.value, DEFAULT_PER_PAGE_CNT);
        setPageSize(newSize);
        if (onPageSizeChange) {
            onPageSizeChange(newSize);
        }
    };

    const getLegacyFilters = useCallback(() => {
        return convertFacetedFiltersToLegacy(facetedFilters);
    }, [facetedFilters]);

    const getLegacyOperators = useCallback(() => {
        return convertFacetOperatorsToLegacy(facetOperators);
    }, [facetOperators]);

    const fetchSuggestions = useCallback(
        async (inputQuery: string) => {
            if (inputQuery.length >= 2) {
                try {
                    let response;

                    if (selectedSpecies && selectedSpecies.length === 1) {
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            selectedSpecies[0],
                            undefined,
                            getLegacyFilters()
                        );
                    }
                    else if (selectedGenomes && selectedGenomes.length > 0) {
                        const genomeIds = selectedGenomes.map(genome => genome.isolate_name).join(',');
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            undefined,
                            genomeIds,
                            getLegacyFilters()
                        );
                    } else {
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            undefined,
                            undefined,
                            getLegacyFilters()
                        );
                    }

                    if (response) {
                        setSuggestions(response);
                    }
                } catch (error) {
                    console.error('Error fetching suggestions:', error);
                }
            } else {
                setSuggestions([]);
            }
        },
        [selectedSpecies, selectedGenomes, getLegacyFilters]
    );


    const debounce = (func: Function, delay: number) => {
        let timeoutId: ReturnType<typeof setTimeout>;
        return (...args: any[]) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(null, args), delay);
        };
    };


    // Fetch search results based on the query, selected species, page, sort field, and sort order
    const fetchSearchResults = useCallback(
        async (
            page = 1,
            sortField: string,
            sortOrder: string,
            selectedFacetFilters: Record<string, string[]>,
            facetOperators?: Record<string, 'AND' | 'OR'>
        ) => {
            const genomeFilter = selectedGenomes?.length
                ? selectedGenomes.map((genome) => ({
                    isolate_name: genome.isolate_name,
                    type_strain: genome.type_strain
                }))
                : undefined;
            const speciesFilter = selectedSpecies?.length === 1 ? selectedSpecies : undefined;

            console.log('fetchSearchResults called with:', {
                query,
                page,
                sortField,
                sortOrder,
                genomeFilter,
                speciesFilter,
                selectedGenomes,
                selectedSpecies
            });

            try {
                setLoading(true); // Start spinner
                let response = null;

                const params = GeneService.buildParamsFetchGeneSearchResults(
                    query,
                    page,
                    pageSize,
                    sortField,
                    sortOrder,
                    genomeFilter,
                    speciesFilter,
                    selectedFacetFilters
                );

                const apiDetails = {
                    url: API_GENE_SEARCH_ADVANCED,
                    method: "GET",
                    headers: {"Content-Type": "application/json"},
                    params: Object.fromEntries(params.entries()),
                };

                // console.log('API details:', apiDetails);
                // console.log('API params:', Object.fromEntries(params.entries()));
                setApiRequestDetails(apiDetails);

                // console.log('Calling GeneService.fetchGeneSearchResultsAdvanced with:', {
                //     query,
                //     page,
                //     pageSize,
                //     sortField,
                //     sortOrder,
                //     genomeFilter,
                //     speciesFilter,
                //     selectedFacetFilters,
                //     facetOperators
                // });

                response = await GeneService.fetchGeneSearchResultsAdvanced(
                    query,
                    page,
                    pageSize,
                    sortField,
                    sortOrder,
                    genomeFilter,
                    speciesFilter,
                    selectedFacetFilters,
                    facetOperators,
                    undefined // No locus_tag for faceted search
                );
                if (response && response.data && response.pagination) {
                    console.log('GeneSearchForm - Search results received:', {
                        dataLength: response.data.length,
                        pagination: response.pagination,
                        isHomePage: !!onResultsUpdate
                    });
                    
                    // If onResultsUpdate callback is provided
                    if (onResultsUpdate) {
                        console.log('GeneSearchForm - Using onResultsUpdate callback for fetchSearchResults');
                        onResultsUpdate(response.data, response.pagination);
                    } else {
                        console.log('GeneSearchForm - Updating internal state for fetchSearchResults');
                        setResults(response.data);
                        setCurrentPage(response.pagination.page_number);
                        setTotalPages(response.pagination.num_pages);
                        setHasPrevious(response.pagination.has_previous);
                        setHasNext(response.pagination.has_next);
                    }
                } else {
                    if (onResultsUpdate) {
                        onResultsUpdate([], null);
                    } else {
                        setResults([]);
                        setCurrentPage(1);
                        setTotalPages(1);
                        setHasPrevious(false);
                        setHasNext(false);
                    }
                }
            } catch (error) {
                console.error("Error fetching data:", error);
                if (onResultsUpdate) {
                    onResultsUpdate([], null);
                } else {
                    setResults([]);
                    setCurrentPage(1);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
                }
            } finally {
                setLoading(false); // Stop spinner
            }
        },
        [query, selectedGenomes, selectedSpecies, pageSize, getLegacyFilters, getLegacyOperators]
    );

    // Trigger new search when page size changes
    useEffect(() => {
        if (pageSize !== lastPageSizeRef.current && (query || selectedGenomes.length > 0 || (selectedSpecies && selectedSpecies.length > 0))) {
            console.log('GeneSearchForm - Page size changed, triggering new search with pageSize:', pageSize);
            lastPageSizeRef.current = pageSize;
            fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
        }
    }, [pageSize, sortField, sortOrder, query, selectedGenomes.length, selectedSpecies]);

    // Debounced
    const debouncedUpdateQuery = useCallback(
        debounce((newQuery: string) => {
            if (!isProcessingSuggestion) {
                console.log('debouncedUpdateQuery called with:', newQuery);
                setQuery(newQuery);
                const searchWithQuery = async () => {
                    const genomeFilter = selectedGenomes?.length
                        ? selectedGenomes.map((genome) => ({
                            isolate_name: genome.isolate_name,
                            type_strain: genome.type_strain
                        }))
                        : undefined;
                    const speciesFilter = selectedSpecies?.length === 1 ? selectedSpecies : undefined;
                                    try {
                    setLoading(true);
                    const response = await GeneService.fetchGeneSearchResultsAdvanced(
                        newQuery,
                        1,
                        pageSize,
                        sortField,
                        sortOrder,
                        genomeFilter,
                        speciesFilter,
                        getLegacyFilters(),
                        getLegacyOperators(),
                        undefined // No locus_tag for text search
                    );
                    if (response && response.data && response.pagination) {
                            // If onResultsUpdate callback is provided
                            if (onResultsUpdate) {
                                // console.log('GeneSearchForm - Using onResultsUpdate callback for debouncedUpdateQuery');
                                onResultsUpdate(response.data, response.pagination);
                            } else {
                                // console.log('GeneSearchForm - Updating internal state for debouncedUpdateQuery');
                                setResults(response.data);
                                setCurrentPage(response.pagination.page_number);
                                setTotalPages(response.pagination.num_pages);
                                setHasPrevious(response.pagination.has_previous);
                                setHasNext(response.pagination.has_next);
                            }
                        } else {
                            if (onResultsUpdate) {
                                onResultsUpdate([], null);
                            } else {
                                setResults([]);
                                setCurrentPage(1);
                                setTotalPages(1);
                                setHasPrevious(false);
                                setHasNext(false);
                            }
                        }
                    } catch (error) {
                        console.error("Error fetching data:", error);
                        if (onResultsUpdate) {
                            onResultsUpdate([], null);
                        } else {
                            setResults([]);
                            setCurrentPage(1);
                            setTotalPages(1);
                            setHasPrevious(false);
                            setHasNext(false);
                        }
                    } finally {
                        setLoading(false);
                    }
                };
                searchWithQuery();
            } else {
                console.log('debouncedUpdateQuery skipped due to suggestion processing');
            }
        }, 500), // 500ms delay
        [selectedGenomes, selectedSpecies, pageSize, sortField, sortOrder, getLegacyFilters, getLegacyOperators, isProcessingSuggestion, onResultsUpdate]
    );

    // Debounced function for updating the search query used by faceted filters
    const debouncedUpdateSearchQuery = useCallback(
        debounce((newQuery: string) => {
            if (!isProcessingSuggestion) {
                console.log('debouncedUpdateSearchQuery called with:', newQuery);
                setDebouncedSearchQuery(newQuery);
            } else {
                console.log('debouncedUpdateSearchQuery skipped due to suggestion processing');
            }
        }, 300), // 300ms delay for faceted filters
        [isProcessingSuggestion]
    );

    const debouncedFetchSuggestions = useCallback(
        debounce((input: string) => {
            if (!isProcessingSuggestion && input.length >= 2) {
                console.log('debouncedFetchSuggestions called with:', input);
                GeneService.fetchGeneAutocompleteSuggestions(
                    input,
                    10,
                    selectedSpecies?.length === 1 ? selectedSpecies[0] : undefined,
                    selectedGenomes.map(g => g.isolate_name).join(","),
                    getLegacyFilters()
                ).then(setSuggestions).catch(console.error);
            } else {
                console.log('debouncedFetchSuggestions skipped - input length or processing suggestion');
                setSuggestions([]);
            }
        }, 300), // 300ms delay for suggestions
        [selectedSpecies, selectedGenomes, getLegacyFilters, isProcessingSuggestion]
    );

    // For GeneViewerPage: load initial data when genome changes
    // GeneViewerPage is determined by having selected genomes but no species (since it's focused on a specific genome)
    const isGeneViewerPage = React.useMemo(() => selectedGenomes.length > 0 && (selectedSpecies?.length ?? 0) === 0, [selectedSpecies?.length, selectedGenomes.length]);
    const lastGenomeRef = React.useRef<string | null>(null);
    const lastSpeciesRef = React.useRef<string[]>([]);
    const hasLoadedInitialData = React.useRef(false);

    // Helper to check if filters are in their initial state (no user interaction)
    const filtersAreInitial = useMemo(
        () => Object.keys(facetedFilters).length === 0 && Object.keys(facetOperators).length === 0,
        [facetedFilters, facetOperators]
    );

    // Initial load effect
    useEffect(() => {
        // console.log('GeneSearchForm - Initial load effect:', {
        //     isGeneViewerPage,
        //     filtersAreInitial,
        //     selectedGenomes,
        //     selectedSpecies,
        //     hasLoadedInitialData: hasLoadedInitialData.current
        // });
        
        if (isGeneViewerPage && filtersAreInitial) {
            const genomeId = selectedGenomes[0]?.isolate_name || null;
            if (genomeId !== lastGenomeRef.current) {
                lastGenomeRef.current = genomeId;
                hasLoadedInitialData.current = false;
            }
            if (selectedGenomes.length > 0 && !hasLoadedInitialData.current) {
                hasLoadedInitialData.current = true;
                // console.log('GeneSearchForm - Loading initial data for GeneViewerPage');

                const timeoutId = setTimeout(() => {
                    const currentFilters = getLegacyFilters();
                    const currentOperators = getLegacyOperators();
                    fetchSearchResults(1, sortField, sortOrder, currentFilters, currentOperators);
                }, 0);
                
                return () => clearTimeout(timeoutId);
            }
        }
        // Removed the HomePage logic - HomePage now handles its own initial load
    }, [selectedGenomes, selectedSpecies, isGeneViewerPage, filtersAreInitial]);

    useEffect(() => {
        // console.log('GeneSearchForm - User interaction effect triggered:', {
        //     filtersAreInitial,
        //     facetedFilters,
        //     facetOperators
        // });
        
        if (!filtersAreInitial) {
            // Use refs to get the latest values without creating dependencies
            const currentFilters = getLegacyFilters();
            const currentOperators = getLegacyOperators();
            
            console.log('GeneSearchForm - Calling fetchSearchResults with:', {
                currentFilters,
                currentOperators
            });
            
            // Use a timeout to break the circular dependency
            const timeoutId = setTimeout(() => {
                fetchSearchResults(1, sortField, sortOrder, currentFilters, currentOperators);
            }, 0);
            
            return () => clearTimeout(timeoutId);
        }
    }, [facetedFilters, facetOperators, filtersAreInitial]);

    useEffect(() => {
        console.log('GeneSearchForm - Fallback effect:', {
            hasLoadedInitialData: hasLoadedInitialData.current,
            resultsLength: results.length
        });

    }, [results.length]);

    // Trigger search when sort parameters change (ONLY for GeneViewerPage)
    useEffect(() => {
        // Skip this effect for HomePage (which uses onResultsUpdate callback)
        if (onResultsUpdate) {
            console.log('GeneSearchForm - Skipping sort trigger for HomePage');
            return;
        }
        
        // Only trigger if we have existing results (to avoid triggering on initial load)
        const effectiveResults = resultsProp && resultsProp.length > 0 ? resultsProp : results;
        if (effectiveResults.length > 0) {
            console.log('GeneSearchForm - Sort parameters changed, triggering search for GeneViewerPage:', {
                sortField,
                sortOrder,
                resultsLength: effectiveResults.length
            });
            
            // timeout
            const timeoutId = setTimeout(() => {
                // reset to page 1 when sorting
                fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
            }, 0);
            
            return () => clearTimeout(timeoutId);
        }
    }, [sortField, sortOrder, results.length, resultsProp, onResultsUpdate]);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newInput = event.target.value;
        console.log('handleInputChange called with:', newInput, 'isProcessingSuggestion:', isProcessingSuggestion);

        const looksLikeDisplayText = newInput.includes('(') && newInput.includes(')') && newInput.includes(' - ');

        setSearchInput(newInput);
        setGeneName('');

        if (!isProcessingSuggestion && !looksLikeDisplayText) {
            // console.log('Calling debounced functions for input:', newInput);
            
            // Special handling for empty input - trigger HomePage initial load
            if (newInput.trim() === '' && onResultsUpdate) {
                // console.log('GeneSearchForm - Empty input detected, triggering HomePage initial load');
                // Reset to initial state for HomePage
                setQuery('');
                setDebouncedSearchQuery('');
                setGeneSearchQuery('');
                setSuggestions([]);
                return;
            }
            
            debouncedUpdateQuery(newInput);
            debouncedUpdateSearchQuery(newInput);
            debouncedFetchSuggestions(newInput);

            setGeneSearchQuery(newInput);
        } else {
            console.log('Skipping debounced functions - processing suggestion or display text detected');
        }
    };

    const handleSuggestionClick = (suggestion: GeneSuggestion) => {
        const selectedValue = suggestion.locus_tag;
        console.log('handleSuggestionClick - selectedValue (locus tag):', selectedValue);
        console.log('handleSuggestionClick - suggestion:', suggestion);

        setIsProcessingSuggestion(true);
        setCurrentLocusTag(selectedValue);
        setQuery(selectedValue);
        // Update searchInput to show a user-friendly display value
        const displayValue = suggestion.gene_name
            ? `${suggestion.gene_name} (${suggestion.locus_tag})`
            : suggestion.locus_tag;
        setSearchInput(displayValue);
        setGeneName(suggestion.gene_name);
        setSuggestions([]);

        setGeneSearchQuery(selectedValue);

        const searchWithLocusTag = async () => {
            const genomeFilter = selectedGenomes?.length
                ? selectedGenomes.map((genome) => ({
                    isolate_name: genome.isolate_name,
                    type_strain: genome.type_strain
                }))
                : undefined;
            const speciesFilter = selectedSpecies?.length === 1 ? selectedSpecies : undefined;
            try {
                setLoading(true);
                console.log('Making API call with locus tag:', selectedValue);
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    "", // Empty query since we're using locus_tag
                    1,
                    pageSize,
                    sortField,
                    sortOrder,
                    genomeFilter,
                    speciesFilter,
                    getLegacyFilters(),
                    getLegacyOperators(),
                    selectedValue // Pass as locus_tag parameter
                );
                if (response && response.data && response.pagination) {
                    // If onResultsUpdate callback is provided
                    if (onResultsUpdate) {
                        // console.log('GeneSearchForm - Using onResultsUpdate callback for HomePage');
                        onResultsUpdate(response.data, response.pagination);
                    } else {
                        // console.log('GeneSearchForm - Updating internal state for GeneViewerPage');
                        setResults(response.data);
                        setCurrentPage(response.pagination.page_number);
                        setTotalPages(response.pagination.num_pages);
                        setHasPrevious(response.pagination.has_previous);
                        setHasNext(response.pagination.has_next);
                    }
                } else {
                    if (onResultsUpdate) {
                        onResultsUpdate([], null);
                    } else {
                        setResults([]);
                        setCurrentPage(1);
                        setTotalPages(1);
                        setHasPrevious(false);
                        setHasNext(false);
                    }
                }
            } catch (error) {
                console.error("Error fetching data:", error);
                if (onResultsUpdate) {
                    onResultsUpdate([], null);
                } else {
                    setResults([]);
                    setCurrentPage(1);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
                }
            } finally {
                setLoading(false);
                setIsProcessingSuggestion(false);
                setCurrentLocusTag('');
            }
        };
        searchWithLocusTag();
    };

    const handleSearch = () => {
        const currentSearchInput = searchInput;
        setQuery(currentSearchInput);

        setGeneSearchQuery(currentSearchInput);
        const searchWithQuery = async () => {
            const genomeFilter = selectedGenomes?.length
                ? selectedGenomes.map((genome) => ({
                    isolate_name: genome.isolate_name,
                    type_strain: genome.type_strain
                }))
                : undefined;
            const speciesFilter = selectedSpecies?.length === 1 ? selectedSpecies : undefined;
            try {
                setLoading(true);
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    currentSearchInput, // Use currentSearchInput directly
                    1,
                    pageSize,
                    sortField,
                    sortOrder,
                    genomeFilter,
                    speciesFilter,
                    getLegacyFilters(),
                    getLegacyOperators(),
                    undefined // No locus_tag for text search
                );
                if (response && response.data && response.pagination) {
                    // If onResultsUpdate callback is provided
                    if (onResultsUpdate) {
                        // console.log('GeneSearchForm - Using onResultsUpdate callback for HomePage search');
                        onResultsUpdate(response.data, response.pagination);
                    } else {
                        // console.log('GeneSearchForm - Updating internal state for GeneViewerPage search');
                        setResults(response.data);
                        setCurrentPage(response.pagination.page_number);
                        setTotalPages(response.pagination.num_pages);
                        setHasPrevious(response.pagination.has_previous);
                        setHasNext(response.pagination.has_next);
                    }
                } else {
                    if (onResultsUpdate) {
                        onResultsUpdate([], null);
                    } else {
                        setResults([]);
                        setCurrentPage(1);
                        setTotalPages(1);
                        setHasPrevious(false);
                        setHasNext(false);
                    }
                }
            } catch (error) {
                console.error("Error fetching data:", error);
                if (onResultsUpdate) {
                    onResultsUpdate([], null);
                } else {
                    setResults([]);
                    setCurrentPage(1);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
                }
            } finally {
                setLoading(false);
            }
        };
        searchWithQuery();
    };

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        handleSearch();
    };

    const handleDownloadTSV = async () => {
        try {
            setIsDownloading(true);
            // Show initial message for large downloads
            alert('Starting download... This may take a while for large datasets.');

            await GeneService.downloadGenesTSV(
                query,
                sortField,
                sortOrder,
                selectedGenomes,
                selectedSpecies,
                getLegacyFilters(),
                getLegacyOperators()
            );
            // alert('Download completed successfully!');
        } catch (error) {
            console.error('Error downloading TSV:', error);
            alert('Failed to download TSV file. Please try again or contact support if the problem persists.');
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <section id="genes">
            <div>
                <p/>
            </div>
            <div className={styles.leftPane}>
                <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome}/>

                <GeneFacetedFilter
                    facets={facets}
                    onToggleFacet={handleToggleFacet}
                    initialVisibleCount={FACET_INITIAL_VISIBLE_CNT}
                    loadMoreStep={FACET_STEP_CNT}
                    onOperatorChange={handleOperatorChange}
                />
            </div>
            <div className={styles.rightPane}>
                <form onSubmit={handleSubmit}
                      className="vf-form vf-form--search vf-form--search--responsive | vf-sidebar vf-sidebar--end">
                    <h2 className={`vf-section-header__subheading ${styles.vfGeneSubHeading}`}>Gene Search</h2>
                    <div>
                        <p/>
                    </div>
                    <GeneSearchInput
                        query={searchInput}
                        onInputChange={handleInputChange}
                        suggestions={suggestions}
                        onSuggestionClick={handleSuggestionClick}
                        onSuggestionsClear={() => setSuggestions([])}
                        onSearch={handleSearch}
                    />
                </form>
                <div>
                    <p>&nbsp;</p>
                </div>

                <div className="vf-grid__col--span-3" id="results-table"
                     style={{display: (results.length > 0 || (resultsProp && resultsProp.length > 0)) ? 'block' : 'none'}}>
                    <GeneResultsTable
                        results={resultsProp && resultsProp.length > 0 ? resultsProp : results}
                        onSortClick={onSortClick}
                        linkData={linkData}
                        viewState={viewState}
                        setLoading={setLoading}
                        isTypeStrainAvailable={selectedGenomes.length ? selectedGenomes.some(genome => genome.type_strain) : true}
                        onDownloadTSV={handleDownloadTSV}
                        isLoading={isDownloading}
                        sortField={sortField}
                        sortOrder={sortOrder}
                    />
                    {/* Page size dropdown and pagination */}
                    <div className={styles.paginationContainer}>
                        <div className={styles.pageSizeDropdown}>
                            <label htmlFor="pageSize">Page Size: </label>
                            <select
                                id="pageSize"
                                value={pageSize}
                                onChange={handlePageSizeChange}
                                className={styles.pageSizeSelect}
                            >
                                <option value={DEFAULT_PER_PAGE_CNT}>Show 10</option>
                                <option value={20}>Show 20</option>
                                <option value={50}>Show 50</option>
                            </select>
                        </div>
                        <div className={styles.paginationBar}>
                            {(() => {
                                // Use props if available (HomePage), otherwise use internal state (GeneViewerPage)
                                const effectiveTotalPages = totalPagesProp || totalPages;
                                const effectiveHasNext = hasNextProp !== undefined ? hasNextProp : hasNext;
                                const effectiveHasPrevious = hasPreviousProp !== undefined ? hasPreviousProp : hasPrevious;
                                const effectiveCurrentPage = currentPageProp || currentPage;
                                const effectiveResults = resultsProp && resultsProp.length > 0 ? resultsProp : results;
                                
                                // Show pagination if we have results AND (more than 1 page OR pagination data)
                                const shouldShowPagination = effectiveResults.length > 0 && (effectiveTotalPages > 1 || effectiveHasNext || effectiveHasPrevious);
                                
                                // console.log('GeneSearchForm - Pagination visibility check:', {
                                //     effectiveTotalPages,
                                //     effectiveHasNext,
                                //     effectiveHasPrevious,
                                //     effectiveCurrentPage,
                                //     shouldShowPagination,
                                //     resultsLength: effectiveResults.length,
                                //     isHomePage: !!onResultsUpdate
                                // });
                                
                                return shouldShowPagination;
                            })() && (
                                <Pagination
                                    currentPage={currentPageProp || currentPage}
                                    totalPages={totalPagesProp || totalPages}
                                    hasPrevious={hasPreviousProp !== undefined ? hasPreviousProp : hasPrevious}
                                    hasNext={hasNextProp !== undefined ? hasNextProp : hasNext}
                                    onPageClick={(page) => {

                                        if (onResultsUpdate) {
                                            console.log('GeneSearchForm - Pagination click for HomePage, page:', page);

                                            const searchWithPage = async () => {
                                                const genomeFilter = selectedGenomes?.length
                                                    ? selectedGenomes.map((genome) => ({
                                                        isolate_name: genome.isolate_name,
                                                        type_strain: genome.type_strain
                                                    }))
                                                    : undefined;
                                                const speciesFilter = selectedSpecies?.length === 1 ? selectedSpecies : undefined;
                                                try {
                                                    setLoading(true);
                                                    const response = await GeneService.fetchGeneSearchResultsAdvanced(
                                                        query,
                                                        page,
                                                        pageSize,
                                                        sortField,
                                                        sortOrder,
                                                        genomeFilter,
                                                        speciesFilter,
                                                        getLegacyFilters(),
                                                        getLegacyOperators(),
                                                        undefined // No locus_tag for pagination
                                                    );
                                                    if (response && response.data && response.pagination) {
                                                        onResultsUpdate(response.data, response.pagination);
                                                    } else {
                                                        onResultsUpdate([], null);
                                                    }
                                                } catch (error) {
                                                    console.error("Error fetching data for pagination:", error);
                                                    onResultsUpdate([], null);
                                                } finally {
                                                    setLoading(false);
                                                }
                                            };
                                            searchWithPage();
                                        } else if (onPageChange) {
                                            // Use the provided page change handler (for GeneViewerPage)
                                            onPageChange(page);
                                        } else {
                                            // Fallback to internal handling
                                            setCurrentPage(page);
                                            fetchSearchResults(page, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
                                        }
                                    }}
                                />
                            )}
                        </div>
                    </div>
                </div>
                <div><p/></div>
                <div className={styles.rightPaneButtons}>
                    <button className="vf-button vf-button--primary vf-button--sm"
                            onClick={() => copyToClipboard(generateCurlRequest(apiRequestDetails))}>Copy cURL
                        Request
                    </button>
                    <button className="vf-button vf-button--primary vf-button--sm"
                            onClick={() => copyToClipboard(generateHttpRequest(apiRequestDetails))}>Copy HTTP
                        Request
                    </button>
                </div>
                <div><p/></div>


                <div>
                    <p>&nbsp;</p>
                    <p>&nbsp;</p>
                    <p>&nbsp;</p>
                </div>
            </div>
        </section>
    );
};

export default GeneSearchForm;
