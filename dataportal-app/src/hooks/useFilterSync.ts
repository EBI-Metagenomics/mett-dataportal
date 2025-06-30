import { useEffect } from 'react'
import { useUrlState } from './useUrlState'
import { useFilterStore } from '../stores/filterStore'
import { syncUrlToStore, syncStoreToUrl, DEFAULT_URL_SYNC_CONFIG } from '../utils/urlSync'

export const useFilterSync = () => {
  const { searchParams, updateUrl } = useUrlState()
  const filterStore = useFilterStore()
  
  // Sync URL to store on mount
  useEffect(() => {
    syncUrlToStore(searchParams, filterStore, DEFAULT_URL_SYNC_CONFIG)
  }, [])
  
  // Sync store to URL on changes
  useEffect(() => {
    const updates = syncStoreToUrl(filterStore, DEFAULT_URL_SYNC_CONFIG)
    updateUrl(updates)
  }, [
    filterStore.selectedSpecies,
    filterStore.selectedTypeStrains,
    filterStore.selectedGenomes,
    filterStore.genomeSearchQuery,
    filterStore.genomeSortField,
    filterStore.genomeSortOrder,
    filterStore.geneSearchQuery,
    filterStore.geneSortField,
    filterStore.geneSortOrder,
    filterStore.facetedFilters,
    filterStore.facetOperators,
  ])
} 