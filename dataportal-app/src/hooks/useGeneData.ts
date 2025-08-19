import {Dispatch, SetStateAction, useState} from 'react';
import {useFilterStore} from '../stores/filterStore';
import {GenomeService} from '../services/genome';
import {BaseGenome} from '../interfaces/Genome';

interface UseGeneDataReturn {
    // Data
    geneResults: any[];
    selectedGenomes: BaseGenome[];
    loading: boolean;
    error: string | null;
    handleGeneSearch: (field?: string, order?: 'asc' | 'desc') => Promise<void>;
    handleGeneSortClick: (field: string) => Promise<void>;
    handleRemoveGenome: (isolate_name: string) => void;
    setLoading: Dispatch<SetStateAction<boolean>>;
}

export const useGeneData = (): UseGeneDataReturn => {
    const filterStore = useFilterStore();

    // Local state
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Use selected genomes from global store
    const selectedGenomes = filterStore.selectedGenomes;

    const handleGeneSearch = async (field = 'locus_tag', order: 'asc' | 'desc' = 'asc'): Promise<void> => {
        try {
            setError(null);
            const response = await GenomeService.fetchGenomesBySearch(
                filterStore.selectedSpecies,
                filterStore.geneSearchQuery,
                field,
                order
            );
            setGeneResults(response.data);
        } catch (err) {
            console.error('Error in gene search:', err);
            setError('Failed to search genes');
        }
    };

    const handleGeneSortClick = async (field: string): Promise<void> => {
        try {
            const currentOrder = 'asc'; // This could be managed in the store if needed
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            await handleGeneSearch(field, newOrder);
        } catch (err) {
            console.error('Error in gene sort:', err);
            setError('Failed to sort genes');
        }
    };

    const handleRemoveGenome = (isolate_name: string): void => {
        filterStore.removeSelectedGenome(isolate_name);
    };

    return {
        // Data
        geneResults,
        selectedGenomes,

        // UI State
        loading,
        error,

        // Actions
        handleGeneSearch,
        handleGeneSortClick,
        handleRemoveGenome,
        setLoading,
    };
}; 