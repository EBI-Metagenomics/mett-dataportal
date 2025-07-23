import React, {useEffect, useState} from 'react';
import styles from './GeneFacetedFilter.module.scss';
import {GeneFacetResponse} from "../../interfaces/Gene";
import {FacetItem} from "../../interfaces/Auxiliary";
import {
    AMR_DETERMINATION_TXT,
    ESSENTIALITY_DETERMINATION_TXT,
    EXT_LINK_AMR_DETERMINATION,
    EXT_LINK_ESSENTIALITY_JOURNAL,
    FACET_ORDER,
    LOGICAL_OPERATOR_FACETS
} from "../../utils/appConstants";
import * as Popover from '@radix-ui/react-popover';
import {MetadataService} from "../../services/metadataService";
import {useFilterStore} from '../../stores/filterStore';

interface GeneFacetedFilterProps {
    facets: GeneFacetResponse;
    onToggleFacet: (facetGroup: string, value: string) => void;
    initialVisibleCount?: number;
    loadMoreStep?: number;
    onOperatorChange?: (facetGroup: string, operator: 'AND' | 'OR') => void;
}

const GeneFacetedFilter: React.FC<GeneFacetedFilterProps> = ({
                                                                 facets,
                                                                 onToggleFacet,
                                                                 initialVisibleCount = 10,
                                                                 loadMoreStep = 10,
                                                                 onOperatorChange,
                                                             }) => {

    const filterStore = useFilterStore();
    const [visibleCount, setVisibleCount] = useState<Record<string, number>>({});
    const [filterText, setFilterText] = useState<Record<string, string>>({});
    const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});
    const [cogCategoryDefs, setCogCategoryDefs] = useState<Record<string, string>>({});
    const [manualCollapsedGroups, setManualCollapsedGroups] = useState<Record<string, boolean>>({});


    const handleOperatorChange = (facetGroup: string, operator: 'AND' | 'OR') => {
        onOperatorChange?.(facetGroup, operator);
    };


    const getFacetLabel = (facetGroup: string, value: string | number | boolean): string => {
        if (facetGroup === 'has_amr_info') {
            return value === true || value === "true" ? "Present" : "Absent";
        }
        return String(value).toUpperCase();
    };


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
                if (!manualCollapsedGroups[key]) {
                    acc[key] = !hasSelection;
                }
            }
            return acc;
        }, {} as Record<string, boolean>);

        setCollapsedGroups(prev => ({...prev, ...initialCollapsed}));

        MetadataService.fetchCOGCategories()
            .then((data) => {
                const mapping = data.reduce((acc: Record<string, string>, item: { code: string, label: string }) => {
                    acc[item.code] = item.label;
                    return acc;
                }, {});
                setCogCategoryDefs(mapping);
            });
    }, [facets, manualCollapsedGroups]);


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
        setManualCollapsedGroups(prev => ({
            ...prev,
            [group]: true
        }));
    };


    return (
        <div className={styles.facetedFilter}>
            <h3 className={styles.title}>Filter by Facets</h3>
            {orderedFacetEntries.map(([facetGroup, values]) => {
                if (facetGroup === 'total_hits' || !Array.isArray(values)) return null;

                const search = filterText[facetGroup] || '';
                const selected = values.filter(f => f.selected);
                const unselected = values.filter(
                    f => !f.selected && String(f.value).toLowerCase().includes(search.toLowerCase())
                );
                const filtered = [...selected, ...unselected];
                const total = filtered.length;
                const showCount = visibleCount[facetGroup] || initialVisibleCount;

                // Determine if this facet group should use OR logic (show all values)
                const isOrMode =
                    facetGroup === 'essentiality' ||
                    facetGroup === 'has_amr_info' ||
                    filterStore.facetOperators[facetGroup as keyof typeof filterStore.facetOperators] === 'OR';

                // Deduplicate by value
                const dedupedFiltered: FacetItem[] = [];
                const seen = new Set();
                for (const facet of filtered) {
                    const key = String(facet.value);
                    if (!seen.has(key)) {
                        // OR mode: show all values (even if count 0 and unselected)
                        // AND mode: only show if count > 0 or selected
                        if (
                            isOrMode ||
                            facet.count > 0 ||
                            facet.selected
                        ) {
                            dedupedFiltered.push(facet);
                        }
                        seen.add(key);
                    }
                }

                return (
                    <div key={facetGroup} className={styles.facetGroup}>
                        <h4 className={styles.groupTitle} onClick={() => toggleCollapse(facetGroup)}
                            style={{cursor: 'pointer'}}>
                            {collapsedGroups[facetGroup] ? '▸' : '▾'}
                            {' '}
                            {
                                facetGroup === 'has_amr_info'
                                    ? 'AMR'
                                    : facetGroup === 'cog_funcats'
                                        ? 'COG CATEGORIES'
                                        : facetGroup.replace('_', ' ').toUpperCase()
                            }
                            {' '}
                            {facetGroup === 'has_amr_info' && (
                                <Popover.Root>
                                    <Popover.Trigger asChild>
                                        <button
                                            className={styles.infoIcon}
                                            onClick={(e) => e.stopPropagation()}
                                            aria-label="AMR"
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

                                                <strong>AMR:</strong><br/>
                                                <p>
                                                    {AMR_DETERMINATION_TXT}
                                                </p>
                                                <p>
                                                    <a target="_blank" rel="noreferrer"
                                                       href={EXT_LINK_AMR_DETERMINATION}>
                                                        NCBI Antimicrobial Resistance Gene Finder (AMRFinderPlus)
                                                    </a>

                                                </p>
                                            </div>
                                        </Popover.Content>
                                    </Popover.Portal>
                                </Popover.Root>
                            )}

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
                            {facetGroup === 'cog_funcats' && (
                                <Popover.Root>
                                    <Popover.Trigger asChild>
                                        <button
                                            className={styles.infoIcon}
                                            onClick={(e) => e.stopPropagation()}
                                            aria-label="COG category info"
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
                                                <strong>COG Categories:</strong><br/>
                                                <ul style={{
                                                    maxHeight: '200px',
                                                    overflowY: 'auto',
                                                    paddingLeft: '1rem'
                                                }}>
                                                    {Object.entries(cogCategoryDefs).map(([code, label]) => (
                                                        <li key={code}><b>{code}</b>: {label}</li>
                                                    ))}
                                                </ul>
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
                                {LOGICAL_OPERATOR_FACETS.includes(facetGroup) && (
                                    <div className={styles.logicWrapper}>
                                        <input
                                            id={`logic-toggle-${facetGroup}`}
                                            type="checkbox"
                                            className={styles.logicToggleSwitch}
                                            checked={filterStore.facetOperators[facetGroup as keyof typeof filterStore.facetOperators] === 'AND'}
                                            onChange={(e) =>
                                                handleOperatorChange(facetGroup, e.target.checked ? 'AND' : 'OR')
                                            }
                                            aria-label={`Toggle between Match Any and Match All for ${facetGroup}`}
                                        />

                                        <span className={styles.logicText}>of these should be present:</span>
                                    </div>
                                )}

                                <ul className={styles.facetList}>
                                    {dedupedFiltered.slice(0, showCount).map((facet: FacetItem) => (
                                        <li key={facet.value}>
                                            <label className={facet.count === 0 ? styles.disabledFacet : ''}>
                                                <input
                                                    type="checkbox"
                                                    checked={facet.selected}
                                                    onChange={() => onToggleFacet(facetGroup, facet.value)}
                                                />
                                                {getFacetLabel(facetGroup, facet.value)} <span
                                                className={styles.countBadge}>{facet.count}</span>
                                            </label>
                                        </li>
                                    ))}
                                </ul>

                                <div className={styles.loadMoreSection}>
                                    {facetGroup != 'essentiality' && facetGroup != 'has_amr_info' && (
                                        <div className={styles.entryNote}>
                                            * Showing {Math.min(showCount, total)} out of {total} entries
                                        </div>
                                    )}
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
                )
                    ;
            })}
        </div>
    );
};

export default GeneFacetedFilter;
