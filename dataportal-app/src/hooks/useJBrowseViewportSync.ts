import { useEffect, useRef, useCallback } from 'react'
import { useViewportSyncStore } from '../stores/viewportSyncStore'

interface UseJBrowseViewportSyncProps {
  viewState: any
  isolateName: string | null
  debounceMs?: number
  enabled?: boolean
}

/**
 * Hook to monitor JBrowse viewport changes and update the viewport sync store
 * Computes anchor coordinate from viewport center and updates store with viewport metadata
 */
export const useJBrowseViewportSync = ({
  viewState,
  isolateName,
  debounceMs = 2000,
  enabled = true,
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

      // Access displayed regions from the view
      const displayedRegions = view.displayedRegions
      if (!displayedRegions || displayedRegions.length === 0) return

      // Get the first displayed region (for single-contig genomes)
      // For multi-contig, we'd need to handle all regions
      const region = displayedRegions[0]
      if (!region) return

      const refName = region.refName
      const regionStart = region.start
      const regionEnd = region.end

      // Get viewport dimensions to calculate visible region
      // Try multiple ways to access view properties (JBrowse API might vary)
      const bpPerPx = view.bpPerPx || view.volatile?.bpPerPx
      
      // Try to get view width from various sources
      let width = 800 // Default width
      if (view.width !== undefined) {
        width = view.width
      } else if (view.volatile?.width !== undefined) {
        width = view.volatile.width
      } else if (view.pxToBp && view.bpToPx) {
        // Estimate width from coordinate conversion functions if available
        try {
          const testBp = 1000
          const testPx = view.bpToPx(testBp)
          if (testPx > 0) {
            // Estimate: if 1000bp = testPx pixels, then viewport in bp = region length
            const regionLength = regionEnd - regionStart
            width = Math.floor((regionLength / testBp) * testPx)
          }
        } catch {
          // Ignore errors, use default
        }
      }
      
      // Get offset - this might be in pixels or base pairs
      // Try to get the actual visible coordinates from JBrowse if available
      let offsetPx = 0
      if (view.offsetPx !== undefined) {
        offsetPx = view.offsetPx
      } else if (view.volatile?.offsetPx !== undefined) {
        offsetPx = view.volatile.offsetPx
      } else if (typeof view.getOffsetPx === 'function') {
        try {
          offsetPx = view.getOffsetPx() || 0
        } catch {
          // Ignore errors
        }
      }
      
      // Try to get visible coordinates directly from view if available
      let start: number = regionStart
      let end: number = regionEnd
      
      // Check if view has methods to get visible coordinates
      if (typeof view.bpToPx === 'function' && typeof view.pxToBp === 'function') {
        try {
          // Try to get the visible bounds using JBrowse's coordinate conversion
          // Get coordinates at viewport edges (0 and width pixels)
          const startPx = 0
          const endPx = width
          const startBp = view.pxToBp(startPx)
          const endBp = view.pxToBp(endPx)
          
          if (startBp !== undefined && endBp !== undefined && startBp < endBp) {
            start = Math.max(regionStart, Math.floor(startBp))
            end = Math.min(regionEnd, Math.floor(endBp))
          } else {
            // Fall back to calculation if method returns invalid values
            if (bpPerPx && bpPerPx > 0 && width > 0) {
              const offsetBp = offsetPx * bpPerPx
              const widthBp = width * bpPerPx
              start = Math.max(regionStart, Math.floor(regionStart + offsetBp))
              end = Math.min(regionEnd, Math.floor(start + widthBp))
            }
          }
        } catch {
          // Fall back to calculation if method fails
          if (bpPerPx && bpPerPx > 0 && width > 0) {
            const offsetBp = offsetPx * bpPerPx
            const widthBp = width * bpPerPx
            start = Math.max(regionStart, Math.floor(regionStart + offsetBp))
            end = Math.min(regionEnd, Math.floor(start + widthBp))
          }
        }
      } else if (bpPerPx && bpPerPx > 0 && width > 0) {
        // Calculate visible viewport based on bpPerPx, width, and offset
        // Visible start = region start + (scroll offset in base pairs)
        // Visible end = visible start + (view width in base pairs)
        const offsetBp = offsetPx * bpPerPx
        const widthBp = width * bpPerPx
        
        start = Math.max(regionStart, Math.floor(regionStart + offsetBp))
        end = Math.min(regionEnd, Math.floor(start + widthBp))
      }
      
      // Ensure start <= end
      if (start > end) {
        const temp = start
        start = end
        end = temp
      }
      
      // If viewport is too large (covers most of the contig), use a centered window
      // This happens on initial load when the entire contig is displayed
      const regionLength = regionEnd - regionStart
      const viewportLength = end - start
      
      // If viewport covers more than 50% of the region, use a centered window around the middle
      if (viewportLength > regionLength * 0.5 && regionLength > 10000) {
        const center = Math.floor((regionStart + regionEnd) / 2)
        // Use 10% of region or 50kb, whichever is smaller
        const windowSize = Math.min(regionLength * 0.1, 50000)
        start = Math.max(regionStart, Math.floor(center - windowSize / 2))
        end = Math.min(regionEnd, Math.floor(center + windowSize / 2))
      }
      
      // Add buffer (10% on each side) to show genes near the viewport edges
      const bufferPercent = 0.1
      const viewportSize = end - start
      const bufferSize = Math.floor(viewportSize * bufferPercent)
      start = Math.max(regionStart, start - bufferSize)
      end = Math.min(regionEnd, end + bufferSize)
      
      // Ensure start <= end after buffer
      if (start > end) {
        const temp = start
        start = end
        end = temp
      }
      
      // Ensure minimum viewport size (at least 1kb)
      if (end - start < 1000) {
        const center = Math.floor((start + end) / 2)
        start = Math.max(regionStart, center - 500)
        end = Math.min(regionEnd, center + 500)
      }

      // Get viewport metadata
      const offsetPxValue = offsetPx || undefined

      // Create viewport signature for change detection
      // Include offsetPx in signature to detect scroll changes
      const viewportSignature = `${refName}:${start}:${end}:${bpPerPx}:${offsetPx}`

      // Only update if viewport actually changed
      if (viewportSignature === lastViewportRef.current) {
        return
      }

      lastViewportRef.current = viewportSignature

      // Clear existing debounce timeout
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }

      // Debounce the viewport update
      debounceTimeoutRef.current = setTimeout(() => {
        // Update viewport in store (only if change source is not from a table to avoid loops)
        // Table sources: 'sync-table', 'search-table'
        // JBrowse source: 'jbrowse' or null
        const currentState = useViewportSyncStore.getState()
        const currentSource = currentState.changeSource
        
        // Check if we're in a cooldown period after table navigation
        // Extended cooldown to prevent sync updates when JBrowse viewport changes after table navigation
        const TABLE_NAVIGATION_COOLDOWN_MS = 5000 // 5 seconds cooldown after table navigation
        const isInCooldown = currentState.lastTableNavigationTime !== null &&
          (Date.now() - currentState.lastTableNavigationTime) < TABLE_NAVIGATION_COOLDOWN_MS
        
        // Don't update if:
        // 1. Change source is from a table (sync-table or search-table)
        // 2. We're in cooldown period after table navigation
        if (currentSource !== 'sync-table' && currentSource !== 'search-table' && !isInCooldown) {
          // Check if viewport actually changed before updating
          const viewportChanged = currentState.seqId !== refName || 
                                   currentState.start !== start || 
                                   currentState.end !== end
          
          // If viewport hasn't been initialized yet, mark it as initialized but don't trigger auto-switch
          // This prevents notifications on initial page load
          if (!currentState.viewportInitialized) {
            useViewportSyncStore.getState().setViewportInitialized(true)
            // Set the viewport but don't trigger viewportChanged flag on first load
            setViewport(refName, start, end, 'jbrowse')
            setViewMeta({
              refName,
              assemblyName: region.assemblyName,
              bpPerPx,
              offsetPx: offsetPxValue,
            })
          } else {
            // Viewport is already initialized, update it normally
            setViewport(refName, start, end, 'jbrowse')
            setViewMeta({
              refName,
              assemblyName: region.assemblyName,
              bpPerPx,
              offsetPx: offsetPxValue,
            })
            
            // Mark viewport as changed to trigger auto-switch (only if it actually changed and not in cooldown)
            // Double-check cooldown here to ensure we don't trigger auto-switch after table navigation
            const finalState = useViewportSyncStore.getState()
            const stillInCooldown = finalState.lastTableNavigationTime !== null &&
              (Date.now() - finalState.lastTableNavigationTime) < TABLE_NAVIGATION_COOLDOWN_MS
            
            if (viewportChanged && !stillInCooldown) {
              useViewportSyncStore.getState().setViewportChanged(true)
            }
          }
        }
      }, debounceMs)
    } catch (error) {
      console.warn('Error reading JBrowse viewport:', error)
    }
  }, [viewState, enabled, debounceMs, setViewport, setViewMeta])

  // Monitor viewport changes
  useEffect(() => {
    if (!viewState || !enabled) return

    // Try to access view and listen to changes
    const session = viewState.session
    if (!session) return

    const views = session.views
    if (!views || views.length === 0) return

    const view = views[0]
    if (!view) return

    // Poll for viewport changes (JBrowse doesn't expose a clean change event)
    // Check more frequently (200ms) to detect scroll changes better
    const intervalId = setInterval(updateViewport, 200)

    // Also update immediately
    updateViewport()

    return () => {
      clearInterval(intervalId)
      if (debounceTimeoutRef.current) {
        clearTimeout(debounceTimeoutRef.current)
      }
    }
  }, [viewState, enabled, updateViewport])

  // Update when isolate name changes
  useEffect(() => {
    if (isolateName) {
      // Reset viewport when genome changes
      lastViewportRef.current = null
      updateViewport()
    }
  }, [isolateName, updateViewport])
}

