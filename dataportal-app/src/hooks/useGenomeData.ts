import {Dispatch, SetStateAction, useEffect, useState} from 'react';
import {useFilterStore} from '../stores/filterStore';
import {GenomeService} from '../services/genomeService';
import {SpeciesService} from '../services/speciesService';
import {BaseGenome, GenomeMeta} from '../interfaces/Genome';

interface UseGenomeDataReturn {
    // Data
    speciesList: Array<{ acronym: string; scientific_name: string; common_name: string; taxonomy_id: number }>;
    typeStrains: GenomeMeta[];
    genomeResults: any[];
    selectedGenomes: BaseGenome[];

    // UI State
    loading: boolean;
    error: string | null;

    // Actions
    handleSpeciesSelect: (species_acronym: string) => Promise<void>;
    handleTypeStrainToggle: (isolate_name: string) => Promise<void>;
    handleGenomeSearch: (field?: string, order?: 'asc' | 'desc') => Promise<void>;
    handleGenomeSelect: (genome: BaseGenome) => void;
    handleRemoveGenome: (isolate_name: string) => void;
    handleToggleGenomeSelect: (genome: BaseGenome) => void;
    handleGenomeSortClick: (field: string) => Promise<void>;
    setLoading: Dispatch<SetStateAction<boolean>>;
}

