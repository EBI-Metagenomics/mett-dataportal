import React, {useCallback, useEffect, useMemo, useState} from 'react';
import GeneSearchInput from './GeneSearchInput';
import styles from "@components/organisms/Gene/GeneSearchForm/GeneSearchForm.module.scss";
import GeneResultsTable from "@components/organisms/Gene/GeneResultsHandler/GeneResultsTable";
import Pagination from "@components/molecules/Pagination";
import {GeneService} from '../../../../services/geneService';
import {createViewState} from '@jbrowse/react-app2';
import {GeneMeta, GeneSuggestion} from "../../../../interfaces/Gene";
import {LinkData} from "../../../../interfaces/Auxiliary";
import {BaseGenome} from "../../../../interfaces/Genome";
import {
    API_GENE_SEARCH_ADVANCED,
    DEFAULT_PER_PAGE_CNT,
    FACET_INITIAL_VISIBLE_CNT,
    FACET_STEP_CNT
} from "../../../../utils/appConstants";
import {copyToClipboard, generateCurlRequest, generateHttpRequest} from "../../../../utils/apiHelpers";
import SelectedGenomes from "@components/Filters/SelectedGenomes";
import GeneFacetedFilter from "@components/Filters/GeneFacetedFilter";
import {useFacetedFilters} from '../../../../hooks/useFacetedFilters';
import {useFilterStore} from '../../../../stores/filterStore';
import {convertFacetedFiltersToLegacy, convertFacetOperatorsToLegacy} from '../../../../utils/filterUtils';

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
                                                       }) => {
    const [searchInput, setSearchInput] = useState<string>('');
    const [query, setQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<GeneSuggestion[]>([]);
    const [geneName, setGeneName] = useState<string>('');
    const [results, setResults] = useState<GeneMeta[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);
    const [pageSize, setPageSize] = useState<number>(DEFAULT_PER_PAGE_CNT);
    const [isDownloading, setIsDownloading] = useState(false);

    const facetedFilters = useFilterStore(state => state.facetedFilters);
    const facetOperators = useFilterStore(state => state.facetOperators);

    // Use the new faceted filters hook
    const {
        facets,
        loading: facetsLoading,
        error: facetsError,
        handleToggleFacet,
        handleOperatorChange,
        refreshFacets
    } = useFacetedFilters({
        selectedSpecies: selectedSpecies || [],
        selectedGenomes,
        searchQuery: query,
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
    };

    // Convert faceted filters to legacy format for API calls
    const getLegacyFilters = useCallback(() => {
        return convertFacetedFiltersToLegacy(facetedFilters);
    }, [facetedFilters]);

    // Convert facet operators to legacy format for API calls
    const getLegacyOperators = useCallback(() => {
        return convertFacetOperatorsToLegacy(facetOperators);
    }, [facetOperators]);

    // Fetch suggestions for autocomplete based on the query and selected species
    const fetchSuggestions = useCallback(
        async (inputQuery: string) => {
            if (inputQuery.length >= 2) {
                try {
                    let response;

                    // If species is selected (used in HomePage.tsx)
                    if (selectedSpecies && selectedSpecies.length === 1) {
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            selectedSpecies[0],
                            undefined,
                            getLegacyFilters()
                        );
                    }
                    // If genome is selected (used in GeneViewerPage.tsx)
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


    // Debounce function to reduce the frequency of API calls
    //todo handle this properly
    // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
    const debounce = (func: Function, delay: number) => {
        let timeoutId: NodeJS.Timeout;
        return (...args: string[]) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };

    const debouncedFetchSuggestions = useCallback(debounce(fetchSuggestions, 300), [fetchSuggestions]);
    const [selectedGeneId, setSelectedGeneId] = useState<string | null>(null);

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
            try {
                setLoading(true); // Start spinner
                let response = null;
                if (selectedGeneId) {
                    // Fetch by gene ID
                    const geneResponseObj = await GeneService.fetchGeneByLocusTag(selectedGeneId);
                    response = {
                        results: [geneResponseObj],
                        page_number: 1,
                        num_pages: 1,
                        has_previous: false,
                        has_next: false,
                    };
                } else {
                    // Fetch results using the advanced search API
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

                    setApiRequestDetails(apiDetails);

                    response = await GeneService.fetchGeneSearchResultsAdvanced(
                        query,
                        page,
                        pageSize,
                        sortField,
                        sortOrder,
                        genomeFilter,
                        speciesFilter,
                        selectedFacetFilters,
                        facetOperators
                    );
                }
                if (response && response.results) {
                    setResults(response.results);
                    setCurrentPage(response.page_number);
                    setTotalPages(response.num_pages);
                    setHasPrevious(response.has_previous);
                    setHasNext(response.has_next);
                } else {
                    setResults([]);
                    setCurrentPage(1);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
                }
            } catch (error) {
                console.error("Error fetching data:", error);
                setResults([]);
                setCurrentPage(1);
                setTotalPages(1);
                setHasPrevious(false);
                setHasNext(false);
            } finally {
                setLoading(false); // Stop spinner
            }
        },
        [query, selectedGeneId, selectedSpecies, selectedGenomes, pageSize, getLegacyFilters, getLegacyOperators]
    );

    // For GeneViewerPage: load initial data when genome changes
    const isGeneViewerPage = React.useMemo(() => (selectedSpecies?.length ?? 0) === 0 && query.length === 0, [selectedSpecies?.length, query.length]);
    const lastGenomeRef = React.useRef<string | null>(null);
    const lastSpeciesRef = React.useRef<string[]>([]);
    const hasLoadedInitialData = React.useRef(false);

    // Helper to check if filters are in their initial state (no user interaction)
    const filtersAreInitial = useMemo(
        () => Object.keys(facetedFilters).length === 0 && Object.keys(facetOperators).length === 0,
        [facetedFilters, facetOperators]
    );

    // Initial load effect: only runs on context change and when filters are initial
    useEffect(() => {
        if (isGeneViewerPage && filtersAreInitial) {
            const genomeId = selectedGenomes[0]?.isolate_name || null;
            if (genomeId !== lastGenomeRef.current) {
                lastGenomeRef.current = genomeId;
                hasLoadedInitialData.current = false;
            }
            if (selectedGenomes.length > 0 && !hasLoadedInitialData.current) {
                hasLoadedInitialData.current = true;
                fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
            }
        } else if (!isGeneViewerPage && selectedSpecies && selectedSpecies.length > 0 && selectedGenomes.length === 0 && filtersAreInitial) {
            const speciesKey = selectedSpecies.join(',');
            if (speciesKey !== lastSpeciesRef.current.join(',')) {
                lastSpeciesRef.current = selectedSpecies;
                hasLoadedInitialData.current = false;
            }
            if (!hasLoadedInitialData.current) {
                hasLoadedInitialData.current = true;
                fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
            }
        }
    }, [selectedGenomes, selectedSpecies, isGeneViewerPage, filtersAreInitial, fetchSearchResults, sortField, sortOrder, getLegacyFilters, getLegacyOperators]);

    // User interaction effect: runs only on user-driven changes
    useEffect(() => {
        if (!filtersAreInitial || query.length > 0) {
            fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
        }
    }, [facetedFilters, facetOperators, query, fetchSearchResults, sortField, sortOrder, getLegacyFilters, getLegacyOperators]);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newInput = event.target.value;
        setSearchInput(newInput);
        setQuery(newInput);
        setGeneName('');
        setSelectedGeneId(null);
        debouncedFetchSuggestions(newInput);
    };

    const handleSuggestionClick = (suggestion: GeneSuggestion) => {
        setQuery(suggestion.gene_name || suggestion.locus_tag);
        setGeneName(suggestion.gene_name);
        setSelectedGeneId(suggestion.locus_tag);
        setSuggestions([]);
        fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setQuery(searchInput);
        fetchSearchResults(1, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
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
            // Show success message
            alert('Download completed successfully!');
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
                        query={query}
                        onInputChange={handleInputChange}
                        suggestions={suggestions}
                        onSuggestionClick={handleSuggestionClick}
                        onSuggestionsClear={() => setSuggestions([])}
                    /></form>
                <div>
                    <p>&nbsp;</p>
                </div>
                <div className="vf-grid__col--span-3" id="results-table"
                     style={{display: results.length > 0 ? 'block' : 'none'}}>
                    <GeneResultsTable
                        results={results}
                        onSortClick={onSortClick}
                        linkData={linkData}
                        viewState={viewState}
                        setLoading={setLoading}
                        isTypeStrainAvailable={selectedGenomes.length ? selectedGenomes.some(genome => genome.type_strain) : true}
                        onDownloadTSV={handleDownloadTSV}
                        isLoading={isDownloading}
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
                            {totalPages > 1 && (
                                <Pagination
                                    currentPage={currentPage}
                                    totalPages={totalPages}
                                    hasPrevious={hasPrevious}
                                    hasNext={hasNext}
                                    onPageClick={(page) => {
                                        setCurrentPage(page);
                                        fetchSearchResults(page, sortField, sortOrder, getLegacyFilters(), getLegacyOperators());
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
