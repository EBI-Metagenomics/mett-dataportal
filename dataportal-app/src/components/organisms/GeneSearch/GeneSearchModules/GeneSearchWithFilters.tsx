import React, { useState } from 'react';
import GeneSearchForm from '../../GeneSearch/GeneSearchForm/GeneSearchForm';
import EssentialityFilter from '@components/Filters/EssentialityFilter';
import styles from '@components/organisms/GeneSearch/GeneSearchModules/GeneSearchWithFilters.module.scss'

interface GeneSearchWithFiltersProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
    selectedSpecies?: number[];
    results: any[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    sortField: string;
    sortOrder: 'asc' | 'desc';
    selectedGenomes?: any[];
    linkData: any;
    viewState?: any;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const GeneSearchWithFilters: React.FC<GeneSearchWithFiltersProps> = ({
    searchQuery,
    onSearchQueryChange,
    onSearchSubmit,
    selectedSpecies,
    results,
    onSortClick,
    sortField,
    sortOrder,
    selectedGenomes,
    linkData,
    viewState,
    setLoading,
}) => {
    const [essentialityFilter, setEssentialityFilter] = useState<string[]>([]);

    const handleEssentialityFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setEssentialityFilter((prev) =>
            prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value]
        );
    };

    const hasTypeStrains = !!(selectedGenomes && selectedGenomes.some(genome => genome.type_strain));

    return (
        <div className={styles.container}>
            <div className={styles.leftPane}>
                <EssentialityFilter
                    essentialityFilter={essentialityFilter}
                    onEssentialityFilterChange={handleEssentialityFilterChange}
                    hasTypeStrains={hasTypeStrains}
                />
            </div>

            <div className={styles.rightPane}>
                <GeneSearchForm
                    searchQuery={searchQuery}
                    onSearchQueryChange={onSearchQueryChange}
                    onSearchSubmit={() => onSearchSubmit()}
                    selectedSpecies={selectedSpecies}
                    results={results}
                    onSortClick={onSortClick}
                    sortField={sortField}
                    sortOrder={sortOrder}
                    selectedGenomes={selectedGenomes}
                    linkData={linkData}
                    viewState={viewState}
                    essentialityFilter={essentialityFilter}
                    setLoading={setLoading}
                />
            </div>
        </div>
    );
};

export default GeneSearchWithFilters;