export const useGenomeData = (): UseGenomeDataReturn => {
    const filterStore = useFilterStore();

    // Local state
    const [speciesList, setSpeciesList] = useState<Array<{
        acronym: string;
        scientific_name: string;
        common_name: string;
        taxonomy_id: number
    }>>([]);
    const [typeStrains, setTypeStrains] = useState<GenomeMeta[]>([]);
    const [genomeResults, setGenomeResults] = useState<any[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Use selected genomes from global store
    const selectedGenomes = filterStore.selectedGenomes;

    // Fetch species and type strains on mount
    useEffect(() => {
        const fetchInitialData = async () => {
            try {
                setError(null);
                const [species, strains] = await Promise.all([
                    SpeciesService.fetchSpeciesList(),
                    GenomeService.fetchTypeStrains()
                ]);

                setSpeciesList(species || []);
                setTypeStrains(strains || []);
            } catch (err) {
                console.error('Error fetching initial data:', err);
                setError('Failed to load species and type strain data');
            }
        };

        fetchInitialData();
    }, []);

    // Fetch genomes when filters change
    useEffect(() => {
        const fetchGenomes = async () => {
            try {
                setError(null);
                const response = await GenomeService.fetchGenomesBySearch(
                    filterStore.selectedSpecies,
                    filterStore.genomeSearchQuery,
                    filterStore.genomeSortField,
                    filterStore.genomeSortOrder
                );
                setGenomeResults(response.data);
            } catch (err) {
                console.error('Error fetching genomes:', err);
                setError('Failed to load genome data');
            }
        };

        fetchGenomes();
    }, [filterStore.selectedSpecies, filterStore.genomeSearchQuery, filterStore.genomeSortField, filterStore.genomeSortOrder]);

    const handleSpeciesSelect = async (species_acronym: string): Promise<void> => {
        try {
            setLoading(true);
            setError(null);

            const startTime = Date.now();
            let updatedSelectedSpecies: string[];

            if (filterStore.selectedSpecies.includes(species_acronym)) {
                updatedSelectedSpecies = filterStore.selectedSpecies.filter((acronym) => acronym !== species_acronym);
            } else {
                updatedSelectedSpecies = [...filterStore.selectedSpecies, species_acronym];
            }

            filterStore.setSelectedSpecies(updatedSelectedSpecies);

            if (updatedSelectedSpecies.length === 0) {
                filterStore.setSelectedTypeStrains([]);
            } else {
                const validTypeStrains = typeStrains.filter((strain) =>
                    updatedSelectedSpecies.includes(strain.species_acronym)
                );

                const updatedSelectedTypeStrains = filterStore.selectedTypeStrains.filter((isolate_name) =>
                    validTypeStrains.some((strain) => strain.isolate_name === isolate_name)
                );

                filterStore.setSelectedTypeStrains(updatedSelectedTypeStrains);

                if (updatedSelectedTypeStrains.length > 0) {
                    const filteredResults = (genomeResults || []).filter((result) =>
                        updatedSelectedTypeStrains.includes(result.strain_id)
                    );
                    setGenomeResults(filteredResults);
                } else {
                    await handleGenomeSearch();
                }
            }

            // Ensure minimum loading time for better UX
            const elapsedTime = Date.now() - startTime;
            const remainingTime = Math.max(0, 500 - elapsedTime); // 500ms minimum

            setTimeout(() => setLoading(false), remainingTime);
        } catch (err) {
            console.error('Error in species selection:', err);
            setError('Failed to update species selection');
            setLoading(false);
        }
    };

    const handleTypeStrainToggle = async (isolate_name: string): Promise<void> => {
        try {
            setLoading(true);
            setError(null);

            const startTime = Date.now();
            let updatedSelectedTypeStrains: string[];

            if (filterStore.selectedTypeStrains.includes(isolate_name)) {
                updatedSelectedTypeStrains = filterStore.selectedTypeStrains.filter((id) => id !== isolate_name);
            } else {
                updatedSelectedTypeStrains = [...filterStore.selectedTypeStrains, isolate_name];
            }

            filterStore.setSelectedTypeStrains(updatedSelectedTypeStrains);

            if (updatedSelectedTypeStrains.length > 0) {
                const filteredResults = (genomeResults || []).filter((result) =>
                    updatedSelectedTypeStrains.includes(result.strain_id)
                );
                setGenomeResults(filteredResults);
            } else {
                await handleGenomeSearch();
            }

            // Ensure minimum loading time for better UX
            const elapsedTime = Date.now() - startTime;
            const remainingTime = Math.max(0, 500 - elapsedTime);

            setTimeout(() => setLoading(false), remainingTime);
        } catch (err) {
            console.error('Error in type strain toggle:', err);
            setError('Failed to update type strain selection');
            setLoading(false);
        }
    };

    const handleGenomeSearch = async (field = filterStore.genomeSortField, order = filterStore.genomeSortOrder): Promise<void> => {
        try {
            setError(null);
            const response = await GenomeService.fetchGenomesBySearch(
                filterStore.selectedSpecies,
                filterStore.genomeSearchQuery,
                field,
                order
            );
            setGenomeResults(response.data);
        } catch (err) {
            console.error('Error in genome search:', err);
            setError('Failed to search genomes');
        }
    };

    const handleGenomeSelect = (genome: BaseGenome): void => {
        filterStore.addSelectedGenome(genome);
    };

    const handleRemoveGenome = (isolate_name: string): void => {
        filterStore.removeSelectedGenome(isolate_name);
    };

    const handleToggleGenomeSelect = (genome: BaseGenome): void => {
        if (selectedGenomes.some(g => g.isolate_name === genome.isolate_name)) {
            handleRemoveGenome(genome.isolate_name);
        } else {
            handleGenomeSelect(genome);
        }
    };

    const handleGenomeSortClick = async (field: string): Promise<void> => {
        try {
            const newSortOrder = filterStore.genomeSortField === field && filterStore.genomeSortOrder === 'asc' ? 'desc' : 'asc';
            filterStore.setGenomeSortField(field);
            filterStore.setGenomeSortOrder(newSortOrder);
            await handleGenomeSearch(field, newSortOrder);
        } catch (err) {
            console.error('Error in genome sort:', err);
            setError('Failed to sort genomes');
        }
    };

    return {
        // Data
        speciesList,
        typeStrains,
        genomeResults,
        selectedGenomes,

        // UI State
        loading,
        error,

        // Actions
        handleSpeciesSelect,
        handleTypeStrainToggle,
        handleGenomeSearch,
        handleGenomeSelect,
        handleRemoveGenome,
        handleToggleGenomeSelect,
        handleGenomeSortClick,
        setLoading,
    };
}; 