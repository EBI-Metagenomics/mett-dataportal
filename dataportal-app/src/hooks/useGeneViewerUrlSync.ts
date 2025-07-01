import { useEffect } from 'react'
import { useUrlState } from './useUrlState'
import { useFilterStore } from '../stores/filterStore'

export const useGeneViewerUrlSync = () => {
  const { searchParams, updateUrl } = useUrlState()
  const filterStore = useFilterStore()
  
  // Clear tab-related parameters and reset filter store on mount since we're on gene viewer page
  useEffect(() => {
    // Reset filter store to clean state for gene viewer
    filterStore.setGenomeSearchQuery('');
    filterStore.setGenomeSortField('species');
    filterStore.setGenomeSortOrder('asc');
    filterStore.setGeneSearchQuery('');
    filterStore.setGeneSortField('locus_tag');
    filterStore.setGeneSortOrder('asc');
    filterStore.setFacetedFilters({});
    filterStore.setFacetOperators({});
    
    // Clear URL parameters that shouldn't be on gene viewer page
    const updates: Record<string, string | string[] | null> = {}
    
    // Clear tab-related parameters
    updates.tab = null
    updates.genomeSearch = null
    updates.genomeSortField = null
    updates.genomeSortOrder = null
    
    // Clear gene tab parameters that are not relevant for gene viewer
    updates.geneSearch = null
    updates.geneSortField = null
    updates.geneSortOrder = null
    updates.facetedFilters = null
    updates.facetOperators = null
    
    // Clear species and type strains (not relevant for gene viewer)
    updates.species = null
    updates.typeStrains = null
    updates.selectedGenomes = null
    
    // Keep only the locus_tag parameter which is relevant for gene viewer
    const locusTag = searchParams.get('locus_tag')
    if (locusTag) {
      updates.locus_tag = locusTag
    }
    
    // Update URL to clean up parameters
    updateUrl(updates)
  }, []) // Only run on mount
  
  // Note: We don't sync gene viewer state back to URL since this page
  // is focused on displaying a specific gene/genome, not search functionality
} 