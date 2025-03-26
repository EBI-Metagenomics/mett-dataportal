import React, {useCallback, useEffect, useState} from 'react';
import Pagination from "../../../molecules/Pagination";
import GenomeSearchInput from "@components/organisms/GenomeSearch/GenomeSearchForm/GenomeSearchInput";
import GenomeResultsTable from "@components/organisms/GenomeSearch/GenomeResultsHandler/GenomeResultsTable";
import styles from "@components/organisms/GenomeSearch/GenomeSearchForm/GenomeSearchForm.module.scss";
import {GenomeService} from "../../../../services/genomeService";
import {LinkData} from "../../../../interfaces/Auxiliary";
import {AutocompleteResponse, BaseGenome, GenomeMeta} from "../../../../interfaces/Genome";
import {
    API_GENOME_SEARCH,
    API_GENOMES_BY_ISOLATE_NAMES,
    DEFAULT_PER_PAGE_CNT,
    getAPIUrlGenomeSearchWithSpecies
} from "../../../../utils/appConstants";
import {copyToClipboard, generateCurlRequest, generateHttpRequest} from "../../../../utils/apiHelpers";
import TypeStrainsFilter from "@components/Filters/TypeStrainsFilter";
import SelectedGenomes from "@components/Filters/SelectedGenomes";

