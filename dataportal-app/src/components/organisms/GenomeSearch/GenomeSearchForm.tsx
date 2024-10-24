import React, {useCallback, useEffect, useState} from 'react';
import Pagination from "../../molecules/Pagination";
import GenomeSearchInput from "@components/organisms/GenomeSearch/GenomeSearchInput";
import GenomeResultsTable from "@components/organisms/GenomeSearch/GenomeResultsTable";
import styles from "@components/organisms/GenomeSearch/GenomeSearchForm.module.scss";
import {
    fetchGenomeAutocompleteSuggestions,
    fetchGenomeByStrainId,
    fetchGenomeSearchResults
} from "../../../services/genomeService";

interface SearchGenomeFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
    selectedSpecies: number [];
    results: any[];
    onSortClick: (sortField: string) => void;
    selectedGenomes: { id: number; name: string }[];
    onToggleGenomeSelect: (genome: { id: number; name: string }) => void;
    onGenomeSelect: (genome: { id: number; name: string }) => void;
    totalPages: number;
    currentPage: number;
    handlePageClick: (page: number) => void;
}

const GenomeSearchForm: React.FC<SearchGenomeFormProps> = ({
                                                               selectedSpecies,
                                                               selectedGenomes,
                                                               onToggleGenomeSelect,
                                                               onGenomeSelect,
                                                               onSortClick
                                                           }) => {
    const [query, setQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<{
        strain_id: number,
        isolate_name: string,
        assembly_name: string
    }[]>([]);
    const [isolateName, setIsolateName] = useState<string>('');
    const [results, setResults] = useState<any[]>([]);
    const [currentSortField, setCurrentSortField] = useState<string>('');
    const [currentSortOrder, setCurrentSortOrder] = useState<string>('');
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);

    const [pageSize, setPageSize] = useState<number>(10);
    const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newSize = parseInt(event.target.value, 10);
        setPageSize(newSize);
    };

    useEffect(() => {
        fetchSearchResults(1);
    }, [pageSize]);

    // Fetch suggestions for autocomplete based on the query and selected species
    const fetchSuggestions = useCallback(
        async (inputQuery: string) => {
            if (inputQuery.length >= 2) {
                try {
                    const response = await fetchGenomeAutocompleteSuggestions(inputQuery, selectedSpecies.join(','));

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


    // Fetch search results based on the query, selected species, page, sort field, and sort order
    const fetchSearchResults = useCallback(
        async (page: number = 1, sortField: string = currentSortField, sortOrder: string = currentSortOrder) => {
            if (selectedStrainId) {
                try {
                    const response = await fetchGenomeByStrainId(selectedStrainId);
                    console.log("response: " + response)
                    if (response) {
                        setResults([response]);
                        setCurrentPage(1);
                        setTotalPages(1);
                        setHasPrevious(false);
                        setHasNext(false);
                    } else {
                        setResults([]);
                        setCurrentPage(1);
                        setTotalPages(1);
                        setHasPrevious(false);
                        setHasNext(false);
                    }
                } catch (error) {
                    console.error('Error fetching data:', error);
                    setResults([]);
                    setCurrentPage(1);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
                }
            } else {
                const isolate = isolateName.trim() || query.trim();
                if (isolate) {
                    const queryString = new URLSearchParams({
                        'query': isolate,
                        'page': String(page),
                        'per_page': String(pageSize),
                        'sortField': sortField,
                        'sortOrder': sortOrder
                    }).toString();

                    try {
                        const response = await fetchGenomeSearchResults(isolate, page, pageSize, sortField, sortOrder, selectedSpecies);


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
                        console.error('Error fetching data:', error);
                        setResults([]);
                        setCurrentPage(1);
                        setTotalPages(1);
                        setHasPrevious(false);
                        setHasNext(false);
                    }
                }

            }
        },
        [selectedStrainId, isolateName, query, selectedSpecies, currentSortField, currentSortOrder, pageSize]
    );


    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newQuery = event.target.value;
        setQuery(newQuery);
        setIsolateName('');
        setSelectedStrainId(null);
        debouncedFetchSuggestions(newQuery);
    };

    const handleSuggestionClick = (suggestion: { strain_id: number, isolate_name: string, assembly_name: string }) => {
        console.log('suggestion: ' + suggestion)
        console.log('isolateName: ' + isolateName)
        console.log('suggestion.strain_id: ' + suggestion.strain_id)
        setQuery(suggestion.isolate_name);
        setIsolateName(suggestion.isolate_name);
        setSelectedStrainId(suggestion.strain_id);
        setSuggestions([]);
        onGenomeSelect({id: suggestion.strain_id, name: suggestion.isolate_name});
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        console.log('selectedStrainId:' + selectedStrainId)
        event.preventDefault();
        fetchSearchResults();
    };

    const handleSortClick = (sortField: string) => {
        const newSortOrder = currentSortField === sortField ? (currentSortOrder === 'asc' ? 'desc' : 'asc') : 'asc';
        setCurrentSortField(sortField);
        setCurrentSortOrder(newSortOrder);
        fetchSearchResults(1, sortField, newSortOrder);
    };

    const handlePageClick = (page: number) => {
        setCurrentPage(page);
        fetchSearchResults(page);
    };

    return (
        <section id="vf-tabs__section--2">
            <div>
                <p/>
            </div>
            <div className={`vf-grid__col--span-3 ${styles.vfGenomeSection}`}>
                <form onSubmit={handleSubmit}
                      className="vf-form vf-form--search vf-form--search--responsive | vf-sidebar vf-sidebar--end">
                    <h2 className={`vf-section-header__subheading ${styles.vfGenomeSubHeading}`}>Search Genome</h2>
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
                        />
                        {/* Page size dropdown and pagination */}
                        <div className={styles.paginationContainer}>
                            <div className={styles.pageSizeDropdown}>
                                <label htmlFor="pageSize">Page Size: </label>
                                <select id="pageSize" value={pageSize} onChange={handlePageSizeChange}>
                                    <option value={10}>Show 10</option>
                                    <option value={20}>Show 20</option>
                                    <option value={50}>Show 50</option>
                                </select>
                            </div>

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
                </form>
            </div>
            <div>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
            </div>
        </section>
    );
};

export default GenomeSearchForm;
