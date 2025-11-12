import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react'
import { useViewportSyncStore } from '../../../../stores/viewportSyncStore'
import { GeneService } from '../../../../services/gene'
import { GeneMeta } from '../../../../interfaces/Gene'
import GeneResultsTable from '../GeneResultsHandler/GeneResultsTable'
import { createViewState } from '@jbrowse/react-app2'
import { LinkData } from '../../../../interfaces/Auxiliary'
import { VIEWPORT_SYNC_CONSTANTS } from '../../../../utils/gene-viewer'
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
  
  const lastFetchedViewportRef = useRef<string | null>(null)
  const isFetchingRef = useRef(false)
  const lastBlockedFetchTimeRef = useRef<number | null>(null)

  const fetchViewportGenes = useCallback(async () => {
    if (!seqId || start === null || end === null || selectedGenomes.length === 0) {
      setResults([])
      lastFetchedViewportRef.current = null
      return
    }

    const viewportSignature = `${seqId}:${start}:${end}`
    
    if (lastFetchedViewportRef.current === viewportSignature && lastFetchedViewportRef.current !== null) {
      return
    }
    
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
        '',
        1,
        VIEWPORT_SYNC_CONSTANTS.SYNC_VIEW_PAGE_SIZE,
        'start_position',
        'asc',
        genomeFilter,
        undefined,
        {},
        {},
        undefined,
        seqId,
        start,
        end
      )

      if (response?.data) {
        setResults(response.data)
        lastFetchedViewportRef.current = viewportSignature
      } else {
        setResults([])
        lastFetchedViewportRef.current = viewportSignature
      }
    } catch (error) {
      console.error('Error fetching viewport genes:', error)
      setResults([])
    } finally {
      isFetchingRef.current = false
      setIsLoading(false)
      setLoading(false)
    }
  }, [seqId, start, end, selectedGenomes, setLoading])

  useEffect(() => {
    if (!seqId || start === null || end === null || selectedGenomes.length === 0) {
      return
    }

    const storeState = useViewportSyncStore.getState()
    const currentChangeSource = storeState.changeSource
    const currentLastNavTime = storeState.lastTableNavigationTime
    
    if (currentChangeSource === 'sync-table' || currentChangeSource === 'search-table') {
      lastBlockedFetchTimeRef.current = Date.now()
      return
    }
    
    const isInCooldown = currentLastNavTime !== null &&
      (Date.now() - currentLastNavTime) < VIEWPORT_SYNC_CONSTANTS.TABLE_NAVIGATION_COOLDOWN_MS
    
    if (isInCooldown) {
      lastBlockedFetchTimeRef.current = Date.now()
      return
    }
    
    if (lastBlockedFetchTimeRef.current !== null &&
        (Date.now() - lastBlockedFetchTimeRef.current) < VIEWPORT_SYNC_CONSTANTS.RECENT_BLOCK_WINDOW_MS) {
      return
    }

    const viewportSignature = `${seqId}:${start}:${end}`
    
    if (lastFetchedViewportRef.current === viewportSignature) {
      return
    }
    
    lastBlockedFetchTimeRef.current = null
    fetchViewportGenes()
  }, [seqId, start, end, selectedGenomes, fetchViewportGenes, changeSource, lastTableNavigationTime])

  const handleSortClick = useCallback(() => {
    // Sorting disabled in sync view
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

