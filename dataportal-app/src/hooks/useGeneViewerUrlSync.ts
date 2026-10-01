import {useEffect, useRef} from 'react';
import {useSearchParams} from 'react-router-dom';
import {useFilterStore} from '../stores/filterStore';

const applyGeneParamsToStore = (
    params: URLSearchParams,
    filterStore: ReturnType<typeof useFilterStore>,
    {clearMissingSearch = false}: {clearMissingSearch?: boolean} = {}
) => {
    const geneSearch = params.get('geneSearch');
    if (geneSearch) {
        filterStore.setGeneSearchQuery(geneSearch);
    } else if (clearMissingSearch && filterStore.geneSearchQuery) {
        filterStore.setGeneSearchQuery('');
    }

    const geneSortField = params.get('geneSortField');
    if (geneSortField) {
        filterStore.setGeneSortField(geneSortField);
    }

    const geneSortOrder = params.get('geneSortOrder') as 'asc' | 'desc' | null;
    if (geneSortOrder === 'asc' || geneSortOrder === 'desc') {
        filterStore.setGeneSortOrder(geneSortOrder);
    }

    const facetedFiltersStr = params.get('facetedFilters');
    if (facetedFiltersStr) {
        try {
            filterStore.setFacetedFilters(JSON.parse(decodeURIComponent(facetedFiltersStr)));
        } catch (error) {
            console.error('Error parsing faceted filters from URL:', error);
        }
    }

    const facetOperatorsStr = params.get('facetOperators');
    if (facetOperatorsStr) {
        try {
            filterStore.setFacetOperators(JSON.parse(decodeURIComponent(facetOperatorsStr)));
        } catch (error) {
            console.error('Error parsing facet operators from URL:', error);
        }
    }
};

/**
 * Keeps gene-viewer search/sort/facet state in the URL so results are shareable,
 * e.g. /genome/BU_ATCC8492?geneSearch=PV_H6-5_03951&geneSortField=locus_tag&geneSortOrder=asc
 */
export const useGeneViewerUrlSync = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const filterStore = useFilterStore();
    const hasHydratedFromUrl = useRef(false);
    const skipNextUrlRead = useRef(false);
    const isFirstStoreWrite = useRef(true);

    // Hydrate synchronously once so the first store→URL write cannot drop geneSearch.
    if (!hasHydratedFromUrl.current) {
        applyGeneParamsToStore(new URLSearchParams(window.location.search), filterStore);
        hasHydratedFromUrl.current = true;
    }

    // Back/forward: re-apply gene params.
    useEffect(() => {
        if (skipNextUrlRead.current) {
            skipNextUrlRead.current = false;
            return;
        }
        if (isFirstStoreWrite.current) {
            return;
        }
        applyGeneParamsToStore(searchParams, filterStore, {clearMissingSearch: true});
        // eslint-disable-next-line react-hooks/exhaustive-deps -- external URL changes only
    }, [searchParams]);

    // Store → URL
    useEffect(() => {
        const next = new URLSearchParams();

        // Preserve deep-link locus_tag when present.
        const locusTag =
            searchParams.get('locus_tag') ||
            new URLSearchParams(window.location.search).get('locus_tag');
        if (locusTag) {
            next.set('locus_tag', locusTag);
        }

        if (filterStore.geneSearchQuery) {
            next.set('geneSearch', filterStore.geneSearchQuery);
        }

        // Always include sort params (matches prior homepage shareable URLs).
        next.set('geneSortField', filterStore.geneSortField || 'locus_tag');
        next.set('geneSortOrder', filterStore.geneSortOrder || 'asc');

        if (Object.keys(filterStore.facetedFilters).length > 0) {
            next.set(
                'facetedFilters',
                encodeURIComponent(JSON.stringify(filterStore.facetedFilters))
            );
        }

        if (Object.keys(filterStore.facetOperators).length > 0) {
            next.set(
                'facetOperators',
                encodeURIComponent(JSON.stringify(filterStore.facetOperators))
            );
        }

        if (next.toString() === searchParams.toString()) {
            isFirstStoreWrite.current = false;
            return;
        }

        skipNextUrlRead.current = true;
        isFirstStoreWrite.current = false;
        setSearchParams(next, {replace: true});
    }, [
        filterStore.geneSearchQuery,
        filterStore.geneSortField,
        filterStore.geneSortOrder,
        filterStore.facetedFilters,
        filterStore.facetOperators,
        searchParams,
        setSearchParams,
    ]);
};
