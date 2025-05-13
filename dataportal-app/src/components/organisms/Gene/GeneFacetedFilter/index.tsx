import React, { useState } from 'react';
import { GeneFacetResponse } from '../../../../interfaces/Gene';
import { FacetItem } from '../../../../interfaces/Auxiliary';
import styles from './GeneFacetedFilter.module.scss';

interface GeneFacetedFilterProps {
    facets: GeneFacetResponse;
    onToggleFacet: (facetGroup: string, value: string) => void;
    initialVisibleCount: number;
    loadMoreStep: number;
    onOperatorChange: (facetGroup: string, operator: 'AND' | 'OR') => void;
}

interface FacetGroupProps {
    facetGroup: string;
    items: FacetItem[];
    visibleCount: number;
    onToggleFacet: (facetGroup: string, value: string) => void;
    onLoadMore: () => void;
    onOperatorChange: (facetGroup: string, operator: 'AND' | 'OR') => void;
}

const FacetGroup: React.FC<FacetGroupProps> = ({
    facetGroup,
    items,
    visibleCount,
    onToggleFacet,
    onLoadMore,
    onOperatorChange,
}) => {
    if (!items || items.length === 0) return null;

    const visibleItems = items.slice(0, visibleCount);

    return (
        <div className={styles.facetGroup}>
            <div className={styles.facetGroupHeader}>
                <h3 className={styles.facetGroupTitle}>{facetGroup}</h3>
                <div className={styles.operatorToggle}>
                    <button
                        onClick={() => onOperatorChange(facetGroup, 'AND')}
                        className={styles.operatorButton}
                    >
                        AND
                    </button>
                    <button
                        onClick={() => onOperatorChange(facetGroup, 'OR')}
                        className={styles.operatorButton}
                    >
                        OR
                    </button>
                </div>
            </div>
            <div className={styles.facetItems}>
                {visibleItems.map((item) => (
                    <div key={item.value} className={styles.facetItem}>
                        <label>
                            <input
                                type="checkbox"
                                checked={item.selected}
                                onChange={() => onToggleFacet(facetGroup, item.value)}
                            />
                            <span className={styles.facetLabel}>
                                {item.value} ({item.count})
                            </span>
                        </label>
                    </div>
                ))}
            </div>
            {items.length > visibleCount && (
                <button
                    className={styles.loadMoreButton}
                    onClick={onLoadMore}
                >
                    Show More
                </button>
            )}
        </div>
    );
};

const GeneFacetedFilter: React.FC<GeneFacetedFilterProps> = ({
    facets,
    onToggleFacet,
    initialVisibleCount,
    loadMoreStep,
    onOperatorChange,
}) => {
    const [visibleCounts, setVisibleCounts] = useState<Record<string, number>>({});

    const handleLoadMore = (facetGroup: string) => {
        setVisibleCounts(prev => ({
            ...prev,
            [facetGroup]: (prev[facetGroup] || initialVisibleCount) + loadMoreStep
        }));
    };

    return (
        <div className={styles.facetedFilter}>
            <h2 className={styles.filterTitle}>Filters</h2>
            {Object.entries(facets).map(([facetGroup, items]) => {
                if (facetGroup === 'total_hits' || facetGroup === 'operators') return null;
                return (
                    <FacetGroup
                        key={facetGroup}
                        facetGroup={facetGroup}
                        items={items as FacetItem[]}
                        visibleCount={visibleCounts[facetGroup] || initialVisibleCount}
                        onToggleFacet={onToggleFacet}
                        onLoadMore={() => handleLoadMore(facetGroup)}
                        onOperatorChange={onOperatorChange}
                    />
                );
            })}
        </div>
    );
};

export default GeneFacetedFilter; 