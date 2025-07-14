import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useFilterStore } from '../stores/filterStore';

export const usePageCleanup = () => {
  const location = useLocation();
  const filterStore = useFilterStore();
  
  useEffect(() => {
    // Clean up filter store when navigating to gene viewer page
    if (location.pathname.startsWith('/genome/')) {
      // Reset all search-related state for gene viewer page
      filterStore.setGenomeSearchQuery('');
      filterStore.setGenomeSortField('species');
      filterStore.setGenomeSortOrder('asc');
      filterStore.setGeneSearchQuery('');
      filterStore.setGeneSortField('locus_tag');
      filterStore.setGeneSortOrder('asc');
      filterStore.setFacetedFilters({});
      filterStore.setFacetOperators({});
      
      // Keep only the selected genomes that are relevant for the current genome
      const strainName = location.pathname.split('/')[2]; // Extract strain name from URL
      if (strainName) {
        // Set only the current genome as selected
        filterStore.setSelectedGenomes([{
          isolate_name: strainName,
          type_strain: false
        }]);
      }
    }
    // Clean up when navigating back to home page
    else if (location.pathname === '/' || location.pathname === '/home') {
      // Don't reset everything here - let the tab-aware URL sync handle it
      // Just ensure we don't have stale gene viewer state
      if (location.search.includes('locus_tag')) {
        // If we have locus_tag in URL, we're coming from gene viewer
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