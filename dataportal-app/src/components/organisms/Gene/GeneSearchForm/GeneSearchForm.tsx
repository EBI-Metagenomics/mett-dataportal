import React, {useCallback, useEffect, useState} from 'react';
import GeneSearchInput from './GeneSearchInput';
import styles from "@components/organisms/Gene/GeneSearchForm/GeneSearchForm.module.scss";
import {GeneService} from '../../../../services/geneService';
import {GeneFacetResponse, GeneMeta, GeneSuggestion} from "../../../../interfaces/Gene";
import {BaseGenome} from "../../../../interfaces/Genome";
import {
    DEFAULT_PER_PAGE_CNT,
    FACET_INITIAL_VISIBLE_CNT,
    FACET_STEP_CNT
} from "../../../../utils/appConstants";
import SelectedGenomes from "@components/Filters/SelectedGenomes";
import GeneFacetedFilter from "@components/Filters/GeneFacetedFilter";
import {useSearchUrlState} from '../../../../hooks/useSearchUrlState';
import {useFacets} from '../../../../contexts/FacetContext';
import {FacetItem, LinkData} from '../../../../interfaces/Auxiliary';
import GeneResultsTable from '../GeneResultsHandler/GeneResultsTable';
import {createViewState} from '@jbrowse/react-app';

type ViewModel = ReturnType<typeof createViewState>;

interface GeneSearchFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
    selectedSpecies?: string[];
    selectedGenomes: BaseGenome[];
    handleRemoveGenome: (genomeId: string) => void;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    onResultsChange: (results: GeneMeta[]) => void;
    sortField: string;
    sortOrder: 'asc' | 'desc';
    results: GeneMeta[];
    onSortClick: (field: string) => void;
    linkData: LinkData;
    viewState?: ViewModel;
    isTypeStrainAvailable: boolean;
}

