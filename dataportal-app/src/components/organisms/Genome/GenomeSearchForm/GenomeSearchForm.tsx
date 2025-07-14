import React, {useCallback, useEffect, useState} from 'react';
import Pagination from "../../../molecules/Pagination";
import GenomeSearchInput from "@components/organisms/Genome/GenomeSearchForm/GenomeSearchInput";
import GenomeResultsTable from "@components/organisms/Genome/GenomeResultsHandler/GenomeResultsTable";
import styles from "@components/organisms/Genome/GenomeSearchForm/GenomeSearchForm.module.scss";
import {GenomeService} from "../../../../services/genomeService";
import {LinkData} from "../../../../interfaces/Auxiliary";
import {AutocompleteResponse, BaseGenome, GenomeMeta} from "../../../../interfaces/Genome";
import {DEFAULT_PER_PAGE_CNT} from "../../../../utils/appConstants";
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
    linkData: LinkData;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const GenomeSearchForm: React.FC<SearchGenomeFormProps> = ({
                                                               searchQuery,
                                                               onSearchQueryChange,
                                                               onSearchSubmit,
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
    const [isDownloading, setIsDownloading] = useState(false);

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


    // Fetch search results
    const fetchSearchResults = useCallback(
        async (
            page: number = 1,
            sortField: string = "isolate_name",
            sortOrder: string = "asc"
        ) => {
            setLoading(true); // Show spinner
            const startTime = Date.now();

            const qry = isolateName.trim() || searchQuery.trim();
            const speciesFilter = selectedSpecies.length ? selectedSpecies : [];
            const typeStrainFilter = selectedTypeStrains.length ? selectedTypeStrains : [];

            try {
                const apiDetails = {
                    url: '',
                    method: 'GET',
                    headers: {'Content-Type': 'application/json'},
                    params: {},
                };

                const params = new URLSearchParams({
                    query: qry,
                    page: String(page),
                    per_page: String(pageSize),
                    sortField,
                    sortOrder,
                });

                if (typeStrainFilter && typeStrainFilter.length) {
                    params.append('isolates', typeStrainFilter.join(','));
                }

                const endpoint = (selectedSpecies && selectedSpecies.length === 1)
                ? `/species/${selectedSpecies[0]}/genomes/search`
                : `/genomes/search`;

                apiDetails.url = endpoint;
                apiDetails.params = Object.fromEntries(params.entries());

                const response = await GenomeService.fetchGenomeSearchResults(
                    qry,
                    page,
                    pageSize,
                    sortField,
                    sortOrder,
                    speciesFilter,
                    typeStrainFilter
                );

                console.log('GenomeSearchForm response received:', response);
                console.log('GenomeSearchForm response.data:', response?.data);
                console.log('GenomeSearchForm response.pagination:', response?.pagination);
                if (response && response.data && response.pagination) {
                    console.log('GenomeSearchForm: Setting results with', response.data.length, 'items');
                    setResults(response.data);
                    setTotalPages(response.pagination.num_pages);
                    setHasPrevious(response.pagination.has_previous ?? page > 1);
                    setHasNext(response.pagination.has_next);
                } else {
                    console.log('GenomeSearchForm: No valid response, setting empty results');
                    setResults([]);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
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
        [searchQuery, isolateName, selectedSpecies, selectedTypeStrains, pageSize]
    );


    useEffect(() => {
        setCurrentPage(1);
        fetchSearchResults(1, sortField, sortOrder);
    }, [selectedSpecies, selectedTypeStrains, sortField, sortOrder, pageSize]);


    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newQuery = event.target.value;
        onSearchQueryChange(event);
        setIsolateName('');
        debouncedFetchSuggestions(newQuery);
    };

    const handleSuggestionClick = (suggestion: AutocompleteResponse) => {
        console.log('suggestion: ' + suggestion)
        console.log('isolateName: ' + suggestion.isolate_name)
        // console.log('suggestion.strain_id: ' + suggestion.id)
        onSearchQueryChange({
            target: { value: suggestion.isolate_name }
        } as React.ChangeEvent<HTMLInputElement>);
        setIsolateName(suggestion.isolate_name);
        setSuggestions([]);
        // fixed for query based on user selection
        fetchSearchResults(1, sortField, sortOrder);
        // EMG-7006 - no auto selection of filters
        //onGenomeSelect({id: suggestion.strain_id, name: suggestion.isolate_name});
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        onSearchSubmit('genome');
        fetchSearchResults(1, sortField, sortOrder);
    };

    const handlePageClick = (page: number) => {
        if (page < 1 || page > totalPages) return;
        setCurrentPage(page);
        fetchSearchResults(page, sortField, sortOrder);
    };

    const handleDownloadTSV = async () => {
        try {
            setIsDownloading(true);
            // Show initial message for large downloads
            alert('Starting download... This may take a while for large datasets.');
            
            await GenomeService.downloadGenomesTSV(
                searchQuery,
                sortField,
                sortOrder,
                selectedSpecies,
                selectedTypeStrains
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
        <section id="genomes">
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
                            query={searchQuery}
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
