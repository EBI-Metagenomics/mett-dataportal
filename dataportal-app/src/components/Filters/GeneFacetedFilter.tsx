import React, {useEffect, useState} from 'react';
import styles from './GeneFacetedFilter.module.scss';
import {GeneFacetResponse} from "../../interfaces/Gene";
import {FacetItem} from "../../interfaces/Auxiliary";

interface GeneFacetedFilterProps {
    facets: GeneFacetResponse;
    onToggleFacet: (facetGroup: string, value: string) => void;
    initialVisibleCount?: number;
    loadMoreStep?: number;
}

const GeneFacetedFilter: React.FC<GeneFacetedFilterProps> = ({
                                                                 facets,
                                                                 onToggleFacet,
                                                                 initialVisibleCount = 10,
                                                                 loadMoreStep = 10,
                                                             }) => {
    // Track how many visible items per group and filter text
    const [visibleCount, setVisibleCount] = useState<Record<string, number>>({});
    const [filterText, setFilterText] = useState<Record<string, string>>({});
    const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

    useEffect(() => {
        const initialCollapsed = Object.entries(facets).reduce((acc, [key, values]) => {
            if (key !== 'total_hits' && Array.isArray(values)) {
                const hasSelection = values.some(v => v.selected);
                acc[key] = !hasSelection; // collapse only if nothing selected
            }
            return acc;
        }, {} as Record<string, boolean>);
        setCollapsedGroups(initialCollapsed);
    }, [facets]);


    const handleLoadMore = (group: string, total: number) => {
        setVisibleCount((prev) => ({
            ...prev,
            [group]: Math.min((prev[group] || initialVisibleCount) + loadMoreStep, total),
        }));
    };

    const handleFilterChange = (group: string, text: string) => {
        setFilterText((prev) => ({...prev, [group]: text}));
        // Reset visible count to show from start of filtered results
        setVisibleCount((prev) => ({...prev, [group]: initialVisibleCount}));
    };

    const toggleCollapse = (group: string) => {
        setCollapsedGroups(prev => ({
            ...prev,
            [group]: !prev[group]
        }));
    };


    return (
        <div className={styles.facetedFilter}>
            <h3 className={styles.title}>Filter by Facets</h3>
            {Object.entries(facets).map(([facetGroup, values]) => {
                if (facetGroup === 'total_hits' || !Array.isArray(values)) return null;

                const search = filterText[facetGroup] || '';
                const selected = values.filter(f => f.selected);
                const unselected = values.filter(f => !f.selected && f.value.toLowerCase().includes(search.toLowerCase()));
                const filtered = [...selected, ...unselected];
                const total = filtered.length;
                const showCount = visibleCount[facetGroup] || initialVisibleCount;

                return (
                    <div key={facetGroup} className={styles.facetGroup}>
                        <h4 className={styles.groupTitle} onClick={() => toggleCollapse(facetGroup)}
                            style={{cursor: 'pointer'}}>
                            {facetGroup.replace('_', ' ').toUpperCase()} {collapsedGroups[facetGroup] ? '▸' : '▾'}
                        </h4>

                        {!collapsedGroups[facetGroup] && (
                            <>
                                <input
                                    type="text"
                                    placeholder="Filter the list"
                                    className={styles.searchInput}
                                    value={search}
                                    onChange={(e) => handleFilterChange(facetGroup, e.target.value)}
                                />

                                <ul className={styles.facetList}>
                                    {filtered.slice(0, showCount).map((facet: FacetItem) => (
                                        <li key={facet.value}>
                                            <label className={facet.count === 0 ? styles.disabledFacet : ''}>
                                                <input
                                                    type="checkbox"
                                                    checked={facet.selected}
                                                    onChange={() => onToggleFacet(facetGroup, facet.value)}
                                                />
                                                {facet.value} <span className={styles.countBadge}>{facet.count}</span>
                                            </label>
                                        </li>
                                    ))}
                                </ul>

                                <div className={styles.loadMoreSection}>
                                    <div className={styles.entryNote}>
                                        * Showing {Math.min(showCount, total)} out of {total} entries
                                    </div>
                                    {showCount < total && (
                                        // <button className={`vf-button vf-button--primary vf-button--sm ${styles.loadMoreButton}`} onClick={() => handleLoadMore(facetGroup, total)}>
                                        <button className={`${styles.loadMoreButton}`}
                                                onClick={() => handleLoadMore(facetGroup, total)}>
                                            Load more
                                        </button>
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                );
            })}
        </div>
    );
};

export default GeneFacetedFilter;