const GeneSearchForm: React.FC<GeneSearchFormProps> = ({
    selectedSpecies,
    selectedGenomes,
    handleRemoveGenome,
    setLoading,
    onResultsChange,
    sortField,
    sortOrder,
    results,
    onSortClick,
    linkData,
    viewState,
    isTypeStrainAvailable,
}) => {
    const { state: urlState, updateUrl } = useSearchUrlState();
    const { state: facetState } = useFacets();
    const [searchInput, setSearchInput] = useState<string>(urlState.query || '');
    const [query, setQuery] = useState<string>(urlState.query || '');
    const [suggestions, setSuggestions] = useState<GeneSuggestion[]>([]);
    const [selectedFacets, setSelectedFacets] = useState<Record<string, string[]>>(urlState.selectedFacets || {});
    const [facetOperators, setFacetOperators] = useState<Record<string, 'AND' | 'OR'>>(urlState.facetOperators || {});
    const [facets, setFacets] = useState<GeneFacetResponse>({
        total_hits: 0,
        operators: {},
        species: [],
        isolate_name: [],
        cog_funcats: [],
        essentiality: [],
        kegg: [],
        pfam: [],
        interpro: [],
        ec_number: [],
        amr: [],
    });

    const [selectedGeneId, setSelectedGeneId] = useState<string | null>(null);

    const fetchSuggestions = useCallback(
        async (inputQuery: string) => {
            if (inputQuery.length >= 2) {
                try {
                    let response;

                    // If species is selected (used in HomePage.tsx)
                    if (selectedSpecies && selectedSpecies.length === 1) {
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            selectedSpecies[0],
                            undefined,
                            selectedFacets
                        );
                    }
                    // If genome is selected (used in GeneViewerPage.tsx)
                    else if (selectedGenomes && selectedGenomes.length > 0) {
                        const genomeIds = selectedGenomes.map(genome => genome.isolate_name).join(',');
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            undefined,
                            genomeIds,
                            selectedFacets
                        );
                    } else {
                        response = await GeneService.fetchGeneAutocompleteSuggestions(
                            inputQuery,
                            DEFAULT_PER_PAGE_CNT,
                            undefined,
                            undefined,
                            selectedFacets
                        );
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
        [selectedSpecies, selectedGenomes, selectedFacets]
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

    // Fetch search results based on the query, selected species, page, sort field, and sort order
    const fetchSearchResults = useCallback(
        async (
            page = 1,
            sortField: string,
            sortOrder: string,
            selectedFacetFilters: Record<string, string[]>,
            facetOperators?: Record<string, 'AND' | 'OR'>
        ) => {
            const genomeFilter = selectedGenomes?.length
                ? selectedGenomes.map((genome) => ({
                    isolate_name: genome.isolate_name,
                    type_strain: genome.type_strain
                }))
                : undefined;
            const speciesFilter = selectedSpecies?.length === 1 ? selectedSpecies : undefined;
            try {
                setLoading(true); // Start spinner
                let response = null;
                if (selectedGeneId) {
                    // Fetch by gene ID
                    const geneResponseObj = await GeneService.fetchGeneByLocusTag(selectedGeneId);
                    response = {
                        results: [geneResponseObj],
                        page_number: 1,
                        num_pages: 1,
                        has_previous: false,
                        has_next: false,
                    };
                } else {
                    // Fetch results using the advanced search API
                    response = await GeneService.fetchGeneSearchResultsAdvanced(
                        query,
                        page,
                        DEFAULT_PER_PAGE_CNT,
                        sortField,
                        sortOrder,
                        genomeFilter,
                        speciesFilter,
                        selectedFacetFilters,
                        facetOperators
                    );
                }
                if (response && response.results) {
                    onResultsChange(response.results);
                } else {
                    onResultsChange([]);
                }
            } catch (error) {
                console.error("Error fetching data:", error);
                onResultsChange([]);
            } finally {
                setLoading(false); // Stop spinner
            }
        },
        [query, selectedGeneId, selectedSpecies, selectedGenomes]
    );

    const loadFacets = useCallback(async () => {
        try {
            const response = await GeneService.fetchFacets({
                species: selectedSpecies,
                genomes: selectedGenomes.map(genome => genome.isolate_name),
                facets: selectedFacets,
                facetOperators: facetOperators
            });

            // Create a map of selected facet items
            const selectedMap = new Map<string, Set<string>>();
            Object.entries(selectedFacets || {}).forEach(([group, values]) => {
                selectedMap.set(group, new Set((values as string[]).map(v => String(v))));
            });

            // Process the response to mark selected items
            const processedFacets: GeneFacetResponse = { total_hits: 0, operators: {} };
            
            Object.entries(response).forEach(([group, items]) => {
                if (group === 'total_hits') {
                    processedFacets.total_hits = items as number;
                    return;
                }

                if (group === 'operators') {
                    processedFacets.operators = items as Record<string, 'AND' | 'OR'>;
                    return;
                }

                const selectedValues = selectedMap.get(group) || new Set();
                const facetItems = (items as Array<{ value: string | number | boolean; count: number }>).map(item => ({
                    ...item,
                    value: String(item.value), // Convert value to string
                    selected: selectedValues.has(String(item.value))
                })) as FacetItem[];

                // Sort selected items to the top
                facetItems.sort((a, b) => {
                    if (a.selected && !b.selected) return -1;
                    if (!a.selected && b.selected) return 1;
                    return 0;
                });

                processedFacets[group] = facetItems;
            });

            setFacets(processedFacets);
        } catch (error) {
            console.error('Error loading facets:', error);
        }
    }, [selectedSpecies, selectedGenomes, selectedFacets, facetOperators]);

    const loadResults = useCallback(async () => {
        try {
            setLoading(true);
            const genomeFilter = selectedGenomes?.length
                ? selectedGenomes.map((genome) => ({
                    isolate_name: genome.isolate_name,
                    type_strain: genome.type_strain
                }))
                : undefined;
            const speciesFilter = selectedSpecies?.length === 1 ? selectedSpecies : undefined;

            const response = await GeneService.fetchGeneSearchResultsAdvanced(
                query,
                urlState.page || 1,
                DEFAULT_PER_PAGE_CNT,
                sortField,
                sortOrder,
                genomeFilter,
                speciesFilter,
                selectedFacets,
                facetOperators
            );

            onResultsChange(response.results);
        } catch (error) {
            console.error('Error loading results:', error);
        } finally {
            setLoading(false);
        }
    }, [query, urlState.page, sortField, sortOrder, selectedSpecies, selectedGenomes, selectedFacets, facetOperators, onResultsChange]);

    // Load initial data from URL
    useEffect(() => {
        const loadInitialData = async () => {
            setLoading(true);
            try {
                await Promise.all([
                    loadFacets(),
                    loadResults()
                ]);
            } catch (error) {
                console.error('Error loading initial data:', error);
            } finally {
                setLoading(false);
            }
        };
        loadInitialData();
    }, [query, selectedSpecies, selectedGenomes, selectedFacets, facetOperators, sortField, sortOrder, urlState.page]);

    // Update URL when state changes
    useEffect(() => {
        const updateUrlState = () => {
            const newState = {
                query: urlState.query,
                page: urlState.page,
                pageSize: urlState.pageSize,
                sortField: urlState.sortField,
                sortOrder: urlState.sortOrder,
                selectedSpecies: urlState.selectedSpecies,
                selectedGenomes: urlState.selectedGenomes,
                selectedFacets: facetState.selectedFacets,
                facetOperators: facetState.facetOperators
            };
            updateUrl(newState);
        };

        const timeoutId = setTimeout(updateUrlState, 300);
        return () => clearTimeout(timeoutId);
    }, [urlState, facetState.selectedFacets, facetState.facetOperators, updateUrl]);

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newInput = event.target.value;
        setSearchInput(newInput);
        setSelectedGeneId(null);
        debouncedFetchSuggestions(newInput);
        // Do NOT update query or fetch results here
        // Only update the URL state for query on submit or suggestion select
    };

    const handleSuggestionClick = (suggestion: GeneSuggestion) => {
        setQuery(suggestion.gene_name || suggestion.locus_tag);
        setSelectedGeneId(suggestion.locus_tag);
        setSuggestions([]);
        // Show only the selected record in the results table
        onResultsChange([suggestion as GeneMeta]);
        // Update URL for consistency
        const newState = {
            ...urlState,
            query: suggestion.gene_name || suggestion.locus_tag || undefined,
            page: 1 // Reset to first page when query changes
        };
        updateUrl(newState);
        // Do NOT call fetchSearchResults here
    };

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setQuery(searchInput);
        // Update URL and fetch results
        const newState = {
            ...urlState,
            query: searchInput || undefined,
            page: 1 // Reset to first page when query changes
        };
        updateUrl(newState);
        fetchSearchResults(1, sortField, sortOrder, selectedFacets, facetOperators);
    };

    const handleToggleFacet = useCallback((facetGroup: string, value: string) => {
        setSelectedFacets(prev => {
            const currentValues = prev[facetGroup] || [];
            const newValues = currentValues.includes(value)
                ? currentValues.filter(v => v !== value)
                : [...currentValues, value];
            
            const newFacets = {
                ...prev,
                [facetGroup]: newValues
            };
            
            return newFacets;
        });
    }, []);

    const handleFacetOperatorChange = useCallback((facetGroup: string, operator: 'AND' | 'OR') => {
        setFacetOperators(prev => ({
            ...prev,
            [facetGroup]: operator
        }));
    }, []);

    return (
        <div className={styles.container}>
            <div className={styles.leftPane}>
                <SelectedGenomes selectedGenomes={selectedGenomes} onRemoveGenome={handleRemoveGenome} />
                <GeneFacetedFilter
                    facets={facets}
                    onToggleFacet={handleToggleFacet}
                    initialVisibleCount={FACET_INITIAL_VISIBLE_CNT}
                    loadMoreStep={FACET_STEP_CNT}
                    onOperatorChange={handleFacetOperatorChange}
                />
            </div>

            <div className={styles.rightPane}>
                <form onSubmit={handleSubmit} className={styles.searchForm}>
                    <GeneSearchInput
                        query={searchInput}
                        onInputChange={handleInputChange}
                        suggestions={suggestions}
                        onSuggestionClick={handleSuggestionClick}
                        onSuggestionsClear={() => setSuggestions([])}
                    />
                </form>

                <GeneResultsTable
                    results={results}
                    onSortClick={onSortClick}
                    linkData={linkData}
                    viewState={viewState}
                    setLoading={setLoading}
                    isTypeStrainAvailable={isTypeStrainAvailable}
                    page={urlState.page || 1}
                    pageSize={DEFAULT_PER_PAGE_CNT}
                    totalHits={facets.total_hits}
                    onPageChange={(page) => {
                        const newState = {
                            ...urlState,
                            page
                        };
                        updateUrl(newState);
                    }}
                />
            </div>
        </div>
    );
};

export default GeneSearchForm;
