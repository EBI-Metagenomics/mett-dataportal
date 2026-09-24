import React, {useCallback, useEffect, useMemo, useState} from 'react';
import styles from './GeneFacetedFilter.module.scss';
import {GenomeMeta} from '../../interfaces/Genome';
import {compareTypeStrainIsolates} from '../../utils/common/homePageConstants';

interface GenomeFacetedFilterProps {
    typeStrains: GenomeMeta[];
    selectedTypeStrains: string[];
    selectedSpecies: string[];
    onTypeStrainToggle: (isolate_name: string) => void;
    onClearAll?: () => void;
    showChrome?: boolean;
    initialVisibleCount?: number;
}

const GenomeFacetedFilter: React.FC<GenomeFacetedFilterProps> = ({
    typeStrains,
    selectedTypeStrains,
    selectedSpecies,
    onTypeStrainToggle,
    onClearAll,
    showChrome = true,
    initialVisibleCount = 10,
}) => {
    const [collapsed, setCollapsed] = useState(false);
    const [filterText, setFilterText] = useState('');
    const [visibleCount, setVisibleCount] = useState(initialVisibleCount);

    useEffect(() => {
        setVisibleCount(initialVisibleCount);
    }, [filterText, initialVisibleCount]);

    const selectedCount = selectedTypeStrains.length;

    const visibleStrains = useMemo(() => {
        const search = filterText.trim().toLowerCase();
        const matchingSpecies = (strain: GenomeMeta) =>
            selectedSpecies.length === 0 || selectedSpecies.includes(strain.species_acronym);

        const selected = typeStrains.filter((strain) =>
            selectedTypeStrains.includes(strain.isolate_name)
        );
        const unselected = typeStrains.filter((strain) => {
            if (selectedTypeStrains.includes(strain.isolate_name)) {
                return false;
            }
            if (!matchingSpecies(strain)) {
                return false;
            }
            if (search && !strain.isolate_name.toLowerCase().includes(search)) {
                return false;
            }
            return true;
        });

        return [...selected, ...unselected].sort((left, right) => {
            const leftSelected = selectedTypeStrains.includes(left.isolate_name);
            const rightSelected = selectedTypeStrains.includes(right.isolate_name);
            if (leftSelected !== rightSelected) {
                return leftSelected ? -1 : 1;
            }
            return compareTypeStrainIsolates(left.isolate_name, right.isolate_name);
        });
    }, [typeStrains, selectedTypeStrains, selectedSpecies, filterText]);

    const handleFilterChange = useCallback((text: string) => {
        setFilterText(text);
        setVisibleCount(initialVisibleCount);
    }, [initialVisibleCount]);

    return (
        <div className={styles.facetedFilter}>
            {showChrome && (
                <div className={styles.header}>
                    <h3 className={styles.title}>Filter by Facets</h3>
                    {onClearAll && selectedCount > 0 && (
                        <button
                            type="button"
                            className={styles.clearAllButton}
                            onClick={onClearAll}
                            aria-label="Clear all facet filters"
                            title="Clear all selected facet filters"
                        >
                            Clear all ({selectedCount})
                        </button>
                    )}
                </div>
            )}

            <div className={styles.facetGroup}>
                <h4
                    className={styles.groupTitle}
                    onClick={() => setCollapsed((current) => !current)}
                    style={{cursor: 'pointer'}}
                >
                    {collapsed ? '▸' : '▾'} TYPE STRAINS
                </h4>

                {!collapsed && (
                    <>
                        <input
                            type="text"
                            placeholder="Filter the list"
                            className={styles.searchInput}
                            value={filterText}
                            onChange={(e) => handleFilterChange(e.target.value)}
                            aria-label="Filter type strains"
                        />
                        <ul className={styles.facetList}>
                            {visibleStrains.slice(0, visibleCount).map((strain) => {
                                const isSelected = selectedTypeStrains.includes(strain.isolate_name);
                                const isEnabled =
                                    selectedSpecies.length === 0 ||
                                    selectedSpecies.includes(strain.species_acronym);
                                return (
                                    <li key={strain.isolate_name}>
                                        <label
                                            className={
                                                isEnabled
                                                    ? styles.facetLabel
                                                    : `${styles.facetLabel} ${styles.disabledFacet}`
                                            }
                                        >
                                            <span
                                                className={styles.checkboxVisual}
                                                data-selected={isSelected ? 'true' : 'false'}
                                                aria-hidden="true"
                                            />
                                            <input
                                                type="checkbox"
                                                className={styles.facetCheckbox}
                                                checked={isSelected}
                                                disabled={!isEnabled}
                                                onChange={() => {
                                                    if (isEnabled) {
                                                        onTypeStrainToggle(strain.isolate_name);
                                                    }
                                                }}
                                            />
                                            <span className={styles.facetLabelText}>
                                                {strain.isolate_name}
                                            </span>
                                        </label>
                                    </li>
                                );
                            })}
                        </ul>

                        {visibleCount < visibleStrains.length && (
                            <div className={styles.loadMoreSection}>
                                <button
                                    type="button"
                                    className={styles.loadMoreButton}
                                    onClick={() => setVisibleCount(visibleStrains.length)}
                                >
                                    Show all
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default GenomeFacetedFilter;
