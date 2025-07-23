import {useEffect} from 'react';
import {useLocation} from 'react-router-dom';
import {useFilterStore} from '../stores/filterStore';

export const useGeneViewerUrlSync = () => {
    const location = useLocation();
    const filterStore = useFilterStore();

    // Sync URL to store on mount
    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);

        // Sync gene search query
        const geneSearch = searchParams.get('geneSearch');
        if (geneSearch) {
            filterStore.setGeneSearchQuery(geneSearch);
        }

        // Sync gene sort field
        const geneSortField = searchParams.get('geneSortField');
        if (geneSortField) {
            filterStore.setGeneSortField(geneSortField);
        }

        // Sync gene sort order
        const geneSortOrder = searchParams.get('geneSortOrder') as 'asc' | 'desc';
        if (geneSortOrder && (geneSortOrder === 'asc' || geneSortOrder === 'desc')) {
            filterStore.setGeneSortOrder(geneSortOrder);
        }

        // Sync faceted filters
        const facetedFiltersStr = searchParams.get('facetedFilters');
        if (facetedFiltersStr) {
            try {
                const facetedFilters = JSON.parse(decodeURIComponent(facetedFiltersStr));
                filterStore.setFacetedFilters(facetedFilters);
            } catch (error) {
                console.error('Error parsing faceted filters from URL:', error);
            }
        }

        // Sync facet operators
        const facetOperatorsStr = searchParams.get('facetOperators');
        if (facetOperatorsStr) {
            try {
                const facetOperators = JSON.parse(decodeURIComponent(facetOperatorsStr));
                filterStore.setFacetOperators(facetOperators);
            } catch (error) {
                console.error('Error parsing facet operators from URL:', error);
            }
        }
    }, []); // Only run on mount

    // Sync store to URL on changes
    useEffect(() => {
        const newParams = new URLSearchParams(location.search);

        // Update gene search query
        if (filterStore.geneSearchQuery) {
            newParams.set('geneSearch', filterStore.geneSearchQuery);
        } else {
            newParams.delete('geneSearch');
        }

        // Update gene sort field
        if (filterStore.geneSortField && filterStore.geneSortField !== 'locus_tag') {
            newParams.set('geneSortField', filterStore.geneSortField);
        } else {
            newParams.delete('geneSortField');
        }

        // Update gene sort order
        if (filterStore.geneSortOrder && filterStore.geneSortOrder !== 'asc') {
            newParams.set('geneSortOrder', filterStore.geneSortOrder);
        } else {
            newParams.delete('geneSortOrder');
        }

        // Update faceted filters
        if (Object.keys(filterStore.facetedFilters).length > 0) {
            newParams.set('facetedFilters', encodeURIComponent(JSON.stringify(filterStore.facetedFilters)));
        } else {
            newParams.delete('facetedFilters');
        }

        // Update facet operators
        if (Object.keys(filterStore.facetOperators).length > 0) {
            newParams.set('facetOperators', encodeURIComponent(JSON.stringify(filterStore.facetOperators)));
        } else {
            newParams.delete('facetOperators');
        }

        // Update the URL without triggering a page reload
        const newUrl = `${location.pathname}?${newParams.toString()}`;
        window.history.replaceState({}, '', newUrl);
    }, [
        filterStore.geneSearchQuery,
        filterStore.geneSortField,
        filterStore.geneSortOrder,
        filterStore.facetedFilters,
        filterStore.facetOperators,
        location.pathname
    ]);
}; 