import React, {useCallback, useEffect, useState} from 'react';
import GeneSearchInput from './GeneSearchInput';
import styles from "@components/organisms/GeneSearch/GeneSearchForm/GeneSearchForm.module.scss";
import GeneResultsTable from "@components/organisms/GeneSearch/GeneResultsHandler/GeneResultsTable";
import Pagination from "@components/molecules/Pagination";
import {GeneService} from '../../../../services/geneService';
import {createViewState} from '@jbrowse/react-app';
import {GeneEssentialityTag, GeneFacetResponse, GeneMeta, GeneSuggestion} from "../../../../interfaces/Gene";
import {FacetItem, LinkData} from "../../../../interfaces/Auxiliary";
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
    essentialityFilter: string[];
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
                                                           essentialityFilter,
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
    const [selectedFacets, setSelectedFacets] = useState<Record<string, string[]>>({});


    const [facets, setFacets] = useState<GeneFacetResponse>({});


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
                            essentialityFilter
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
                            essentialityFilter
                        );
                    } else {
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            undefined,
                            undefined,
                            essentialityFilter
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
        [selectedSpecies, selectedGenomes, essentialityFilter]
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
            selectedFacetFilters: Record<string, string[]>
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
                        selectedFacetFilters
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
        [query, selectedGeneId, selectedSpecies, selectedGenomes, pageSize]
    );


    useEffect(() => {
        fetchSearchResults(1, sortField, sortOrder, selectedFacets);

        const loadFacets = async () => {
            try {
                const speciesAcronym = selectedSpecies?.[0];
                const isolates = selectedGenomes.map(genome => genome.isolate_name).join(',');
                const response = await GeneService.fetchGeneFacets(
                    speciesAcronym,
                    isolates,
                    selectedFacets.essentiality?.join(','),
                    selectedFacets.cog_id?.join(','),
                    selectedFacets.kegg?.join(','),
                    selectedFacets.go_term?.join(','),
                    selectedFacets.pfam?.join(','),
                    selectedFacets.interpro?.join(',')
                );

                // selected state
                const updatedFacets: GeneFacetResponse = {};
                for (const [facetGroup, items] of Object.entries(response)) {
                    if (!Array.isArray(items)) continue;

                    const selectedValues = selectedFacets[facetGroup] || [];

                    // Map response values and mark selected
                    const responseMap = new Map(items.map(item => [item.value, {
                        ...item,
                        selected: selectedValues.includes(item.value),
                    }]));

                    // Inject selected values not present in API response
                    selectedValues.forEach(sel => {
                        if (!responseMap.has(sel)) {
                            responseMap.set(sel, {
                                value: sel,
                                count: 0,
                                selected: true
                            });
                        }
                    });

                    updatedFacets[facetGroup] = Array.from(responseMap.values());
                }
                setFacets(updatedFacets);
            } catch (e) {
                console.error('Error loading facets', e);
            }
        };

        loadFacets();
    }, [selectedSpecies, selectedGenomes, sortField, sortOrder, pageSize, selectedFacets]);


    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newInput = event.target.value;
        setSearchInput(newInput);
        setQuery(newInput);
        setGeneName('');
        setSelectedGeneId(null);
        debouncedFetchSuggestions(newInput);
    };

    const handleSuggestionClick = (suggestion: GeneSuggestion) => {
        // console.log('suggestion: ' + suggestion)
        // console.log('strain name: ' + suggestion.isolate_name)
        // console.log('suggestion.gene_name: ' + suggestion.gene_name)
        // console.log('suggestion.locus_tag: ' + suggestion.locus_tag)
        setQuery(suggestion.gene_name || suggestion.locus_tag + '(' + suggestion.isolate_name + ')');
        setGeneName(suggestion.gene_name);
        setSelectedGeneId(suggestion.locus_tag);
        setSuggestions([]);
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        // console.log('selectedGeneId:' + selectedGeneId)
        event.preventDefault();
        setQuery(searchInput);
        fetchSearchResults(1, sortField, sortOrder, selectedFacets);
    };

    const handleToggleFacet = (group: string, value: string) => {
        const updated = {...facets};
        const groupValues = updated[group] as FacetItem[];

        updated[group] = groupValues.map(item =>
            item.value === value ? {...item, selected: !item.selected} : item
        );

        setFacets(updated);

        // Extract selected facet values by group
        const newSelected: Record<string, string[]> = {};
        for (const [key, val] of Object.entries(updated)) {
            if (Array.isArray(val)) {
                const selectedVals = val.filter(v => v.selected).map(v => v.value);
                if (selectedVals.length) newSelected[key] = selectedVals;
            }
        }

        setSelectedFacets(newSelected);

        fetchSearchResults(1, sortField, sortOrder, newSelected);
    };


    const handlePageClick = (page: number) => {
        setCurrentPage(page);
        fetchSearchResults(page, sortField, sortOrder, selectedFacets);
    };

    return (
        <section id="vf-tabs__section--2">
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
                                    onPageClick={handlePageClick}
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
