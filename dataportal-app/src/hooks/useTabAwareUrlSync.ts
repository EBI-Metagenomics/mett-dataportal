import {useEffect} from 'react'
import {useUrlState} from './useUrlState'
import {useFilterStore} from '../stores/filterStore'
import {GENE_TAB_URL_CONFIG, GENOME_TAB_URL_CONFIG, syncStoreToUrl, syncUrlToStore} from '../utils/common/urlSync'

export const useTabAwareUrlSync = (activeTab: string) => {
    const {searchParams, updateUrl} = useUrlState()
    const filterStore = useFilterStore()

    useEffect(() => {
        if (activeTab === 'genomes') {
            syncUrlToStore(searchParams, filterStore, GENOME_TAB_URL_CONFIG)
        } else if (activeTab === 'genes') {
            syncUrlToStore(searchParams, filterStore, GENE_TAB_URL_CONFIG)
        }

    }, [activeTab])


    useEffect(() => {
        if (activeTab === 'genomes') {
            const updates = syncStoreToUrl(filterStore, GENOME_TAB_URL_CONFIG)

            const genomeUpdates: Record<string, string | string[] | null> = {}

            if (updates.species) genomeUpdates.species = updates.species
            if (updates.typeStrains) genomeUpdates.typeStrains = updates.typeStrains

            // Include genome search and sort parameters
            if (updates.genomeSearch) genomeUpdates.genomeSearch = updates.genomeSearch
            if (updates.genomeSortField) genomeUpdates.genomeSortField = updates.genomeSortField
            if (updates.genomeSortOrder) genomeUpdates.genomeSortOrder = updates.genomeSortOrder

            if (updates.selectedGenomes) genomeUpdates.selectedGenomes = updates.selectedGenomes

            genomeUpdates.tab = 'genomes'

            replaceUrlParams(genomeUpdates)
        } else if (activeTab === 'genes') {
            const updates = syncStoreToUrl(filterStore, GENE_TAB_URL_CONFIG)

            const geneUpdates: Record<string, string | string[] | null> = {}

            if (updates.species) geneUpdates.species = updates.species
            if (updates.typeStrains) geneUpdates.typeStrains = updates.typeStrains

            if (updates.geneSearch) geneUpdates.geneSearch = updates.geneSearch
            if (updates.geneSortField) geneUpdates.geneSortField = updates.geneSortField
            if (updates.geneSortOrder) geneUpdates.geneSortOrder = updates.geneSortOrder

            if (updates.facetedFilters) geneUpdates.facetedFilters = updates.facetedFilters
            if (updates.facetOperators) geneUpdates.facetOperators = updates.facetOperators

            if (updates.selectedGenomes) geneUpdates.selectedGenomes = updates.selectedGenomes

            geneUpdates.tab = 'genes'

            replaceUrlParams(geneUpdates)
        } else if (activeTab === 'proteinsearch') {
            const proteinUpdates: Record<string, string | string[] | null> = {}

            proteinUpdates.tab = 'proteinsearch'

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

    const replaceUrlParams = (updates: Record<string, string | string[] | null>) => {
        const newParams = new URLSearchParams()

        Object.entries(updates).forEach(([key, value]) => {
            if (value === null) {
            } else if (Array.isArray(value)) {
                if (value.length > 0) {
                    value.forEach(v => newParams.append(key, v))
                }
            } else {
                newParams.set(key, value)
            }
        })

        const newUrl = `${window.location.pathname}?${newParams.toString()}`
        window.history.replaceState({}, '', newUrl)
    }
} 