import React, {useCallback, useState} from 'react';
import {getData} from "../../services/api";
import {extractIsolateName} from "../../utils/utils";
import styles from "./SearchGenomeForm.module.scss";

interface SearchGenomeFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
    onGenomeSelect: (genome: string) => void;
    selectedSpecies: string; // Accept the selectedSpecies prop
}

const SearchGenomeForm: React.FC<SearchGenomeFormProps> = ({
                                                               searchQuery,
                                                               onSearchQueryChange,
                                                               onSearchSubmit,
                                                               onGenomeSelect,
                                                               selectedSpecies // Use the selectedSpecies prop
                                                           }) => {
    const [query, setQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [isolateName, setIsolateName] = useState<string>('');
    const [results, setResults] = useState<any[]>([]);
    const [currentSortField, setCurrentSortField] = useState<string>('');
    const [currentSortOrder, setCurrentSortOrder] = useState<string>('');
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);

    // Fetch suggestions for autocomplete based on the query and selected species
    const fetchSuggestions = useCallback(async () => {
        console.log("selectedSpecies: " + selectedSpecies);

        if (query.length >= 2) {
            try {
                const url = selectedSpecies
                    ? `/search/autocomplete?query=${encodeURIComponent(query)}&species_id=${selectedSpecies}`
                    : `/search/autocomplete?query=${encodeURIComponent(query)}`;

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
    }, [query, selectedSpecies]);


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

    // Fetch search results based on the query, selected species, page, sort field, and sort order
    const fetchSearchResults = useCallback(
        async (page: number = 1, sortField: string = currentSortField, sortOrder: string = currentSortOrder) => {
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
                    const response = await getData(`/search/genome/?${queryString}`);
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
        },
        [isolateName, query, selectedSpecies, currentSortField, currentSortOrder]
    );

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setQuery(event.target.value);
        setIsolateName('');
        debouncedFetchSuggestions(); // Call the debounced fetch suggestions function
    };

    const handleSuggestionClick = (suggestion: string) => {
        setQuery(suggestion);
        setIsolateName(extractIsolateName(suggestion));
        setSuggestions([]);
        fetchSearchResults(); // Fetch results for the selected suggestion
    };

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        fetchSearchResults(); // Fetch results based on typed query or selected suggestion
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
                    <div className="vf-sidebar__inner">
                        <div className="vf-form__item">
                            <input
                                type="search"
                                value={query}
                                onChange={handleInputChange}
                                placeholder="Search..."
                                className="vf-form__input"
                                autoComplete="off"
                                aria-autocomplete="list"
                                aria-controls="suggestions"
                                role="combobox"
                                aria-expanded={suggestions.length > 0}
                            />
                            {suggestions.length > 0 && (
                                <div id="suggestions" className="vf-dropdown__menu" role="listbox">
                                    {suggestions.map((suggestion, index) => (
                                        <div
                                            key={index}
                                            className="suggestion-item"
                                            onClick={() => handleSuggestionClick(suggestion)}
                                            role="option"
                                        >
                                            {suggestion}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        <button type="submit" className="vf-button vf-button--primary vf-button--sm">
                            <span className="vf-button__text">Search</span>
                        </button>
                    </div>
                </form>

                {/* Search Results Section */}
                <div className="vf-grid__col--span-3" id="results-table"
                     style={{display: results.length > 0 ? 'block' : 'none'}}>
                    <h3>Search Results</h3>
                    <table className="vf-table vf-table--sortable">
                        <thead className="vf-table__header">
                        <tr className="vf-table__row">
                            <th className="vf-table__heading" scope="col">
                                <button
                                    className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                                    onClick={() => handleSortClick('species')}
                                >
                                    Species
                                </button>
                            </th>
                            <th className="vf-table__heading" scope="col">
                                <button
                                    className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                                    onClick={() => handleSortClick('isolate_name')}
                                >
                                    Strain
                                </button>
                            </th>
                            <th className="vf-table__heading" scope="col">Assembly</th>
                            <th className="vf-table__heading" scope="col">Annotations</th>
                            <th className="vf-table__heading" scope="col">Actions</th>
                        </tr>
                        </thead>
                        <tbody className="vf-table__body">
                        {results.map((result, index) => (
                            <tr key={index} className="vf-table__row">
                                <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.species || 'Unknown Species'}</td>
                                <td className={`vf-table__cell ${styles.vfTableCell}`}>{result.isolate_name || 'Unknown Isolate'}</td>
                                <td className={`vf-table__cell ${styles.vfTableCell}`}>
                                    <a href={result.fasta_file || '#'}>{result.assembly_name || 'Unknown Assembly'}</a>
                                </td>
                                <td className={`vf-table__cell ${styles.vfTableCell}`}><a
                                    href={result.gff_file || '#'}>GFF</a></td>
                                <td className={`vf-table__cell ${styles.vfTableCell}`}><a
                                    href={`/jbrowse/${result.id}/`}>Browse</a></td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
};

export default SearchGenomeForm;
