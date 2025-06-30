import { useEffect } from 'react'
import { useUrlState } from './useUrlState'
import { useFilterStore } from '../stores/filterStore'
import { syncUrlToStore, syncStoreToUrl, DEFAULT_URL_SYNC_CONFIG } from '../utils/urlSync'

export const useGeneViewerUrlSync = () => {
  const { searchParams, updateUrl } = useUrlState()
  const filterStore = useFilterStore()
  
  // Sync URL to store on mount (only gene-related parameters)
  useEffect(() => {
    // Create a modified config that only syncs gene-related parameters
    const geneViewerConfig = {
      ...DEFAULT_URL_SYNC_CONFIG,
      // We don't want to sync genome-related parameters in gene viewer
      searchParam: 'geneViewerSearch', // Different param name to avoid conflicts
      sortFieldParam: 'geneViewerSortField',
      sortOrderParam: 'geneViewerSortOrder',
    }
    
    syncUrlToStore(searchParams, filterStore, geneViewerConfig)
  }, [])
  
  // Sync store to URL on changes (only gene-related parameters)
  useEffect(() => {
    const updates = syncStoreToUrl(filterStore, DEFAULT_URL_SYNC_CONFIG)
    
    // Only include gene-related parameters in the URL
    const geneViewerUpdates: Record<string, string | string[] | null> = {}
    
    // Include gene search and sort parameters
    if (updates.geneSearch) geneViewerUpdates.geneSearch = updates.geneSearch
    if (updates.geneSortField) geneViewerUpdates.geneSortField = updates.geneSortField
    if (updates.geneSortOrder) geneViewerUpdates.geneSortOrder = updates.geneSortOrder
    
    // Include faceted filters
    if (updates.facetedFilters) geneViewerUpdates.facetedFilters = updates.facetedFilters
    if (updates.facetOperators) geneViewerUpdates.facetOperators = updates.facetOperators
    
    // Include selected genomes (relevant for gene search)
    if (updates.selectedGenomes) geneViewerUpdates.selectedGenomes = updates.selectedGenomes
    
    updateUrl(geneViewerUpdates)
  }, [
    filterStore.geneSearchQuery,
    filterStore.geneSortField,
    filterStore.geneSortOrder,
    filterStore.facetedFilters,
    filterStore.facetOperators,
    filterStore.selectedGenomes,
  ])
} 