import React, {useCallback, useEffect, useMemo, useRef, useState} from 'react';
import {GeneService} from '../../../../../services/gene';
import {GeneMeta, GeneSuggestion} from '../../../../../interfaces/Gene';
import {BaseGenome} from '../../../../../interfaces/Genome';
import {
    API_GENE_SEARCH_ADVANCED,
    DEFAULT_PER_PAGE_CNT,
} from '../../../../../utils/common/constants';
import {useFacetedFilters} from '../../../../../hooks/useFacetedFilters';
import {useFilterStore} from '../../../../../stores/filterStore';
import {
    convertFacetedFiltersToLegacy,
    convertFacetOperatorsToLegacy,
} from '../../../../../utils/common/filterUtils';
import {genomesForQuery, looksLikeLocusTag} from '../utils/geneSearchHelpers';

export interface UseGeneSearchControllerArgs {
    searchQuery: string;
    selectedSpecies?: string[];
    selectedGenomes: BaseGenome[];
    extraIsolates?: string[];
    sortField: string;
    sortOrder: 'asc' | 'desc';
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    resultsProp?: GeneMeta[];
    currentPageProp?: number;
    totalPagesProp?: number;
    hasPreviousProp?: boolean;
    hasNextProp?: boolean;
    onResultsUpdate?: (results: GeneMeta[], pagination: any) => void;
    onPageSizeChange?: (newPageSize: number) => void;
    onPageChange?: (page: number) => void;
}

