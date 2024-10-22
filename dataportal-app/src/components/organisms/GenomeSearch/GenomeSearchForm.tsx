import React, {useCallback, useState} from 'react';
import {getData} from "../../../services/api";
import Pagination from "../../molecules/Pagination";
import GenomeSearchInput from "@components/organisms/GenomeSearch/GenomeSearchInput";
import GenomeResultsTable from "@components/organisms/GenomeSearch/GenomeResultsTable";
import styles from "@components/organisms/GenomeSearch/GenomeSearchForm.module.scss";

interface SearchGenomeFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
    selectedSpecies: string;
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

    // Fetch suggestions for autocomplete based on the query and selected species
    const fetchSuggestions = useCallback(
        async (inputQuery: string) => {
            if (inputQuery.length >= 2) {
                try {
                    const url = selectedSpecies
                        ? `/genomes/autocomplete?query=${encodeURIComponent(inputQuery)}&species_id=${selectedSpecies}`
                        : `/genomes/autocomplete?query=${encodeURIComponent(inputQuery)}`;

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
                    const response = await getData(`/genomes/${selectedStrainId}`);
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
                        'sortField': sortField,
                        'sortOrder': sortOrder
                    }).toString();

                    try {
                        const endpoint = (selectedSpecies && selectedSpecies.length === 1)
                            ? `/species/${selectedSpecies[0]}/genomes/search?${queryString}`
                            : `/genomes/search?${queryString}`;

                        const response = await getData(endpoint);

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
                    />
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
            <div>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
            </div>
        </section>
    );
};

export default GenomeSearchForm;
