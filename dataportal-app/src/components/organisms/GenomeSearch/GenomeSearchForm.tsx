import React, {useCallback, useState} from 'react';
import {getData} from "../../../services/api";
import styles from "./GenomeSearchForm.module.scss";
import Pagination from "../../molecules/Pagination";
import GenomeSearchInput from "@components/organisms/GenomeSearch/GenomeSearchInput";
import GenomeResultsTable from "@components/organisms/GenomeSearch/GenomeResultsTable";

interface SearchGenomeFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
    onGenomeSelect: (genome: string) => void;
    selectedSpecies: string;
}

const GenomeSearchForm: React.FC<SearchGenomeFormProps> = ({
                                                               searchQuery,
                                                               onSearchQueryChange,
                                                               onSearchSubmit,
                                                               onGenomeSelect,
                                                               selectedSpecies
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

    // Fetch suggestions for autocomplete based on the query and selected species
    const fetchSuggestions = useCallback(
        async (inputQuery: string) => {
            if (inputQuery.length >= 2) {
                try {
                    const url = selectedSpecies
                        ? `/search/autocomplete?query=${encodeURIComponent(inputQuery)}&species_id=${selectedSpecies}`
                        : `/search/autocomplete?query=${encodeURIComponent(inputQuery)}`;

                    const response = await getData(url);

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
    const debounce = (func: Function, delay: number) => {
        let timeoutId: NodeJS.Timeout;
        return (...args: any[]) => {
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
                // Fetch data by strain_id
                try {
                    const response = await getData(`/search/genome?strain_id=${selectedStrainId}&page=${page}`);
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
            } else {
                // Perform the regular search
                let isolate = isolateName.trim() || query.trim();
                if (isolate && selectedSpecies) {
                    const queryString = new URLSearchParams({
                        'isolate_name': isolate,
                        'species_id': selectedSpecies,
                        'page': String(page),
                        'sortField': sortField,
                        'sortOrder': sortOrder
                    }).toString();

                    try {
                        const response = await getData(`/search/genome?${queryString}`);
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
        [selectedStrainId, isolateName, query, selectedSpecies, currentSortField, currentSortOrder]
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
            <div className="vf-grid__col--span-3">
                <h2 className="vf-section-header__subheading">Search Genome</h2>
                <form onSubmit={handleSubmit}
                      className="vf-form vf-form--search vf-form--search--responsive | vf-sidebar vf-sidebar--end">
                        <GenomeSearchInput
                            query={query}
                            onInputChange={handleInputChange}
                            suggestions={suggestions}
                            onSuggestionClick={handleSuggestionClick}
                        />
                        <button type="submit" className="vf-button vf-button--primary vf-button--sm">
                            <span className="vf-button__text">Search</span>
                        </button>
                </form>

                <div className="vf-grid__col--span-3" id="results-table"
                     style={{display: results.length > 0 ? 'block' : 'none'}}>
                    <GenomeResultsTable results={results} onSortClick={handleSortClick}/>
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
        </section>
    );
};

export default GenomeSearchForm;
