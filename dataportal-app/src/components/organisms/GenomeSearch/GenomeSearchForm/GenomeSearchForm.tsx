import React, {useCallback, useEffect, useState} from 'react';
import Pagination from "../../../molecules/Pagination";
import GenomeSearchInput from "@components/organisms/GenomeSearch/GenomeSearchForm/GenomeSearchInput";
import GenomeResultsTable from "@components/organisms/GenomeSearch/GenomeResultsHandler/GenomeResultsTable";
import styles from "@components/organisms/GenomeSearch/GenomeSearchForm/GenomeSearchForm.module.scss";
import {GenomeService} from "../../../../services/genomeService";
import {LinkData} from "../../../../interfaces/Auxiliary";
import {BaseGenome} from "../../../../interfaces/Genome";

interface SearchGenomeFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: (field: string) => void;
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    selectedSpecies: number [];
    selectedTypeStrains: number[];
    results: any[];
    sortField: string,
    sortOrder: 'asc' | 'desc';
    selectedGenomes: BaseGenome[];
    onToggleGenomeSelect: (genome: BaseGenome) => void;
    // onGenomeSelect: (genome: { id: number; name: string }) => void;
    linkData: LinkData;
}

const GenomeSearchForm: React.FC<SearchGenomeFormProps> = ({
                                                               selectedSpecies,
                                                               selectedTypeStrains,
                                                               selectedGenomes,
                                                               onToggleGenomeSelect,
                                                               // onGenomeSelect,
                                                               onSortClick,
                                                               sortField,
                                                               sortOrder,
                                                               linkData
                                                           }) => {
    const [query, setQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<{
        strain_id: number,
        isolate_name: string,
        assembly_name: string
    }[]>([]);
    const [isolateName, setIsolateName] = useState<string>('');
    const [results, setResults] = useState<any[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);
    const [pageSize, setPageSize] = useState<number>(10);

    const [resetFlag, setResetFlag] = useState<boolean>(false);

    const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newSize = parseInt(event.target.value, 10);
        setPageSize(newSize);
        setResetFlag(true);
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
            const qry = isolateName.trim() || query.trim();
            console.log("fetchSearchResults called with page:", page);

            const speciesFilter = selectedSpecies.length ? selectedSpecies : [];
            const typeStrainFilter = selectedTypeStrains.length ? selectedTypeStrains : null;

            try {
                let response;

                if (typeStrainFilter) {
                    console.log("Fetching genomes by type strain IDs:", typeStrainFilter);
                    response = await GenomeService.fetchGenomeByStrainIds(typeStrainFilter);
                    setResults(response);
                    setTotalPages(1);
                    setHasPrevious(false);
                    setHasNext(false);
                } else {
                    console.log("Fetching genomes using standard search");
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
            } catch (error) {
                console.error("Error fetching data:", error);
                setResults([]);
                setTotalPages(1);
                setHasPrevious(false);
                setHasNext(false);
            }
        },
        [query, isolateName, selectedSpecies, selectedTypeStrains, sortField, sortOrder, pageSize]
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

    const handleSuggestionClick = (suggestion: { strain_id: number, isolate_name: string, assembly_name: string }) => {
        console.log('suggestion: ' + suggestion)
        console.log('isolateName: ' + isolateName)
        console.log('suggestion.strain_id: ' + suggestion.strain_id)
        setQuery(suggestion.isolate_name);
        setIsolateName(suggestion.isolate_name);
        setSelectedStrainId(suggestion.strain_id);
        setSuggestions([]);
        // EMG-7006 - no auto selection of filters
        //onGenomeSelect({id: suggestion.strain_id, name: suggestion.isolate_name});
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        console.log('selectedStrainId:' + selectedStrainId)
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