function debounce<T extends (...args: any[]) => void>(func: T, delay: number) {
    let timeoutId: ReturnType<typeof setTimeout>;
    return (...args: Parameters<T>) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

export function useGeneSearchController({
    searchQuery,
    selectedSpecies,
    selectedGenomes,
    extraIsolates = [],
    sortField,
    sortOrder,
    setLoading,
    resultsProp,
    currentPageProp,
    totalPagesProp,
    hasPreviousProp,
    hasNextProp,
    onResultsUpdate,
    onPageSizeChange,
    onPageChange,
}: UseGeneSearchControllerArgs) {
    const [searchInput, setSearchInput] = useState<string>(searchQuery || '');
    const [query, setQuery] = useState<string>(searchQuery || '');
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState<string>(searchQuery || '');
    const [suggestions, setSuggestions] = useState<GeneSuggestion[]>([]);
    const [results, setResults] = useState<GeneMeta[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);
    const [pageSize, setPageSize] = useState<number>(DEFAULT_PER_PAGE_CNT);
    const [isDownloading, setIsDownloading] = useState(false);
    const [isProcessingSuggestion, setIsProcessingSuggestion] = useState(false);
    const [currentLocusTag, setCurrentLocusTag] = useState('');
    const [apiRequestDetails, setApiRequestDetails] = useState<{
        url: string;
        method: string;
        headers: Record<string, string>;
        params?: Record<string, string>;
        body?: unknown;
    } | null>(null);

    const lastPageSizeRef = useRef(DEFAULT_PER_PAGE_CNT);
    const ignoreStoreSyncRef = useRef(false);
    const searchRequestIdRef = useRef(0);
    const isInitialFacetPhaseRef = useRef(true);
    const lastGenomeRef = useRef<string | null>(null);
    const hasLoadedInitialData = useRef(false);
    const isHomePageMode = Boolean(onResultsUpdate);

    useEffect(() => {
        if (ignoreStoreSyncRef.current || isProcessingSuggestion) {
            return;
        }
        const storeQuery = searchQuery || '';
        if (storeQuery === searchInput || storeQuery === query) {
            return;
        }
        setSearchInput(storeQuery);
        setQuery(storeQuery);
        setDebouncedSearchQuery(storeQuery);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchQuery, isProcessingSuggestion]);

    useEffect(() => {
        if (!isHomePageMode || resultsProp === undefined) {
            return;
        }
        setResults(resultsProp || []);
        setCurrentPage(currentPageProp || 1);
        setTotalPages(totalPagesProp || 1);
        setHasPrevious(hasPreviousProp || false);
        setHasNext(hasNextProp || false);
    }, [
        isHomePageMode,
        resultsProp,
        currentPageProp,
        totalPagesProp,
        hasPreviousProp,
        hasNextProp,
    ]);

    const facetedFilters = useFilterStore((state) => state.facetedFilters);
    const facetOperators = useFilterStore((state) => state.facetOperators);
    const setGeneSearchQuery = useFilterStore((state) => state.setGeneSearchQuery);
    const clearFacetedFilters = useFilterStore((state) => state.clearFacetedFilters);

    const {
        facets,
        loading: facetsLoading,
        handleToggleFacet,
        handleOperatorChange,
    } = useFacetedFilters({
        selectedSpecies: selectedSpecies ?? [],
        selectedGenomes,
        extraIsolates,
        searchQuery: isProcessingSuggestion ? currentLocusTag : debouncedSearchQuery,
    });

    useEffect(() => {
        const hasFacetGroups = Object.entries(facets || {}).some(
            ([key, values]) =>
                key !== 'total_hits' &&
                key !== 'operators' &&
                Array.isArray(values) &&
                values.length > 0
        );

        if (isInitialFacetPhaseRef.current) {
            setLoading(facetsLoading);
            if (hasFacetGroups && !facetsLoading) {
                isInitialFacetPhaseRef.current = false;
            }
        }
    }, [facets, facetsLoading, setLoading]);

    const getLegacyFilters = useCallback(
        () => convertFacetedFiltersToLegacy(facetedFilters),
        [facetedFilters]
    );
    const getLegacyOperators = useCallback(
        () => convertFacetOperatorsToLegacy(facetOperators),
        [facetOperators]
    );

    const publishResults = useCallback(
        (responseData: GeneMeta[] | undefined, pagination: any | null | undefined) => {
            if (responseData && pagination) {
                if (onResultsUpdate) {
                    onResultsUpdate(responseData, pagination);
                } else {
                    setResults(responseData);
                    setCurrentPage(pagination.page_number);
                    setTotalPages(pagination.num_pages);
                    setHasPrevious(pagination.has_previous);
                    setHasNext(pagination.has_next);
                }
                return;
            }
            if (onResultsUpdate) {
                onResultsUpdate([], null);
            } else {
                setResults([]);
                setCurrentPage(1);
                setTotalPages(1);
                setHasPrevious(false);
                setHasNext(false);
            }
        },
        [onResultsUpdate]
    );

    const fetchSearchResults = useCallback(
        async (
            page = 1,
            nextSortField: string,
            nextSortOrder: string,
            selectedFacetFilters: Record<string, string[]>,
            nextFacetOperators?: Record<string, 'AND' | 'OR'>
        ) => {
            const genomeFilter = genomesForQuery(selectedGenomes, extraIsolates);
            const speciesFilter = selectedSpecies;
            const requestId = ++searchRequestIdRef.current;
            try {
                setLoading(true);
                const params = GeneService.buildParamsFetchGeneSearchResults(
                    query,
                    page,
                    pageSize,
                    nextSortField,
                    nextSortOrder,
                    genomeFilter,
                    speciesFilter,
                    selectedFacetFilters
                );
                setApiRequestDetails({
                    url: API_GENE_SEARCH_ADVANCED,
                    method: 'GET',
                    headers: {'Content-Type': 'application/json'},
                    params: Object.fromEntries(params.entries()),
                });

                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    query,
                    page,
                    pageSize,
                    nextSortField,
                    nextSortOrder,
                    genomeFilter,
                    speciesFilter,
                    selectedFacetFilters,
                    nextFacetOperators,
                    undefined
                );
                if (requestId !== searchRequestIdRef.current) {
                    return;
                }
                publishResults(response?.data, response?.pagination);
            } catch (error) {
                console.error('Error fetching data:', error);
                if (requestId !== searchRequestIdRef.current) {
                    return;
                }
                publishResults(undefined, null);
            } finally {
                if (requestId === searchRequestIdRef.current) {
                    setLoading(false);
                }
            }
        },
        [
            query,
            selectedGenomes,
            extraIsolates,
            selectedSpecies,
            pageSize,
            setLoading,
            publishResults,
        ]
    );

    useEffect(() => {
        if (
            pageSize !== lastPageSizeRef.current &&
            (query || selectedGenomes.length > 0 || (selectedSpecies && selectedSpecies.length > 0))
        ) {
            lastPageSizeRef.current = pageSize;
            fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [pageSize, sortField, sortOrder, query, selectedGenomes.length, selectedSpecies]);

    const debouncedFetchSuggestions = useCallback(
        debounce((input: string) => {
            if (!isProcessingSuggestion && input.length >= 2) {
                GeneService.fetchGeneAutocompleteSuggestions(
                    input,
                    10,
                    selectedSpecies?.join(','),
                    genomesForQuery(selectedGenomes, extraIsolates)
                        ?.map((g) => g.isolate_name)
                        .join(',') || '',
                    getLegacyFilters()
                )
                    .then(setSuggestions)
                    .catch(console.error);
            } else {
                setSuggestions([]);
            }
        }, 300),
        [selectedSpecies, selectedGenomes, extraIsolates, getLegacyFilters, isProcessingSuggestion]
    );

    const isGeneViewerPage = useMemo(
        () => selectedGenomes.length > 0 && (selectedSpecies?.length ?? 0) === 0,
        [selectedSpecies?.length, selectedGenomes.length]
    );

    const filtersAreInitial = useMemo(
        () => Object.keys(facetedFilters).length === 0 && Object.keys(facetOperators).length === 0,
        [facetedFilters, facetOperators]
    );

    useEffect(() => {
        if (isGeneViewerPage && filtersAreInitial) {
            const genomeId = selectedGenomes[0]?.isolate_name || null;
            if (genomeId !== lastGenomeRef.current) {
                lastGenomeRef.current = genomeId;
                hasLoadedInitialData.current = false;
            }
            if (selectedGenomes.length > 0 && !hasLoadedInitialData.current) {
                hasLoadedInitialData.current = true;
                const timeoutId = setTimeout(() => {
                    fetchSearchResults(
                        1,
                        sortField,
                        sortOrder,
                        getLegacyFilters(),
                        getLegacyOperators()
                    );
                }, 0);
                return () => clearTimeout(timeoutId);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedGenomes, selectedSpecies, isGeneViewerPage, filtersAreInitial]);

    useEffect(() => {
        if (!filtersAreInitial) {
            const timeoutId = setTimeout(() => {
                fetchSearchResults(
                    1,
                    sortField,
                    sortOrder,
                    getLegacyFilters(),
                    getLegacyOperators()
                );
            }, 0);
            return () => clearTimeout(timeoutId);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [facetedFilters, facetOperators, filtersAreInitial]);

    useEffect(() => {
        if (onResultsUpdate) {
            return;
        }
        const effectiveResults = resultsProp && resultsProp.length > 0 ? resultsProp : results;
        if (effectiveResults.length > 0) {
            const timeoutId = setTimeout(() => {
                fetchSearchResults(
                    1,
                    sortField,
                    sortOrder,
                    getLegacyFilters(),
                    getLegacyOperators()
                );
            }, 0);
            return () => clearTimeout(timeoutId);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sortField, sortOrder, results.length, resultsProp, onResultsUpdate]);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newInput = event.target.value;
        const looksLikeDisplayText =
            newInput.includes('(') && newInput.includes(')') && newInput.includes(' - ');

        setSearchInput(newInput);

        if (isProcessingSuggestion || looksLikeDisplayText) {
            return;
        }
        if (newInput.trim() === '') {
            setSuggestions([]);
            return;
        }
        debouncedFetchSuggestions(newInput);
    };

    const handleClearSearch = useCallback(() => {
        ignoreStoreSyncRef.current = true;
        setSearchInput('');
        setQuery('');
        setDebouncedSearchQuery('');
        setCurrentLocusTag('');
        setSuggestions([]);
        setIsProcessingSuggestion(false);
        setGeneSearchQuery('');
        window.setTimeout(() => {
            ignoreStoreSyncRef.current = false;
        }, 0);

        const genomeFilter = genomesForQuery(selectedGenomes, extraIsolates);
        const speciesFilter = selectedSpecies;

        const reloadAll = async () => {
            const requestId = ++searchRequestIdRef.current;
            try {
                setLoading(true);
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    '',
                    1,
                    pageSize,
                    sortField,
                    sortOrder,
                    genomeFilter,
                    speciesFilter,
                    getLegacyFilters(),
                    getLegacyOperators(),
                    undefined
                );
                if (requestId !== searchRequestIdRef.current) {
                    return;
                }
                publishResults(response?.data, response?.pagination);
            } catch (error) {
                console.error('Error clearing gene search:', error);
            } finally {
                if (requestId === searchRequestIdRef.current) {
                    setLoading(false);
                }
            }
        };

        void reloadAll();
    }, [
        selectedGenomes,
        extraIsolates,
        selectedSpecies,
        pageSize,
        sortField,
        sortOrder,
        getLegacyFilters,
        getLegacyOperators,
        setGeneSearchQuery,
        setLoading,
        publishResults,
    ]);

    const handleClearAllFacets = useCallback(() => {
        clearFacetedFilters();
        setTimeout(() => {
            fetchSearchResults(1, sortField, sortOrder, {}, {});
        }, 0);
    }, [clearFacetedFilters, fetchSearchResults, sortField, sortOrder]);

    const activeSearchLabel = useMemo(() => query.trim(), [query]);

    const hasActiveFacets = useMemo(
        () =>
            Object.values(facetedFilters).some(
                (values) => Array.isArray(values) && values.length > 0
            ),
        [facetedFilters]
    );

    const handleSuggestionClick = (suggestion: GeneSuggestion) => {
        const selectedValue = suggestion.locus_tag;
        const displayValue = suggestion.gene_name
            ? `${suggestion.gene_name} (${suggestion.locus_tag})`
            : suggestion.locus_tag;

        ignoreStoreSyncRef.current = true;
        setIsProcessingSuggestion(true);
        setCurrentLocusTag(selectedValue);
        setQuery(selectedValue);
        setDebouncedSearchQuery(selectedValue);
        setSearchInput(displayValue);
        setSuggestions([]);

        const searchWithLocusTag = async () => {
            const requestId = ++searchRequestIdRef.current;
            const genomeFilter = genomesForQuery(selectedGenomes, extraIsolates);
            const speciesFilter = selectedSpecies;
            try {
                setGeneSearchQuery(selectedValue);
                setLoading(true);
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    '',
                    1,
                    pageSize,
                    sortField,
                    sortOrder,
                    genomeFilter,
                    speciesFilter,
                    getLegacyFilters(),
                    getLegacyOperators(),
                    selectedValue
                );
                if (requestId !== searchRequestIdRef.current) {
                    return;
                }
                publishResults(response?.data, response?.pagination);
            } catch (error) {
                console.error('Error fetching data:', error);
                if (requestId !== searchRequestIdRef.current) {
                    return;
                }
                publishResults(undefined, null);
            } finally {
                if (requestId === searchRequestIdRef.current) {
                    setLoading(false);
                    setIsProcessingSuggestion(false);
                    setCurrentLocusTag('');
                    window.setTimeout(() => {
                        ignoreStoreSyncRef.current = false;
                    }, 0);
                }
            }
        };

        window.setTimeout(() => {
            void searchWithLocusTag();
        }, 0);
    };

    const handleSearch = () => {
        const currentSearchInput = searchInput;
        setQuery(currentSearchInput);
        setDebouncedSearchQuery(currentSearchInput);
        setGeneSearchQuery(currentSearchInput);
        setSuggestions([]);

        const searchWithQuery = async () => {
            const requestId = ++searchRequestIdRef.current;
            const genomeFilter = genomesForQuery(selectedGenomes, extraIsolates);
            const speciesFilter = selectedSpecies;
            try {
                setLoading(true);
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    currentSearchInput,
                    1,
                    pageSize,
                    sortField,
                    sortOrder,
                    genomeFilter,
                    speciesFilter,
                    getLegacyFilters(),
                    getLegacyOperators(),
                    undefined
                );
                if (requestId !== searchRequestIdRef.current) {
                    return;
                }
                publishResults(response?.data, response?.pagination);
            } catch (error) {
                console.error('Error fetching data:', error);
                if (requestId !== searchRequestIdRef.current) {
                    return;
                }
                publishResults(undefined, null);
            } finally {
                if (requestId === searchRequestIdRef.current) {
                    setLoading(false);
                }
            }
        };
        void searchWithQuery();
    };

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        handleSearch();
    };

    const handleDownloadTSV = async () => {
        try {
            setIsDownloading(true);
            alert('Starting download... This may take a while for large datasets.');
            await GeneService.downloadGenesTSV(
                query,
                sortField,
                sortOrder,
                genomesForQuery(selectedGenomes, extraIsolates),
                selectedSpecies,
                getLegacyFilters(),
                getLegacyOperators()
            );
        } catch (error) {
            console.error('Error downloading TSV:', error);
            alert(
                'Failed to download TSV file. Please try again or contact support if the problem persists.'
            );
        } finally {
            setIsDownloading(false);
        }
    };

    const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newSize = parseInt(event.target.value, 10);
        setPageSize(newSize);
        onPageSizeChange?.(newSize);
    };

    const handlePageClick = (page: number) => {
        if (onResultsUpdate) {
            const searchWithPage = async () => {
                const requestId = ++searchRequestIdRef.current;
                const genomeFilter = genomesForQuery(selectedGenomes, extraIsolates);
                const speciesFilter = selectedSpecies;
                const locusTag = looksLikeLocusTag(query) ? query.trim() : undefined;
                try {
                    setLoading(true);
                    const response = await GeneService.fetchGeneSearchResultsAdvanced(
                        locusTag ? '' : query,
                        page,
                        pageSize,
                        sortField,
                        sortOrder,
                        genomeFilter,
                        speciesFilter,
                        getLegacyFilters(),
                        getLegacyOperators(),
                        locusTag
                    );
                    if (requestId !== searchRequestIdRef.current) {
                        return;
                    }
                    publishResults(response?.data, response?.pagination);
                } catch (error) {
                    console.error('Error fetching data for pagination:', error);
                    if (requestId === searchRequestIdRef.current) {
                        publishResults(undefined, null);
                    }
                } finally {
                    if (requestId === searchRequestIdRef.current) {
                        setLoading(false);
                    }
                }
            };
            void searchWithPage();
            return;
        }
        if (onPageChange) {
            onPageChange(page);
            return;
        }
        setCurrentPage(page);
        void fetchSearchResults(page, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
    };

    const displayResults = isHomePageMode ? resultsProp || [] : results;
    const displayCurrentPage = isHomePageMode ? currentPageProp || 1 : currentPage;
    const displayTotalPages = isHomePageMode ? totalPagesProp || 1 : totalPages;
    const displayHasPrevious = isHomePageMode ? Boolean(hasPreviousProp) : hasPrevious;
    const displayHasNext = isHomePageMode ? Boolean(hasNextProp) : hasNext;

    return {
        isHomePageMode,
        searchInput,
        suggestions,
        setSuggestions,
        facets,
        handleToggleFacet,
        handleOperatorChange,
        hasActiveFacets,
        handleClearAllFacets,
        activeSearchLabel,
        handleClearSearch,
        handleInputChange,
        handleSuggestionClick,
        handleSearch,
        handleSubmit,
        handleDownloadTSV,
        handlePageSizeChange,
        handlePageClick,
        pageSize,
        isDownloading,
        apiRequestDetails,
        displayResults,
        displayCurrentPage,
        displayTotalPages,
        displayHasPrevious,
        displayHasNext,
        getLegacyFilters,
        getLegacyOperators,
        fetchSearchResults,
    };
}
