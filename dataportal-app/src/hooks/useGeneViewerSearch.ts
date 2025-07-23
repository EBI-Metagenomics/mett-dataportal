import {useState} from 'react';
import {GeneService} from '../services/geneService';
import {GenomeMeta} from '../interfaces/Genome';
import {APP_CONSTANTS} from '../utils/constants';
import {useFilterStore} from '../stores/filterStore';

interface UseGeneViewerSearchProps {
    genomeMeta: GenomeMeta | null;
    setLoading: (loading: boolean) => void;
}

interface UseGeneViewerSearchReturn {
    // Data
    geneResults: any[];
    totalPages: number;

    // UI State
    geneSearchQuery: string;
    sortField: string;
    sortOrder: 'asc' | 'desc';

    // Actions
    setGeneSearchQuery: (query: string) => void;
    handleGeneSearch: () => Promise<void>;
    handleGeneSortClick: (field: string) => Promise<void>;
}

export const useGeneViewerSearch = ({
                                        genomeMeta,
                                        setLoading,
                                    }: UseGeneViewerSearchProps): UseGeneViewerSearchReturn => {
    // Get filter store actions for URL synchronization
    const setGeneSortField = useFilterStore(state => state.setGeneSortField);
    const setGeneSortOrder = useFilterStore(state => state.setGeneSortOrder);

    // Local state
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [totalPages, setTotalPages] = useState(1);
    const [geneSearchQuery, setGeneSearchQuery] = useState('');
    const [sortField, setSortField] = useState<string>('locus_tag');
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

    const handleGeneSearch = async (): Promise<void> => {
        if (genomeMeta?.isolate_name) {
            try {
                setLoading(true);
                const response = await GeneService.fetchGeneBySearch(genomeMeta.isolate_name, geneSearchQuery);
                setGeneResults(response.data || []);
                setTotalPages(response.pagination?.num_pages || 1);
            } catch (error) {
                console.error('Error searching genes:', error);
            } finally {
                setTimeout(() => setLoading(false), APP_CONSTANTS.SPINNER_DELAY);
            }
        }
    };

    const handleGeneSortClick = async (field: string): Promise<void> => {
        const newSortOrder = sortField === field && sortOrder === 'asc' ? 'desc' : 'asc';
        setSortField(field);
        setSortOrder(newSortOrder);

        // Update filter store for URL synchronization
        setGeneSortField(field);
        setGeneSortOrder(newSortOrder);

        console.log('Geneviewer Sorting Genes by:', {field, order: newSortOrder});

        // Optionally trigger a new search with the updated sort parameters
        // await handleGeneSearch();
    };

    return {
        // Data
        geneResults,
        totalPages,

        // UI State
        geneSearchQuery,
        sortField,
        sortOrder,

        // Actions
        setGeneSearchQuery,
        handleGeneSearch,
        handleGeneSortClick,
    };
}; 