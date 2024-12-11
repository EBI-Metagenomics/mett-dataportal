import React, {useCallback, useEffect, useState} from 'react';
import GeneSearchInput from './GeneSearchInput';
import styles from "@components/organisms/GeneSearch/GeneSearchForm.module.scss";
import GeneResultsTable from "@components/organisms/GeneSearch/GeneResultsTable";
import Pagination from "@components/molecules/Pagination";
import {
    fetchEssentialityTags,
    fetchGeneAutocompleteSuggestions,
    fetchGeneSearchResults
} from "../../../services/geneService";
import {createViewState} from '@jbrowse/react-app';
import {GeneMeta, GeneSuggestion} from "../../../interfaces/Gene";
import {LinkData} from "../../../interfaces/Auxiliary";
import {BaseGenome} from "../../../interfaces/Genome";

type ViewModel = ReturnType<typeof createViewState>;

interface GeneSearchFormProps {
    searchQuery: string,
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void,
    onSearchSubmit: () => void,
    selectedSpecies?: number [],
    results: any[],
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    sortField: string,
    sortOrder: 'asc' | 'desc';
    selectedGenomes?: BaseGenome[],
    linkData: LinkData,
    viewState?: ViewModel;
}

const GeneSearchForm: React.FC<GeneSearchFormProps> = ({
                                                           selectedSpecies,
                                                           onSortClick,
                                                           selectedGenomes,
                                                           linkData,
                                                           viewState,
                                                           sortField,
                                                           sortOrder
                                                       }) => {
    const [query, setQuery] = useState<string>('');
    const [suggestions, setSuggestions] = useState<GeneSuggestion[]>([]);
    const [geneName, setGeneName] = useState<string>('');
    const [results, setResults] = useState<GeneMeta[]>([]);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [hasPrevious, setHasPrevious] = useState<boolean>(false);
    const [hasNext, setHasNext] = useState<boolean>(false);
    const [pageSize, setPageSize] = useState<number>(10);
    const [essentialityFilter, setEssentialityFilter] = useState<string[]>([]);
    const [essentialityTags, setEssentialityTags] = useState<string[]>([]);

    const handlePageSizeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newSize = parseInt(event.target.value, 10);
        setPageSize(newSize);
    };

    useEffect(() => {
    const essentialityTags = async () => {
        try {
            const response = await fetchEssentialityTags();
            console.log("*****response",response);
            setEssentialityTags(response.data.map((tag: any) => tag.name));
        } catch (error) {
            console.error('Error fetching essentiality tags:', error);
        }
    };

    fetchEssentialityTags();
}, []);

    useEffect(() => {
        fetchSearchResults(1, sortField, sortOrder, essentialityFilter);
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
        async (page = 1, sortField: string, sortOrder: string, essentialityFilter: string[]) => {

            const genomeFilter = selectedGenomes && selectedGenomes.length > 0
                ? selectedGenomes.map((genome) => ({id: genome.id, name: genome.isolate_name}))
                : undefined;
            const speciesFilter = selectedSpecies && selectedSpecies.length === 1
                ? selectedSpecies
                : undefined;

            try {
                const response = await fetchGeneSearchResults(
                    query, page, pageSize, sortField, sortOrder, genomeFilter, speciesFilter, essentialityFilter
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
        },
        [query, selectedSpecies, selectedGenomes, sortField, sortOrder, pageSize]
    );


    useEffect(() => {
        fetchSearchResults(1, sortField, sortOrder, essentialityFilter);
    }, [selectedSpecies, selectedGenomes, sortField, sortOrder, pageSize]);

    const handleEssentialityFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setEssentialityFilter((prev) =>
            prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value]
        );
    };


    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newQuery = event.target.value;
        setQuery(newQuery);
        setGeneName('');
        setSelectedGeneId(null);
        debouncedFetchSuggestions(newQuery);
    };

    const handleSuggestionClick = (suggestion: GeneSuggestion) => {
        console.log('suggestion: ' + suggestion)
        console.log('strain name: ' + suggestion.strain_name)
        console.log('suggestion.gene_id: ' + suggestion.gene_id)
        console.log('suggestion.gene_name: ' + suggestion.gene_name)
        console.log('suggestion.locus_tag: ' + suggestion.locus_tag)
        setQuery(suggestion.gene_name || suggestion.locus_tag);
        setGeneName(suggestion.gene_name);
        setSelectedGeneId(suggestion.gene_id);
        setSuggestions([]);
    };


    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        console.log('selectedGeneId:' + selectedGeneId)
        event.preventDefault();
        fetchSearchResults(1, sortField, sortOrder, essentialityFilter);
    };


    const handlePageClick = (page: number) => {
        setCurrentPage(page);
        fetchSearchResults(page, sortField, sortOrder, essentialityFilter);
    };

    return (
        <section id="vf-tabs__section--2">
            <div>
                <p/>
                {/*{selectedGenomes && selectedGenomes[0].type_strain && (*/}
                {/*<div className={styles.essentialityFilterContainer}>*/}
                {/*    <h3>Essentiality</h3>*/}
                {/*    <label>*/}
                {/*        <input*/}
                {/*            type="checkbox"*/}
                {/*            value="Essential"*/}
                {/*            checked={essentialityFilter.includes("Essential")}*/}
                {/*            onChange={handleEssentialityFilterChange}*/}
                {/*        />*/}
                {/*        Essential*/}
                {/*    </label>*/}
                {/*    <label>*/}
                {/*        <input*/}
                {/*            type="checkbox"*/}
                {/*            value="Not Essential"*/}
                {/*            checked={essentialityFilter.includes("Not Essential")}*/}
                {/*            onChange={handleEssentialityFilterChange}*/}
                {/*        />*/}
                {/*        Not Essential*/}
                {/*    </label>*/}
                {/*    <label>*/}
                {/*        <input*/}
                {/*            type="checkbox"*/}
                {/*            value="Not Clear"*/}
                {/*            checked={essentialityFilter.includes("Not Clear")}*/}
                {/*            onChange={handleEssentialityFilterChange}*/}
                {/*        />*/}
                {/*        Not Clear*/}
                {/*    </label>*/}
                {/*</div>*/}
                {/*)}*/}
            </div>
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


            <div>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
            </div>
        </section>
    );
};

export default GeneSearchForm;
