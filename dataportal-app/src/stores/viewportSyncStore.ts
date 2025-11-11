import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export type ChangeSource = 'jbrowse' | 'sync-table' | 'search-table' | null

export interface ViewMeta {
  refName: string
  assemblyName?: string
  bpPerPx?: number
  offsetPx?: number
}

export interface ViewportSyncState {
  // Locus coordinates: chrom:start..end format
  locus: string | null
  // Selected locus tag
  selectedLocusTag: string | null
  // View metadata for debugging/derived logic
  viewMeta: ViewMeta | null
  // Change source to avoid feedback loops
  changeSource: ChangeSource
  // Viewport coordinates
  seqId: string | null
  start: number | null
  end: number | null
  // Flag to indicate viewport has changed (for auto-switching to sync tab)
  viewportChanged: boolean
  // Flag to track if viewport has been initialized (prevents notification on initial load)
  viewportInitialized: boolean
  // Timestamp of last table navigation (to prevent sync updates for a period after table navigation)
  lastTableNavigationTime: number | null
  
  setLocus: (locus: string | null) => void
  setSelectedLocusTag: (locusTag: string | null) => void
  setViewMeta: (viewMeta: ViewMeta | null) => void
  setChangeSource: (source: ChangeSource) => void
  setViewport: (seqId: string | null, start: number | null, end: number | null, source?: ChangeSource) => void
  setViewportChanged: (changed: boolean) => void
  setViewportInitialized: (initialized: boolean) => void
  setLastTableNavigationTime: (timestamp: number | null) => void
  reset: () => void
}

const initialState = {
  locus: null,
  selectedLocusTag: null,
  viewMeta: null,
  changeSource: null as ChangeSource,
  seqId: null,
  start: null,
  end: null,
  viewportChanged: false,
  viewportInitialized: false,
  lastTableNavigationTime: null,
}

export const useViewportSyncStore = create<ViewportSyncState>()(
  devtools(
    (set) => ({
      ...initialState,
      setLocus: (locus) => set({ locus }),
      setSelectedLocusTag: (locusTag) => set({ selectedLocusTag: locusTag }),
      setViewMeta: (viewMeta) => set({ viewMeta }),
      setChangeSource: (source) => set({ changeSource: source }),
      setViewport: (seqId, start, end, source = 'jbrowse') => {
        const locus = seqId && start !== null && end !== null 
          ? `${seqId}:${start}..${end}` 
          : null
        set({ 
          seqId, 
          start, 
          end, 
          locus,
          changeSource: source
        })
      },
      setViewportChanged: (changed) => set({ viewportChanged: changed }),
      setViewportInitialized: (initialized) => set({ viewportInitialized: initialized }),
      setLastTableNavigationTime: (timestamp) => set({ lastTableNavigationTime: timestamp }),
      reset: () => set(initialState),
    }),
    { name: 'viewport-sync-store' }
  )
)

