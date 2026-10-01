import React, {useLayoutEffect, useMemo, useState} from 'react';
import {createPortal} from 'react-dom';
import ActiveFilters, {ActiveFilterItem} from '@components/Filters/ActiveFilters';
import GeneFacetedFilter from '@components/Filters/GeneFacetedFilter';
import {GeneFacetResponse} from '../../../../interfaces/Gene';
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

    useLayoutEffect(() => {
        if (!sidebarPortalId) {
            setSidebarHost(null);
            return;
        }
        setSidebarHost(document.getElementById(sidebarPortalId));
    }, [sidebarPortalId]);

    // Homepage rail already shows Active filters at the top; only viewer sidebar needs the chip.
    const activeSearchItems: ActiveFilterItem[] = useMemo(() => {
        if (!activeSearchLabel || sidebarPortalId) {
            return [];
        }
        return [
            {
                id: `gene-search-${activeSearchLabel}`,
                label: activeSearchLabel,
                onRemove: onClearSearch,
            },
        ];
    }, [activeSearchLabel, onClearSearch, sidebarPortalId]);

    const content = (
        <>
            <ActiveFilters items={activeSearchItems} onClearAll={onClearSearch} />

            <GeneFacetedFilter
                facets={facets}
                onToggleFacet={onToggleFacet}
                initialVisibleCount={FACET_INITIAL_VISIBLE_CNT}
                loadMoreStep={FACET_STEP_CNT}
                onOperatorChange={onOperatorChange}
                onClearAll={hasActiveFacets ? onClearAllFacets : undefined}
                showChrome={!sidebarPortalId}
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
