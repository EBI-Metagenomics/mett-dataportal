import { useEffect, useRef, useCallback } from 'react'
import { useViewportSyncStore } from '../stores/viewportSyncStore'
import { VIEWPORT_SYNC_CONSTANTS } from '../utils/gene-viewer'

interface UseJBrowseViewportSyncProps {
  viewState: any
  isolateName: string | null
  debounceMs?: number
  enabled?: boolean
  bufferPercent?: number
}

/**
 * Monitors JBrowse viewport changes and updates the viewport sync store.
 * Computes viewport coordinates from viewport center and updates store with metadata.
 * 
 * @param bufferPercent - Optional buffer percentage to add around viewport (0-1). 
 *                        Defaults to VIEWPORT_SYNC_CONSTANTS.VIEWPORT_BUFFER_PERCENT (0.1).
 *                        Set to 0 to disable buffer.
 */
export const useJBrowseViewportSync = ({
  viewState,
  isolateName,
  debounceMs = VIEWPORT_SYNC_CONSTANTS.VIEWPORT_DEBOUNCE_MS,
  enabled = true,
  bufferPercent = VIEWPORT_SYNC_CONSTANTS.VIEWPORT_BUFFER_PERCENT,
}: UseJBrowseViewportSyncProps) => {
  const { setViewport, setViewMeta } = useViewportSyncStore()
  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastViewportRef = useRef<string | null>(null)

  const updateViewport = useCallback(() => {
    if (!viewState || !enabled) return

    try {
      const session = viewState.session
      if (!session) return

      const views = session.views
      if (!views || views.length === 0) return

      const view = views[0]
      if (!view) return

      const displayedRegions = view.displayedRegions
      if (!displayedRegions || displayedRegions.length === 0) return

      const region = displayedRegions[0]
      if (!region) return

      const refName = region.refName
      const regionStart = region.start
      const regionEnd = region.end

      const bpPerPx = view.bpPerPx || view.volatile?.bpPerPx
      
      let width = VIEWPORT_SYNC_CONSTANTS.DEFAULT_VIEWPORT_WIDTH_PX
      if (view.width !== undefined) {
        width = view.width
      } else if (view.volatile?.width !== undefined) {
        width = view.volatile.width
      } else if (view.pxToBp && view.bpToPx) {
        try {
          const testBp = VIEWPORT_SYNC_CONSTANTS.TEST_BP_FOR_WIDTH_ESTIMATION
          const testPx = view.bpToPx(testBp)
          if (testPx > 0) {
            const regionLength = regionEnd - regionStart
            width = Math.floor((regionLength / testBp) * testPx)
          }
        } catch {
          // Use default width
        }
      }
      
      let offsetPx = 0
      if (view.offsetPx !== undefined) {
        offsetPx = view.offsetPx
      } else if (view.volatile?.offsetPx !== undefined) {
        offsetPx = view.volatile.offsetPx
      } else if (typeof view.getOffsetPx === 'function') {
        try {
          offsetPx = view.getOffsetPx() || 0
        } catch {
          // Use default
        }
      }
      
      let start: number = regionStart
      let end: number = regionEnd
      
      if (typeof view.bpToPx === 'function' && typeof view.pxToBp === 'function') {
        try {
          const startBp = view.pxToBp(0)
          const endBp = view.pxToBp(width)
          
          if (startBp !== undefined && endBp !== undefined && startBp < endBp) {
            start = Math.max(regionStart, Math.floor(startBp))
            end = Math.min(regionEnd, Math.floor(endBp))
          } else if (bpPerPx && bpPerPx > 0 && width > 0) {
            const offsetBp = offsetPx * bpPerPx
            const widthBp = width * bpPerPx
            start = Math.max(regionStart, Math.floor(regionStart + offsetBp))
            end = Math.min(regionEnd, Math.floor(start + widthBp))
          }
        } catch {
          if (bpPerPx && bpPerPx > 0 && width > 0) {
            const offsetBp = offsetPx * bpPerPx
            const widthBp = width * bpPerPx
            start = Math.max(regionStart, Math.floor(regionStart + offsetBp))
            end = Math.min(regionEnd, Math.floor(start + widthBp))
          }
        }
      } else if (bpPerPx && bpPerPx > 0 && width > 0) {
        const offsetBp = offsetPx * bpPerPx
        const widthBp = width * bpPerPx
        start = Math.max(regionStart, Math.floor(regionStart + offsetBp))
        end = Math.min(regionEnd, Math.floor(start + widthBp))
      }
      
      if (start > end) {
        [start, end] = [end, start]
      }
      
      const regionLength = regionEnd - regionStart
      const viewportLength = end - start
      
      if (viewportLength > regionLength * VIEWPORT_SYNC_CONSTANTS.LARGE_REGION_THRESHOLD && 
          regionLength > VIEWPORT_SYNC_CONSTANTS.MIN_REGION_LENGTH_FOR_CENTERED_WINDOW) {
        const center = Math.floor((regionStart + regionEnd) / 2)
        const windowPercent = bufferPercent > 0 ? bufferPercent : VIEWPORT_SYNC_CONSTANTS.VIEWPORT_BUFFER_PERCENT
        const windowSize = Math.min(regionLength * windowPercent, 
                                     VIEWPORT_SYNC_CONSTANTS.CENTERED_WINDOW_SIZE_BP)
        start = Math.max(regionStart, Math.floor(center - windowSize / 2))
        end = Math.min(regionEnd, Math.floor(center + windowSize / 2))
      }
      
      if (bufferPercent > 0) {
        const viewportSize = end - start
        const bufferSize = Math.floor(viewportSize * bufferPercent)
        start = Math.max(regionStart, start - bufferSize)
        end = Math.min(regionEnd, end + bufferSize)
      }
      
      if (start > end) {
        [start, end] = [end, start]
      }
      
      if (end - start < VIEWPORT_SYNC_CONSTANTS.MIN_VIEWPORT_SIZE_BP) {
        const center = Math.floor((start + end) / 2)
        const halfSize = VIEWPORT_SYNC_CONSTANTS.MIN_VIEWPORT_SIZE_BP / 2
        start = Math.max(regionStart, center - halfSize)
        end = Math.min(regionEnd, center + halfSize)
      }

      const offsetPxValue = offsetPx || undefined
      const viewportSignature = `${refName}:${start}:${end}:${bpPerPx}:${offsetPx}`

      // Check store state BEFORE creating signature and scheduling update
      // This prevents unnecessary work when navigation is in progress
      const storeStateBeforeUpdate = useViewportSyncStore.getState()
      const currentSourceBeforeUpdate = storeStateBeforeUpdate.changeSource
      const isInCooldownBeforeUpdate = storeStateBeforeUpdate.lastTableNavigationTime !== null &&
        (Date.now() - storeStateBeforeUpdate.lastTableNavigationTime) < VIEWPORT_SYNC_CONSTANTS.TABLE_NAVIGATION_COOLDOWN_MS
      
      // Early return if change source is from table or in cooldown
      // Update lastViewportRef to prevent re-detection on next poll
      if (currentSourceBeforeUpdate === 'sync-table' || currentSourceBeforeUpdate === 'search-table' || isInCooldownBeforeUpdate) {
        // Update lastViewportRef to prevent re-detecting this viewport on next poll
        // This prevents the hook from scheduling updates after changeSource is reset
        lastViewportRef.current = viewportSignature
        return
      }

      if (viewportSignature === lastViewportRef.current) {
        return
      }

      lastViewportRef.current = viewportSignature

      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }

      debounceTimeoutRef.current = setTimeout(() => {
        // Double-check store state in debounced callback to prevent race conditions
        const currentState = useViewportSyncStore.getState()
        const currentSource = currentState.changeSource
        const isInCooldown = currentState.lastTableNavigationTime !== null &&
          (Date.now() - currentState.lastTableNavigationTime) < VIEWPORT_SYNC_CONSTANTS.TABLE_NAVIGATION_COOLDOWN_MS
        
        if (currentSource !== 'sync-table' && currentSource !== 'search-table' && !isInCooldown) {
          const viewportChanged = currentState.seqId !== refName || 
                                   currentState.start !== start || 
                                   currentState.end !== end
          
          if (!currentState.viewportInitialized) {
            useViewportSyncStore.getState().setViewportInitialized(true)
            setViewport(refName, start, end, 'jbrowse')
            setViewMeta({
              refName,
              assemblyName: region.assemblyName,
              bpPerPx,
              offsetPx: offsetPxValue,
            })
          } else {
            setViewport(refName, start, end, 'jbrowse')
            setViewMeta({
              refName,
              assemblyName: region.assemblyName,
              bpPerPx,
              offsetPx: offsetPxValue,
            })
            
            const finalState = useViewportSyncStore.getState()
            const stillInCooldown = finalState.lastTableNavigationTime !== null &&
              (Date.now() - finalState.lastTableNavigationTime) < VIEWPORT_SYNC_CONSTANTS.TABLE_NAVIGATION_COOLDOWN_MS
            
            if (viewportChanged && !stillInCooldown) {
              useViewportSyncStore.getState().setViewportChanged(true)
            }
          }
        }
      }, debounceMs)
    } catch (error) {
      console.warn('Error reading JBrowse viewport:', error)
    }
  }, [viewState, enabled, debounceMs, bufferPercent, setViewport, setViewMeta])

  useEffect(() => {
    if (!viewState || !enabled) return

    const session = viewState.session
    if (!session) return

    const views = session.views
    if (!views || views.length === 0) return

    const view = views[0]
    if (!view) return

    const intervalId = setInterval(updateViewport, VIEWPORT_SYNC_CONSTANTS.VIEWPORT_POLLING_INTERVAL_MS)
    updateViewport()

    return () => {
      clearInterval(intervalId)
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [viewState, enabled, updateViewport])

  useEffect(() => {
    if (isolateName) {
      lastViewportRef.current = null
      updateViewport()
    }
  }, [isolateName, updateViewport])
}

