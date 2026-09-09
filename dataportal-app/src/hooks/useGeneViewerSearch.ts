import {useState, useCallback, useEffect} from 'react';
import {GeneService} from '../services/gene';
import {GenomeMeta} from '../interfaces/Genome';
import {APP_CONSTANTS} from '../utils/common/constants';
import {useFilterStore} from '../stores/filterStore';
import {GeneMeta} from "../interfaces/Gene";
import {convertFacetedFiltersToLegacy, convertFacetOperatorsToLegacy} from '../utils/common/filterUtils';

interface UseGeneViewerSearchProps {
    genomeMeta: GenomeMeta | null;
    setLoading: (loading: boolean) => void;
    pageSize?: number;
}

interface UseGeneViewerSearchReturn {
    // Data
    geneResults: any[];
    totalPages: number;
    currentPage: number;
    hasPrevious: boolean;
    hasNext: boolean;
    totalCount: number;

    // UI State
    geneSearchQuery: string;
    sortField: string;
    sortOrder: 'asc' | 'desc';

    // Actions
    setGeneSearchQuery: (query: string) => void;
    handleGeneSearch: (overridePageSize?: number, overridePage?: number) => Promise<void>;
    handleGeneSortClick: (field: string) => Promise<void>;
    handlePageChange: (page: number) => Promise<void>;
}

export const useGeneViewerSearch = ({
                                        genomeMeta,
                                        setLoading,
                                        pageSize = 10,
                                    }: UseGeneViewerSearchProps): UseGeneViewerSearchReturn => {
    // Get filter store state and actions for URL synchronization
    const geneSearchQuery = useFilterStore(state => state.geneSearchQuery);
    const geneSortField = useFilterStore(state => state.geneSortField);
    const geneSortOrder = useFilterStore(state => state.geneSortOrder);
    const facetedFilters = useFilterStore(state => state.facetedFilters);
    const facetOperators = useFilterStore(state => state.facetOperators);
    const setGeneSearchQuery = useFilterStore(state => state.setGeneSearchQuery);
    const setGeneSortField = useFilterStore(state => state.setGeneSortField);
    const setGeneSortOrder = useFilterStore(state => state.setGeneSortOrder);

    // Local state
    const [geneResults, setGeneResults] = useState<GeneMeta[]>([]);
    const [totalPages, setTotalPages] = useState(1);
    const [currentPage, setCurrentPage] = useState(1);
    const [hasPrevious, setHasPrevious] = useState(false);
    const [hasNext, setHasNext] = useState(false);
    const [totalCount, setTotalCount] = useState(0);
    
    const handleGeneSearch = useCallback(async (overridePageSize?: number, overridePage?: number): Promise<void> => {
        if (genomeMeta?.isolate_name) {
            try {
                setLoading(true);
                // console.log('useGeneViewerSearch - Making API call with query:', geneSearchQuery);
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    geneSearchQuery,
                    overridePage || currentPage, // page - use override if provided, otherwise use current page
                    overridePageSize || pageSize, // pageSize - use override if provided, otherwise use current pageSize
                    geneSortField, // Use filter store sort field
                    geneSortOrder, // Use filter store sort order
                    [{isolate_name: genomeMeta.isolate_name, type_strain: genomeMeta.type_strain}], // genomeFilter
                    undefined, // speciesFilter
                    convertFacetedFiltersToLegacy(facetedFilters), // Convert facet filters to legacy format
                    convertFacetOperatorsToLegacy(facetOperators), // Convert facet operators to legacy format
                    undefined // No locus_tag for gene viewer search
                );
                // console.log('useGeneViewerSearch - Search results received:', {
                //     query: geneSearchQuery,
                //     dataLength: response.data?.length || 0,
                //     pagination: response.pagination
                // });

                setGeneResults(response.data || []);
                setTotalPages(response.pagination?.num_pages || 1);
                setCurrentPage(response.pagination?.page_number || 1);
                setHasPrevious(response.pagination?.has_previous || false);
                setHasNext(response.pagination?.has_next || false);
                setTotalCount(response.pagination?.total_results || 0);
            } catch (error) {
                console.error('Error searching genes:', error);
            } finally {
                setTimeout(() => setLoading(false), APP_CONSTANTS.SPINNER_DELAY);
            }
        }
    }, [genomeMeta, geneSearchQuery, pageSize, geneSortField, geneSortOrder, facetedFilters, facetOperators, setLoading]);

    // Trigger search when facet filters or search query changes
    useEffect(() => {
        if (genomeMeta?.isolate_name) {
            console.log('useGeneViewerSearch - Facet filters or search query changed, triggering search');
            setCurrentPage(1); // Reset to page 1 when filters change
            handleGeneSearch(undefined, 1);
        }
    }, [facetedFilters, facetOperators, geneSearchQuery, handleGeneSearch, genomeMeta?.isolate_name]);

    // Trigger initial search when genome becomes available
    useEffect(() => {
        if (genomeMeta?.isolate_name) {
            console.log('useGeneViewerSearch - Initial search triggered for genome:', genomeMeta.isolate_name);
            handleGeneSearch();
        }
    }, [genomeMeta?.isolate_name, handleGeneSearch]);

    const handleGeneSortClick = async (field: string): Promise<void> => {
        const newSortOrder = geneSortField === field && geneSortOrder === 'asc' ? 'desc' : 'asc';
        
        // Update filter store for URL synchronization
        setGeneSortField(field);
        setGeneSortOrder(newSortOrder);

        console.log('Geneviewer Sorting Genes by:', {field, order: newSortOrder});

        // Trigger a new search with the updated sort parameters
        await handleGeneSearch();
    };

    const handlePageChange = async (page: number): Promise<void> => {
        setCurrentPage(page);
        await handleGeneSearch(undefined, page);
    };

    return {
        // Data
        geneResults,
        totalPages,
        currentPage,
        hasPrevious,
        hasNext,
        totalCount,

        // UI State
        geneSearchQuery,
        sortField: geneSortField,
        sortOrder: geneSortOrder,

        // Actions
        setGeneSearchQuery,
        handleGeneSearch,
        handleGeneSortClick,
        handlePageChange,
    };
}; 