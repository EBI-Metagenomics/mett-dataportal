import React, {useEffect, useMemo, useState} from 'react';
import styles from './GeneFacetedFilter.module.scss';

interface Species {
    acronym: string;
    scientific_name: string;
}

interface SpeciesFilterProps {
    speciesList: Species[];
    selectedSpecies: string[];
    onSpeciesSelect: (acronym: string) => void;
    initialVisibleCount?: number;
}

const SpeciesFilter: React.FC<SpeciesFilterProps> = ({
    speciesList,
    selectedSpecies,
    onSpeciesSelect,
    initialVisibleCount = 5,
}) => {
    const [collapsed, setCollapsed] = useState(false);
    const [filterText, setFilterText] = useState('');
    const [visibleCount, setVisibleCount] = useState(initialVisibleCount);

    useEffect(() => {
        setVisibleCount(initialVisibleCount);
    }, [filterText, initialVisibleCount]);

    const visibleSpecies = useMemo(() => {
        const search = filterText.trim().toLowerCase();
        const matches = (species: Species) =>
            !search ||
            species.scientific_name.toLowerCase().includes(search) ||
            species.acronym.toLowerCase().includes(search);

        const selected = speciesList.filter((species) => selectedSpecies.includes(species.acronym));
        const unselected = speciesList.filter((species) =>
            !selectedSpecies.includes(species.acronym) && matches(species)
        );
        return [...selected, ...unselected];
    }, [speciesList, selectedSpecies, filterText]);

    return (
        <div className={styles.facetGroup}>
            <h4
                className={styles.groupTitle}
                onClick={() => setCollapsed((current) => !current)}
                style={{cursor: 'pointer'}}
            >
                {collapsed ? '▸' : '▾'} SPECIES
            </h4>
            {!collapsed && (
                <>
                    <input
                        type="text"
                        placeholder="Filter the list"
                        className={styles.searchInput}
                        value={filterText}
                        onChange={(event) => setFilterText(event.target.value)}
                        aria-label="Filter species"
                    />
                    <ul className={styles.facetList}>
                        {visibleSpecies.slice(0, visibleCount).map((species) => {
                            const isSelected = selectedSpecies.includes(species.acronym);
                            return (
                                <li key={species.acronym}>
                                    <label className={styles.facetLabel}>
                                        <span
                                            className={styles.checkboxVisual}
                                            data-selected={isSelected ? 'true' : 'false'}
                                            aria-hidden="true"
                                        />
                                        <input
                                            type="checkbox"
                                            className={styles.facetCheckbox}
                                            checked={isSelected}
                                            onChange={() => onSpeciesSelect(species.acronym)}
                                        />
                                        <span className={styles.facetLabelText}>
                                            <i>{species.scientific_name}</i>
                                        </span>
                                    </label>
                                </li>
                            );
                        })}
                    </ul>
                    {visibleCount < visibleSpecies.length && (
                        <div className={styles.loadMoreSection}>
                            <button
                                type="button"
                                className={styles.loadMoreButton}
                                onClick={() => setVisibleCount(visibleSpecies.length)}
                            >
                                Show all
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default SpeciesFilter;
