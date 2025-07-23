import {useEffect} from 'react';
import {useLocation} from 'react-router-dom';
import {useFilterStore} from '../stores/filterStore';

export const usePageCleanup = () => {
    const location = useLocation();
    const filterStore = useFilterStore();

    useEffect(() => {
        if (location.pathname.startsWith('/genome/')) {
            filterStore.setGenomeSearchQuery('');
            filterStore.setGenomeSortField('species');
            filterStore.setGenomeSortOrder('asc');
            filterStore.setGeneSearchQuery('');
            filterStore.setGeneSortField('locus_tag');
            filterStore.setGeneSortOrder('asc');
            filterStore.setFacetedFilters({});
            filterStore.setFacetOperators({});

            const strainName = location.pathname.split('/')[2];
            if (strainName) {
                filterStore.setSelectedGenomes([{
                    isolate_name: strainName,
                    type_strain: false
                }]);
            }
        }
        // Clean up when navigating back to home page
        else if (location.pathname === '/' || location.pathname === '/home') {
            if (location.search.includes('locus_tag')) {
                // Clear any gene viewer specific state
                filterStore.setGeneSearchQuery('');
                filterStore.setGeneSortField('locus_tag');
                filterStore.setGeneSortOrder('asc');
                filterStore.setFacetedFilters({});
                filterStore.setFacetOperators({});
            }
        }
    }, [location.pathname, location.search, filterStore]);
}; 