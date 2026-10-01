import React, {useCallback, useLayoutEffect, useMemo, useState} from 'react';
import {createPortal} from 'react-dom';
import ActiveFilters, {ActiveFilterItem} from '@components/Filters/ActiveFilters';
import GeneFacetedFilter from '@components/Filters/GeneFacetedFilter';
import {GeneFacetResponse} from '../../../../interfaces/Gene';
import {useFilterStore} from '../../../../stores/filterStore';
import {buildFacetActiveFilterItems} from '../../../../utils/common/filterUtils';
import {
    FACET_INITIAL_VISIBLE_CNT,
    FACET_STEP_CNT,
} from '../../../../utils/common/constants';
import styles from './GeneSearchForm.module.scss';

interface GeneSearchSidebarProps {
    sidebarPortalId?: string;
    activeSearchLabel: string;
    onClearSearch: () => void;
    facets: GeneFacetResponse;
    onToggleFacet: (facetGroup: string, value: string | boolean) => void;
    onOperatorChange?: (facetGroup: string, operator: 'AND' | 'OR') => void;
    hasActiveFacets: boolean;
    onClearAllFacets?: () => void;
}

const GeneSearchSidebar: React.FC<GeneSearchSidebarProps> = ({
    sidebarPortalId,
    activeSearchLabel,
    onClearSearch,
    facets,
    onToggleFacet,
    onOperatorChange,
    hasActiveFacets,
    onClearAllFacets,
}) => {
    const [sidebarHost, setSidebarHost] = useState<HTMLElement | null>(null);
    const facetedFilters = useFilterStore((state) => state.facetedFilters);

    useLayoutEffect(() => {
        if (!sidebarPortalId) {
            setSidebarHost(null);
            return;
        }
        setSidebarHost(document.getElementById(sidebarPortalId));
    }, [sidebarPortalId]);

    // Homepage rail already owns Active filters; viewer sidebar shows search + facet chips together.
    const activeFilterItems: ActiveFilterItem[] = useMemo(() => {
        if (sidebarPortalId) {
            return [];
        }

        const searchItems: ActiveFilterItem[] = activeSearchLabel
            ? [
                  {
                      id: `gene-search-${activeSearchLabel}`,
                      label: activeSearchLabel,
                      onRemove: onClearSearch,
                  },
              ]
            : [];

        const facetItems = buildFacetActiveFilterItems(facetedFilters).map((item) => ({
            id: item.id,
            label: item.label,
            onRemove: () => onToggleFacet(String(item.facetGroup), item.value),
        }));

        return [...searchItems, ...facetItems];
    }, [activeSearchLabel, facetedFilters, onClearSearch, onToggleFacet, sidebarPortalId]);

    const handleClearAll = useCallback(() => {
        onClearSearch();
        if (hasActiveFacets) {
            onClearAllFacets?.();
        }
    }, [hasActiveFacets, onClearAllFacets, onClearSearch]);

    const content = (
        <>
            <ActiveFilters items={activeFilterItems} onClearAll={handleClearAll} />

            <GeneFacetedFilter
                facets={facets}
                onToggleFacet={onToggleFacet}
                initialVisibleCount={FACET_INITIAL_VISIBLE_CNT}
                loadMoreStep={FACET_STEP_CNT}
                onOperatorChange={onOperatorChange}
                showChrome={false}
            />
        </>
    );

    if (sidebarHost) {
        return createPortal(content, sidebarHost);
    }
    if (sidebarPortalId) {
        return null;
    }
    return <div className={styles.leftPane}>{content}</div>;
};

export default GeneSearchSidebar;
