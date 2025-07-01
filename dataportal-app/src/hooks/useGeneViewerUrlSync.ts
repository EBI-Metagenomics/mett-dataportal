import { useEffect } from 'react'
import { useUrlState } from './useUrlState'
import { useFilterStore } from '../stores/filterStore'
import { GENE_TAB_URL_CONFIG } from '../utils/urlSync'

export const useGeneViewerUrlSync = () => {
  const { searchParams, updateUrl } = useUrlState()
  const filterStore = useFilterStore()
  
  // Sync URL to store on mount
  useEffect(() => {
    // Sync gene search query
    const geneSearchQuery = searchParams.get(GENE_TAB_URL_CONFIG.geneSearchParam)
    if (geneSearchQuery) {
      filterStore.setGeneSearchQuery(geneSearchQuery)
    }

    // Sync gene sort field
    const geneSortField = searchParams.get(GENE_TAB_URL_CONFIG.geneSortFieldParam)
    if (geneSortField) {
      filterStore.setGeneSortField(geneSortField)
    }

    // Sync gene sort order
    const geneSortOrder = searchParams.get(GENE_TAB_URL_CONFIG.geneSortOrderParam) as 'asc' | 'desc'
    if (geneSortOrder && (geneSortOrder === 'asc' || geneSortOrder === 'desc')) {
      filterStore.setGeneSortOrder(geneSortOrder)
    }

    // Sync faceted filters
    const facetedFiltersStr = searchParams.get(GENE_TAB_URL_CONFIG.facetedFiltersParam)
    if (facetedFiltersStr) {
      try {
        const facetedFilters = JSON.parse(decodeURIComponent(facetedFiltersStr))
        filterStore.setFacetedFilters(facetedFilters)
      } catch (error) {
        console.error('Error parsing faceted filters from URL:', error)
      }
    }

    // Sync facet operators
    const facetOperatorsStr = searchParams.get(GENE_TAB_URL_CONFIG.facetOperatorsParam)
    if (facetOperatorsStr) {
      try {
        const facetOperators = JSON.parse(decodeURIComponent(facetOperatorsStr))
        filterStore.setFacetOperators(facetOperators)
      } catch (error) {
        console.error('Error parsing facet operators from URL:', error)
      }
    }
  }, []) // Only run on mount
  
  // Sync store to URL on changes
  useEffect(() => {
    const updates: Record<string, string | string[] | null> = {}
    
    // Include gene search and sort parameters
    if (filterStore.geneSearchQuery) {
      updates[GENE_TAB_URL_CONFIG.geneSearchParam] = filterStore.geneSearchQuery
    } else {
      updates[GENE_TAB_URL_CONFIG.geneSearchParam] = null
    }
    
    if (filterStore.geneSortField !== GENE_TAB_URL_CONFIG.defaultSortField) {
      updates[GENE_TAB_URL_CONFIG.geneSortFieldParam] = filterStore.geneSortField
    } else {
      updates[GENE_TAB_URL_CONFIG.geneSortFieldParam] = null
    }
    
    if (filterStore.geneSortOrder !== GENE_TAB_URL_CONFIG.defaultSortOrder) {
      updates[GENE_TAB_URL_CONFIG.geneSortOrderParam] = filterStore.geneSortOrder
    } else {
      updates[GENE_TAB_URL_CONFIG.geneSortOrderParam] = null
    }
    
    // Include faceted filters (gene-specific)
    if (Object.keys(filterStore.facetedFilters).length > 0) {
      updates[GENE_TAB_URL_CONFIG.facetedFiltersParam] = encodeURIComponent(JSON.stringify(filterStore.facetedFilters))
    } else {
      updates[GENE_TAB_URL_CONFIG.facetedFiltersParam] = null
    }
    
    if (Object.keys(filterStore.facetOperators).length > 0) {
      updates[GENE_TAB_URL_CONFIG.facetOperatorsParam] = encodeURIComponent(JSON.stringify(filterStore.facetOperators))
    } else {
      updates[GENE_TAB_URL_CONFIG.facetOperatorsParam] = null
    }
    
    // Update URL with the changes
    updateUrl(updates)
  }, [
    filterStore.geneSearchQuery,
    filterStore.geneSortField,
    filterStore.geneSortOrder,
    filterStore.facetedFilters,
    filterStore.facetOperators,
    updateUrl
  ])
} 