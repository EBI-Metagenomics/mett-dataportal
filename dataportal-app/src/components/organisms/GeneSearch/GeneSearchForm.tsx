import React, {useCallback, useEffect, useState} from 'react';
import GeneSearchInput from './GeneSearchInput';
import styles from "@components/organisms/GeneSearch/GeneSearchForm.module.scss";
import GeneResultsTable from "@components/organisms/GeneSearch/GeneResultsTable";
import Pagination from "@components/molecules/Pagination";
import {fetchGeneAutocompleteSuggestions, fetchGeneById, fetchGeneSearchResults} from "../../../services/geneService";
import {createViewState} from '@jbrowse/react-linear-genome-view';

type ViewModel = ReturnType<typeof createViewState>;

interface GeneSearchFormProps {
    searchQuery: string,
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void,
    onSearchSubmit: () => void,
    selectedSpecies?: number [],
    results: any[],
    onSortClick: (sortField: string) => void,
    totalPages: number,
    currentPage: number,
    handlePageClick: (page: number) => void,
    selectedGenomes?: { id: number; name: string }[],
    linkData: {
        template: string;
        alias: string;
    },
    viewState?: ViewModel;
}

const GeneSearchForm: React.FC<GeneSearchFormProps> = ({
                                                           selectedSpecies,
                                                           onSortClick,
                                                           selectedGenomes,
                                                           linkData,
                                                           viewState
                                                       }) => {
    const [query, setQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<{
        gene_id: number,
        strain_name: string,
        gene_name: string
    }[]>([]);
    const [geneName, setGeneName] = useState<string>('');
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
                    let response;

                    // If species is selected (used in HomePage.tsx)
                    if (selectedSpecies && selectedSpecies.length == 1) {
                        response = await fetchGeneAutocompleteSuggestions(inputQuery, 10, selectedSpecies[0]);
                    }

                    // If genome is selected (used in GeneViewerPage.tsx)
                    else if (selectedGenomes && selectedGenomes.length > 0) {
                        const genomeIds = selectedGenomes.map(genome => genome.id).join(',');
                        response = await fetchGeneAutocompleteSuggestions(inputQuery, 10, undefined, genomeIds);
                    } else {
                        response = await fetchGeneAutocompleteSuggestions(inputQuery);
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
        [selectedSpecies, selectedGenomes]
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
    const [selectedGeneId, setSelectedGeneId] = useState<number | null>(null);

    // Fetch search results based on the query, selected species, page, sort field, and sort order
    const fetchSearchResults = useCallback(
        async (page = 1, sortField = currentSortField, sortOrder = currentSortOrder) => {

            if (selectedGeneId) {
                try {
                    const response = await fetchGeneById(selectedGeneId);
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
                const gene = geneName.trim() || query.trim();
                if (gene) {
                    // Build the query parameters dynamically
                    const params = new URLSearchParams({
                        'query': gene,
                        'page': String(page),
                        'per_page': String(pageSize),
                        'sortField': sortField,
                        'sortOrder': sortOrder,
                    });

                    // Add genome IDs if available
                    if (selectedGenomes && selectedGenomes.length > 0) {
                        params.append('genome_ids', selectedGenomes.map((genome: {
                            id: number;
                            name: string
                        }) => genome.id).join(','));
                    }

                    try {
                        const response = await fetchGeneSearchResults(
                            gene, page, pageSize, sortField, sortOrder, selectedGenomes, selectedSpecies
                        );

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
        [selectedGeneId, geneName, query, selectedSpecies, selectedGenomes, currentSortField, currentSortOrder, pageSize]
    );


    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newQuery = event.target.value;
        setQuery(newQuery);
        setGeneName('');
        setSelectedGeneId(null);
        debouncedFetchSuggestions(newQuery);
    };

    const handleSuggestionClick = (suggestion: { gene_id: number, strain_name: string, gene_name: string }) => {
        console.log('suggestion: ' + suggestion)
        console.log('strain name: ' + suggestion.strain_name)
        console.log('suggestion.strain_id: ' + suggestion.gene_name)
        setQuery(suggestion.gene_name);
        setGeneName(suggestion.gene_name);
        setSelectedGeneId(suggestion.gene_id);
        setSuggestions([]);
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        console.log('selectedStrainId:' + selectedGeneId)
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
        <section id="vf-tabs__section--1">
            <div>
                <p/>
            </div>
            <div className={`vf-grid__col--span-3 ${styles.vfGeneSection}`}>
                <form onSubmit={handleSubmit}
                      className="vf-form vf-form--search vf-form--search--responsive | vf-sidebar vf-sidebar--end">
                    <h2 className={`vf-section-header__subheading ${styles.vfGeneSubHeading}`}>Search Gene</h2>
                    <div>
                        <p/>
                    </div>
                    <GeneSearchInput
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
                        <GeneResultsTable
                            results={results}
                            onSortClick={onSortClick}
                            linkData={linkData}
                            viewState={viewState}
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

export default GeneSearchForm;
