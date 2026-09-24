import {useEffect, useRef} from 'react'
import {useSearchParams} from 'react-router-dom'
import {useFilterStore} from '../stores/filterStore'
import {GENE_TAB_URL_CONFIG, GENOME_TAB_URL_CONFIG, syncStoreToUrl, syncUrlToStore} from '../utils/common/urlSync'

const configForTab = (tab: string | null) =>
    tab === 'genes' ? GENE_TAB_URL_CONFIG : GENOME_TAB_URL_CONFIG

const toQueryString = (updates: Record<string, string | string[] | null>) => {
    const params = new URLSearchParams()

    Object.entries(updates).forEach(([key, value]) => {
        if (value === null || value === undefined) {
            return
        }
        if (Array.isArray(value)) {
            value.forEach((entry) => params.append(key, entry))
            return
        }
        params.set(key, value)
    })

    return params.toString()
}

/**
 * Homepage tabs share one filter store. The store is the source of truth after
 * the first load: changing tabs must not re-apply an older query string.
 * React Router is updated from the store so back/forward stays in sync.
 */
export const useTabAwareUrlSync = (activeTab: string) => {
    const filterStore = useFilterStore()
    const [searchParams, setSearchParams] = useSearchParams()
    const hasHydratedFromUrl = useRef(false)
    const skipNextUrlRead = useRef(false)
    const isFirstSearchParamsEffect = useRef(true)
    const previousTab = useRef(activeTab)
    const previousSearch = useRef(searchParams.toString())

    if (!hasHydratedFromUrl.current) {
        const initialParams = new URLSearchParams(window.location.search)
        const initialTab = initialParams.get('tab') || activeTab
        syncUrlToStore(initialParams, filterStore, configForTab(initialTab))
        hasHydratedFromUrl.current = true
    }

    useEffect(() => {
        if (isFirstSearchParamsEffect.current) {
            isFirstSearchParamsEffect.current = false
            return
        }
        if (skipNextUrlRead.current) {
            skipNextUrlRead.current = false
            return
        }
        syncUrlToStore(searchParams, filterStore, configForTab(searchParams.get('tab') || activeTab))
        // Only external query changes (back/forward) should rehydrate the store.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams])

    useEffect(() => {
        const searchChanged = previousSearch.current !== searchParams.toString()
        const tabChanged = previousTab.current !== activeTab
        previousSearch.current = searchParams.toString()
        previousTab.current = activeTab

        // A new query arrived while the tab state is unchanged. That is navigation
        // (or the echo of our own write). Leave it for the tab state to follow.
        if (searchChanged && !tabChanged) {
            return
        }

        if (activeTab !== 'genomes' && activeTab !== 'genes') {
            const proteinQuery = toQueryString({tab: 'proteinsearch'})
            if (searchParams.toString() !== proteinQuery) {
                skipNextUrlRead.current = true
                setSearchParams(new URLSearchParams(proteinQuery), {replace: true})
            }
            return
        }

        const updates = syncStoreToUrl(
            filterStore,
            activeTab === 'genes' ? GENE_TAB_URL_CONFIG : GENOME_TAB_URL_CONFIG
        )
        updates.tab = activeTab
        const nextQuery = toQueryString(updates)

        if (nextQuery === searchParams.toString()) {
            return
        }

        skipNextUrlRead.current = true
        setSearchParams(new URLSearchParams(nextQuery), {replace: true})
    }, [
        activeTab,
        filterStore,
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
        searchParams,
        setSearchParams,
    ])
}
