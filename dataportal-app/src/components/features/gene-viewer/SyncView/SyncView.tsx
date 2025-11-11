import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { useViewportSyncStore } from '../../../../stores/viewportSyncStore'
import { GeneService } from '../../../../services/gene'
import { GeneMeta } from '../../../../interfaces/Gene'
import GeneResultsTable from '../GeneResultsHandler/GeneResultsTable'
import { createViewState } from '@jbrowse/react-app2'
import { LinkData } from '../../../../interfaces/Auxiliary'
import styles from './SyncView.module.scss'

type ViewModel = ReturnType<typeof createViewState>

interface SyncViewProps {
  viewState?: ViewModel
  selectedGenomes: Array<{ isolate_name: string; type_strain: boolean }>
  setLoading: React.Dispatch<React.SetStateAction<boolean>>
  onFeatureSelect?: (feature: any) => void
  linkData: LinkData
}

const SyncView: React.FC<SyncViewProps> = ({
  viewState,
  selectedGenomes,
  setLoading,
  onFeatureSelect,
  linkData,
}) => {
  const { seqId, start, end, changeSource, selectedLocusTag, lastTableNavigationTime } = useViewportSyncStore()
  const [results, setResults] = useState<GeneMeta[]>([])
  const [isLoading, setIsLoading] = useState(false)
  
  // Track the last viewport coordinates that were successfully fetched
  // This prevents unnecessary re-fetches when coordinates haven't changed
  const lastFetchedViewportRef = useRef<string | null>(null)
  
  // Track if we're currently fetching to prevent duplicate requests
  const isFetchingRef = useRef(false)
  
  // Track the last time we blocked a fetch due to table navigation
  // This helps prevent race conditions
  const lastBlockedFetchTimeRef = useRef<number | null>(null)

  // Fetch genes in viewport
  // This function assumes all conditions have been checked by the calling effect
  const fetchViewportGenes = useCallback(async () => {
    if (!seqId || start === null || end === null || selectedGenomes.length === 0) {
      setResults([])
      lastFetchedViewportRef.current = null
      return
    }

    // Create viewport signature
    const viewportSignature = `${seqId}:${start}:${end}`
    
    // Don't fetch if coordinates haven't changed (double-check)
    if (lastFetchedViewportRef.current === viewportSignature && lastFetchedViewportRef.current !== null) {
      return
    }
    
    // Don't fetch if we're already fetching
    if (isFetchingRef.current) {
      return
    }

    try {
      isFetchingRef.current = true
      setIsLoading(true)
      setLoading(true)

      const genomeFilter = selectedGenomes.map((genome) => ({
        isolate_name: genome.isolate_name,
        type_strain: genome.type_strain,
      }))

      const response = await GeneService.fetchGeneSearchResultsAdvanced(
        '', // No query string for viewport sync
        1, // Page 1
        1000, // Large page size to get all genes in viewport (no pagination in sync view)
        'start_position', // Sort by start position
        'asc', // Ascending order
        genomeFilter,
        undefined, // No species filter
        {}, // No facet filters
        {}, // No facet operators
        undefined, // No locus tag
        seqId, // Sequence ID
        start, // Start position
        end // End position
      )

      if (response && response.data) {
        setResults(response.data)
        // Mark this viewport as successfully fetched
        lastFetchedViewportRef.current = viewportSignature
      } else {
        setResults([])
        lastFetchedViewportRef.current = viewportSignature
      }
    } catch (error) {
      console.error('Error fetching viewport genes:', error)
      setResults([])
      // Don't update lastFetchedViewportRef on error - allow retry
    } finally {
      isFetchingRef.current = false
      setIsLoading(false)
      setLoading(false)
    }
  }, [seqId, start, end, selectedGenomes, setLoading])

  // Fetch genes when viewport coordinates change (but only if conditions are met)
  // IMPORTANT: This effect should ONLY trigger on actual viewport coordinate changes from JBrowse scrolling,
  // NOT when clicking Browse from the sync table
  useEffect(() => {
    // Skip if coordinates are not available
    if (!seqId || start === null || end === null || selectedGenomes.length === 0) {
      return
    }

    // Get current store state FIRST to check conditions before any other logic
    // This is critical to prevent fetches when clicking Browse from sync table
    const storeState = useViewportSyncStore.getState()
    const currentChangeSource = storeState.changeSource
    const currentLastNavTime = storeState.lastTableNavigationTime
    
    // CRITICAL: Don't fetch if change source is from a table click (sync-table or search-table)
    // This prevents refresh when clicking Browse from sync table
    // Check this FIRST - this is the most important check
    if (currentChangeSource === 'sync-table' || currentChangeSource === 'search-table') {
      // Mark that we blocked a fetch due to table navigation
      lastBlockedFetchTimeRef.current = Date.now()
      // Don't proceed with fetch
      return
    }
    
    // Don't fetch if we're in cooldown period after table navigation
    // This provides additional protection even if changeSource gets reset early
    const TABLE_NAVIGATION_COOLDOWN_MS = 5000
    const isInCooldown = currentLastNavTime !== null &&
      (Date.now() - currentLastNavTime) < TABLE_NAVIGATION_COOLDOWN_MS
    
    if (isInCooldown) {
      // Mark that we blocked a fetch due to cooldown
      lastBlockedFetchTimeRef.current = Date.now()
      // Don't proceed with fetch
      return
    }
    
    // Additional safety: if we recently blocked a fetch due to table navigation,
    // don't fetch for a short period to prevent race conditions
    // This handles edge cases where changeSource might be reset but cooldown hasn't fully expired
    const RECENT_BLOCK_WINDOW_MS = 1000 // 1 second safety window
    if (lastBlockedFetchTimeRef.current !== null &&
        (Date.now() - lastBlockedFetchTimeRef.current) < RECENT_BLOCK_WINDOW_MS) {
      return
    }

    // Create viewport signature to check if coordinates actually changed
    const viewportSignature = `${seqId}:${start}:${end}`
    
    // Skip if coordinates haven't changed since last fetch
    // This prevents unnecessary refetches when the effect runs for other reasons
    if (lastFetchedViewportRef.current === viewportSignature) {
      return
    }
    
    // All conditions met - this must be a legitimate viewport change from JBrowse scrolling
    // Clear the blocked fetch time since we're proceeding with a fetch
    lastBlockedFetchTimeRef.current = null
    fetchViewportGenes()
  }, [seqId, start, end, selectedGenomes, fetchViewportGenes, changeSource, lastTableNavigationTime])

  // Handle sort (disabled in sync view, but needed for table component)
  const handleSortClick = useCallback((sortField: string, sortOrder: 'asc' | 'desc') => {
    // Sorting is disabled in sync view - genes are always sorted by start_position
    console.log('Sorting disabled in sync view')
  }, [])

  const hasResults = useMemo(() => results.length > 0, [results.length])

  if (!seqId || start === null || end === null) {
    return (
      <div className={styles.syncViewEmpty}>
        <p>Navigate in the genome viewer to see genes in the current viewport.</p>
      </div>
    )
  }

  return (
    <div className={styles.syncView}>
      <div className={styles.syncViewHeader}>
        <h3>Genes in Viewport</h3>
        <p className={styles.viewportInfo}>
          Showing genes in {seqId}:{start.toLocaleString()}..{end.toLocaleString()}
        </p>
        <p className={styles.syncViewNote}>
          This view automatically updates as you scroll the genome viewer. 
          No pagination or sorting available.
        </p>
      </div>

      {hasResults ? (
        <div className={styles.syncViewTable}>
          <GeneResultsTable
            results={results}
            onSortClick={handleSortClick}
            linkData={linkData}
            viewState={viewState}
            setLoading={setLoading}
            isTypeStrainAvailable={selectedGenomes.some((g) => g.type_strain)}
            sortField="start_position"
            sortOrder="asc"
            onFeatureSelect={onFeatureSelect}
            highlightedLocusTag={selectedLocusTag || undefined}
            tableSource="sync-table"
          />
        </div>
      ) : (
        <div className={styles.syncViewEmpty}>
          {isLoading ? (
            <p>Loading genes in viewport...</p>
          ) : (
            <p>No genes found in the current viewport.</p>
          )}
        </div>
      )}
    </div>
  )
}

export default SyncView

