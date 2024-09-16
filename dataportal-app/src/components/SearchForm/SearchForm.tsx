import React, {useState, useEffect, useCallback} from 'react';
import {getData} from '../../services/api';
import {extractIsolateName} from '../../utils/utils';
import styles from "./SearchForm.module.scss";

interface SearchFormProps {
    onSearch: (isolateName: string) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({onSearch}) => {
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

    // Fetch suggestions for autocomplete
    const fetchSuggestions = useCallback(async () => {
        if (query.length >= 2) {
            try {
                const response = await getData(`/search/autocomplete/?query=${encodeURIComponent(query)}`);
                if (response) {
                    setSuggestions(response);
                }
            } catch (error) {
                console.error('Error fetching suggestions:', error);
            }
        } else {
            setSuggestions([]);
        }
    }, [query]);

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

    // Fetch search results based on query, page, sort field, and sort order
    const fetchSearchResults = useCallback(
        async (page: number = 1, sortField: string = currentSortField, sortOrder: string = currentSortOrder) => {
            let isolate = isolateName.trim() || query.trim();

            if (isolate) {
                const queryString = new URLSearchParams({
                    'isolate_name': isolate,
                    'page': String(page),
                    'sortField': sortField,
                    'sortOrder': sortOrder
                }).toString();

                try {
                    const response = await getData(`/search/results/?${queryString}`);
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
        [isolateName, query, currentSortField, currentSortOrder]
    );

    useEffect(() => {
        debouncedFetchSuggestions();
    }, [query, debouncedFetchSuggestions]);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setQuery(event.target.value);
        setIsolateName('');
    };

    const handleSuggestionClick = (suggestion: string) => {
        setQuery(suggestion);
        setIsolateName(extractIsolateName(suggestion));
        setSuggestions([]);
    };

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
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
                        <input type="hidden" name="isolate-name" value={isolateName}/>

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
                                <svg width="12" height="22" xmlns="http://www.w3.org/2000/svg">
                                    <path id="vf-table--sortable-top-arrow" d="M6 0l6 10H0z"></path>
                                    <path id="vf-table--sortable-bottom-arrow" d="M6 22L0 12h12z"></path>
                                </svg>
                            </button>
                        </th>
                        <th className="vf-table__heading" scope="col">
                            <button
                                className="vf-button vf-button--sm vf-button--icon vf-table__button vf-table__button--sortable"
                                onClick={() => handleSortClick('isolate_name')}
                            >
                                Strain
                                <svg width="12" height="22" xmlns="http://www.w3.org/2000/svg">
                                    <path id="vf-table--sortable-top-arrow" d="M6 0l6 10H0z"></path>
                                    <path id="vf-table--sortable-bottom-arrow" d="M6 22L0 12h12z"></path>
                                </svg>
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
                    {/* Pagination Section */}
                    {totalPages > 1 && (
                        <tfoot className={`vf-table__footer ${styles.vfTableFooter}`}>
                        <tr className="vf-table__row">
                            <td className="vf-table__cell" colSpan={5}>
                                <nav className="vf-pagination" aria-label="Pagination">
                                    <ul className="vf-pagination__list">
                                        {hasPrevious && (
                                            <li className="vf-pagination__item">
                                                <button
                                                    className="vf-pagination__link"
                                                    onClick={() => handlePageClick(1)}
                                                >
                                                    First
                                                </button>
                                            </li>
                                        )}
                                        {hasPrevious && (
                                            <li className="vf-pagination__item vf-pagination__item--previous-page">
                                                <button
                                                    className="vf-pagination__link"
                                                    onClick={() => handlePageClick(currentPage - 1)}
                                                >
                                                    Previous
                                                </button>
                                            </li>
                                        )}
                                        <li className="vf-pagination__item">
              <span className="vf-pagination__link">
                Page {currentPage} of {totalPages}
              </span>
                                        </li>
                                        {hasNext && (
                                            <li className="vf-pagination__item vf-pagination__item--next-page">
                                                <button
                                                    className="vf-pagination__link"
                                                    onClick={() => handlePageClick(currentPage + 1)}
                                                >
                                                    Next
                                                </button>
                                            </li>
                                        )}
                                        {hasNext && (
                                            <li className="vf-pagination__item">
                                                <button
                                                    className="vf-pagination__link"
                                                    onClick={() => handlePageClick(totalPages)}
                                                >
                                                    Last
                                                </button>
                                            </li>
                                        )}
                                    </ul>
                                </nav>
                            </td>
                        </tr>
                        </tfoot>
                    )}
                </table>
            </div>
        </div>
    );
};

export default SearchForm;
