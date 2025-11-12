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
  locus: string | null
  selectedLocusTag: string | null
  viewMeta: ViewMeta | null
  changeSource: ChangeSource
  seqId: string | null
  start: number | null
  end: number | null
  viewportChanged: boolean
  viewportInitialized: boolean
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

