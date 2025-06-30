import { useEffect } from 'react'
import { useUrlState } from './useUrlState'
import { useFilterStore } from '../stores/filterStore'
import { syncUrlToStore, syncStoreToUrl, GENOME_TAB_URL_CONFIG, GENE_TAB_URL_CONFIG } from '../utils/urlSync'

export const useTabAwareUrlSync = (activeTab: string) => {
  const { searchParams, updateUrl } = useUrlState()
  const filterStore = useFilterStore()
  
  // Sync URL to store on mount based on active tab
  useEffect(() => {
    if (activeTab === 'genomes') {
      // Genome tab
      syncUrlToStore(searchParams, filterStore, GENOME_TAB_URL_CONFIG)
    } else if (activeTab === 'genes') {
      // Gene tab
      syncUrlToStore(searchParams, filterStore, GENE_TAB_URL_CONFIG)
    }
    // Note: proteinsearch tab doesn't sync any parameters to/from URL
  }, [activeTab])
  
  // Sync store to URL on changes based on active tab
  useEffect(() => {
    if (activeTab === 'genomes') {
      // Genome tab - only sync genome-related parameters
      const updates = syncStoreToUrl(filterStore, GENOME_TAB_URL_CONFIG)
      
      const genomeUpdates: Record<string, string | string[] | null> = {}
      
      // Include species and type strains (shared)
      if (updates.species) genomeUpdates.species = updates.species
      if (updates.typeStrains) genomeUpdates.typeStrains = updates.typeStrains
      
      // Include genome search and sort parameters
      if (updates.genomeSearch) genomeUpdates.genomeSearch = updates.genomeSearch
      if (updates.genomeSortField) genomeUpdates.genomeSortField = updates.genomeSortField
      if (updates.genomeSortOrder) genomeUpdates.genomeSortOrder = updates.genomeSortOrder
      
      // Include selected genomes (relevant for genome search)
      if (updates.selectedGenomes) genomeUpdates.selectedGenomes = updates.selectedGenomes
      
      // Always include the tab parameter
      genomeUpdates.tab = 'genomes'
      
      // Replace all URL parameters (don't merge with existing ones)
      replaceUrlParams(genomeUpdates)
    } else if (activeTab === 'genes') {
      // Gene tab - only sync gene-related parameters
      const updates = syncStoreToUrl(filterStore, GENE_TAB_URL_CONFIG)
      
      const geneUpdates: Record<string, string | string[] | null> = {}
      
      // Include species and type strains (shared)
      if (updates.species) geneUpdates.species = updates.species
      if (updates.typeStrains) geneUpdates.typeStrains = updates.typeStrains
      
      // Include gene search and sort parameters
      if (updates.geneSearch) geneUpdates.geneSearch = updates.geneSearch
      if (updates.geneSortField) geneUpdates.geneSortField = updates.geneSortField
      if (updates.geneSortOrder) geneUpdates.geneSortOrder = updates.geneSortOrder
      
      // Include faceted filters (gene-specific)
      if (updates.facetedFilters) geneUpdates.facetedFilters = updates.facetedFilters
      if (updates.facetOperators) geneUpdates.facetOperators = updates.facetOperators
      
      // Include selected genomes (relevant for gene search)
      if (updates.selectedGenomes) geneUpdates.selectedGenomes = updates.selectedGenomes
      
      // Always include the tab parameter
      geneUpdates.tab = 'genes'
      
      // Replace all URL parameters (don't merge with existing ones)
      replaceUrlParams(geneUpdates)
    } else if (activeTab === 'proteinsearch') {
      // Protein search tab - only include the tab parameter, clear all others
      const proteinUpdates: Record<string, string | string[] | null> = {}
      
      // Only include the tab parameter
      proteinUpdates.tab = 'proteinsearch'
      
      // Replace all URL parameters (don't merge with existing ones)
      replaceUrlParams(proteinUpdates)
    }
  }, [
    activeTab,
    filterStore.selectedSpecies,
    filterStore.selectedTypeStrains,
    filterStore.genomeSearchQuery,
    filterStore.genomeSortField,
    filterStore.genomeSortOrder,
    filterStore.geneSearchQuery,
    filterStore.geneSortField,
    filterStore.geneSortOrder,
    filterStore.facetedFilters,
    filterStore.facetOperators,
    filterStore.selectedGenomes,
  ])
  
  // Helper function to replace all URL parameters instead of merging
  const replaceUrlParams = (updates: Record<string, string | string[] | null>) => {
    const newParams = new URLSearchParams()
    
    Object.entries(updates).forEach(([key, value]) => {
      if (value === null) {
        // Skip null values
      } else if (Array.isArray(value)) {
        if (value.length > 0) {
          value.forEach(v => newParams.append(key, v))
        }
      } else {
        newParams.set(key, value)
      }
    })
    
    // Use window.history directly to replace all parameters
    const newUrl = `${window.location.pathname}?${newParams.toString()}`
    window.history.replaceState({}, '', newUrl)
  }
} 