import React, {useEffect, useState} from 'react';
import styles from './GeneFacetedFilter.module.scss';
import {GeneFacetResponse} from "../../interfaces/Gene";
import {FacetItem} from "../../interfaces/Auxiliary";
import {ESSENTIALITY_DETERMINATION_TXT, EXT_LINK_ESSENTIALITY_JOURNAL, FACET_ORDER} from "../../utils/appConstants";
import * as Popover from '@radix-ui/react-popover';

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

    const [visibleCount, setVisibleCount] = useState<Record<string, number>>({});
    const [filterText, setFilterText] = useState<Record<string, string>>({});
    const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

    const orderedFacetEntries = Object.entries(facets)
        .filter(([facetGroup, values]) => facetGroup !== 'total_hits' && Array.isArray(values))
        .sort(([a], [b]) => {
            const indexA = FACET_ORDER.indexOf(a);
            const indexB = FACET_ORDER.indexOf(b);

            // Unlisted facets go to the end, sorted alphabetically
            if (indexA === -1 && indexB === -1) return a.localeCompare(b);
            if (indexA === -1) return 1;
            if (indexB === -1) return -1;
            return indexA - indexB;
        });

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
            {orderedFacetEntries.map(([facetGroup, values]) => {
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
                            {facetGroup === 'essentiality' && (
                                <Popover.Root>
                                    <Popover.Trigger asChild>
                                        <button
                                            className={styles.infoIcon}
                                            onClick={(e) => e.stopPropagation()}
                                            aria-label="Essentiality info"
                                        >
                                            ℹ️
                                        </button>
                                    </Popover.Trigger>
                                    <Popover.Portal>
                                        <Popover.Content
                                            className={styles.popoverContent}
                                            side="top"
                                            align="end"
                                            sideOffset={5}
                                        >
                                            <div className={styles.popoverInner}>

                                                <strong>Essentiality determination:</strong><br/>
                                                <p>
                                                    {ESSENTIALITY_DETERMINATION_TXT}
                                                </p>
                                                <p>
                                                    <a target="_blank" rel="noreferrer"
                                                       href={EXT_LINK_ESSENTIALITY_JOURNAL}>
                                                        DeJesus et al. 2015
                                                    </a>

                                                </p>
                                            </div>
                                        </Popover.Content>
                                    </Popover.Portal>
                                </Popover.Root>
                            )}
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
                                                {facet.value.toUpperCase()} <span
                                                className={styles.countBadge}>{facet.count}</span>
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