interface SearchGenomeFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: (field: string) => void;
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    selectedSpecies: string [];
    selectedTypeStrains: string[];
    results: any[];
    sortField: string,
    sortOrder: 'asc' | 'desc';
    selectedGenomes: BaseGenome[];
    typeStrains: GenomeMeta[];
    onToggleGenomeSelect: (genome: BaseGenome) => void;
    handleRemoveGenome: (genomeId: string) => void;
    handleTypeStrainToggle: (isolate_name: string) => void;
    // onGenomeSelect: (genome: { id: number; name: string }) => void;
    linkData: LinkData;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const GenomeSearchForm: React.FC<SearchGenomeFormProps> = ({
                                                               selectedSpecies,
                                                               selectedTypeStrains,
                                                               selectedGenomes,
                                                               typeStrains,
                                                               onToggleGenomeSelect,
                                                               handleTypeStrainToggle,
                                                               handleRemoveGenome,
                                                               // onGenomeSelect,
                                                               onSortClick,
                                                               sortField,
                                                               sortOrder,
                                                               linkData,
                                                               setLoading,
                                                           }) => {
    const [query, setQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<AutocompleteResponse[]>([]);
    const [isolateName, setIsolateName] = useState<string>('');
    const [results, setResults] = useState<any[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);
    const [pageSize, setPageSize] = useState<number>(DEFAULT_PER_PAGE_CNT);

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
                    const response = await GenomeService.fetchGenomeAutocompleteSuggestions(inputQuery, selectedSpecies.join(','));

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
        [selectedSpecies]
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
    const [selectedStrainId, setSelectedStrainId] = useState<number | null>(null);


    // Fetch search results
    const fetchSearchResults = useCallback(
        async (
            page: number = 1,
            sortField: string = "isolate_name",
            sortOrder: string = "asc"
        ) => {
            setLoading(true); // Show spinner
            const startTime = Date.now();

            const qry = isolateName.trim() || query.trim();
            const speciesFilter = selectedSpecies.length ? selectedSpecies : [];
            const typeStrainFilter = selectedTypeStrains.length ? selectedTypeStrains : null;

            try {
                let response;
                const apiDetails = {
                    url: '',
                    method: 'GET',
                    headers: {'Content-Type': 'application/json'},
                    params: {},
                };

                if (typeStrainFilter) {
                    // Fetch by strain IDs
                    apiDetails.url = API_GENOMES_BY_ISOLATE_NAMES;
                    apiDetails.params = {ids: typeStrainFilter.join(",")};

                    response = await GenomeService.fetchGenomeByIsolateNames(typeStrainFilter);
                    setResults(response);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
                } else {
                    // Standard genome search
                    const params = new URLSearchParams({
                        query: qry,
                        page: String(page),
                        per_page: String(pageSize),
                        sortField,
                        sortOrder,
                    });

                    const endpoint =
                        speciesFilter.length === 1
                            ? getAPIUrlGenomeSearchWithSpecies(speciesFilter[0])
                            : API_GENOME_SEARCH;

                    apiDetails.url = endpoint;
                    apiDetails.params = Object.fromEntries(params.entries());

                    response = await GenomeService.fetchGenomeSearchResults(
                        qry,
                        page,
                        pageSize,
                        sortField,
                        sortOrder,
                        speciesFilter
                    );

                    if (response && response.results) {
                        setResults(response.results);
                        setTotalPages(response.num_pages);
                        setHasPrevious(response.has_previous ?? page > 1);
                        setHasNext(response.has_next);
                    } else {
                        setResults([]);
                        setTotalPages(1);
                        setHasPrevious(false);
                        setHasNext(false);
                    }
                }
                // console.log('apiRequestDetails', apiDetails)
                setApiRequestDetails(apiDetails);
            } catch (error) {
                console.error("Error fetching data:", error);
                setResults([]);
                setTotalPages(1);
                setHasPrevious(false);
                setHasNext(false);
            } finally {
                const elapsedTime = Date.now() - startTime;
                const remainingTime = 500 - elapsedTime;
                setTimeout(() => setLoading(false), remainingTime > 0 ? remainingTime : 0);
            }
        },
        [query, isolateName, selectedSpecies, selectedTypeStrains, pageSize]
    );


    useEffect(() => {
        setCurrentPage(1);
        fetchSearchResults(1, sortField, sortOrder);
    }, [selectedSpecies, selectedTypeStrains, sortField, sortOrder, pageSize]);


    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newQuery = event.target.value;
        setQuery(newQuery);
        setIsolateName('');
        setSelectedStrainId(null);
        debouncedFetchSuggestions(newQuery);
    };

    const handleSuggestionClick = (suggestion: AutocompleteResponse) => {
        // console.log('suggestion: ' + suggestion)
        // console.log('isolateName: ' + isolateName)
        // console.log('suggestion.strain_id: ' + suggestion.id)
        setQuery(suggestion.isolate_name);
        setIsolateName(suggestion.isolate_name);
        setSuggestions([]);
        // EMG-7006 - no auto selection of filters
        //onGenomeSelect({id: suggestion.strain_id, name: suggestion.isolate_name});
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        // console.log('selectedStrainId:' + selectedStrainId)
        event.preventDefault();
        fetchSearchResults(1, sortField, sortOrder);
    };

    const handlePageClick = (page: number) => {
        if (page < 1 || page > totalPages) return;
        setCurrentPage(page);
        fetchSearchResults(page, sortField, sortOrder);
    };

    return (
        <section id="vf-tabs__section--2">
            <div>
                <p/>
            </div>
            <div className={styles.leftPane}>

                {/* Type Strains Filter */}
                <TypeStrainsFilter
                    typeStrains={typeStrains}
                    selectedTypeStrains={selectedTypeStrains}
                    selectedSpecies={selectedSpecies}
                    onTypeStrainToggle={handleTypeStrainToggle}
                />

                <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome}/>
            </div>
            <div className={styles.rightPane}>
                <div className={`vf-grid__col--span-3 ${styles.vfGenomeSection}`}>
                    <form onSubmit={handleSubmit}
                          className="vf-form vf-form--search vf-form--search--responsive | vf-sidebar vf-sidebar--end">
                        <h2 className={`vf-section-header__subheading ${styles.vfGenomeSubHeading}`}>Genome Search</h2>
                        <div>
                            <p/>
                        </div>
                        <GenomeSearchInput
                            query={query}
                            onInputChange={handleInputChange}
                            suggestions={suggestions}
                            onSuggestionClick={handleSuggestionClick}
                            onSuggestionsClear={() => setSuggestions([])}
                        />

                    </form>
                    <div>
                        <p>&nbsp;</p>
                    </div>
                    <div className="vf-grid__col--span-3" id="results-table"
                         style={{display: results.length > 0 ? 'block' : 'none'}}>
                        <GenomeResultsTable
                            results={results}
                            onSortClick={onSortClick}
                            selectedGenomes={selectedGenomes}
                            onToggleGenomeSelect={onToggleGenomeSelect}
                            linkData={linkData}
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
                                )}</div>
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

                </div>
                <div>
                    <p>&nbsp;</p>
                    <p>&nbsp;</p>
                    <p>&nbsp;</p>
                </div>
            </div>
        </section>
    );
};

export default GenomeSearchForm;
