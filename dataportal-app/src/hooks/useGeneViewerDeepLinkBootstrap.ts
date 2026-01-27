import { useEffect, useRef } from 'react'
import type { MutableRefObject } from 'react'
import { GeneService } from '../services/gene'
import { useViewportSyncStore } from '../stores/viewportSyncStore'
import { ZOOM_LEVELS } from '../utils/common/constants'
import { GeneMeta } from '../interfaces/Gene'

type ActiveTab = 'search' | 'sync'

interface UseGeneViewerDeepLinkBootstrapArgs {
  viewState: any
  geneMeta: GeneMeta | null
  genomeIsolateName?: string | null
  jbrowseInitKey: number
  setLoading: (loading: boolean) => void
  setSelectedFeature: (feature: any | null) => void

  // UI coordination (kept in page, driven by the hook)
  setActiveTab: (tab: ActiveTab) => void
  setShowAutoSwitchNotification: (show: boolean) => void
  setWasAutoSwitched: (was: boolean) => void
  manualOverrideUntilRef: MutableRefObject<number | null>

  debug?: boolean
}

/**
 * Bootstraps the gene viewer from a deep-link like `?locus_tag=...`.
 * - selects the feature + highlights it (store + window.selectedGeneId)
 * - switches to Genomic Context view
 * - navigates JBrowse to the gene locus once the view is initialized
 *
 * Note: in dev StrictMode, effects can mount+cleanup+remount; we only mark a bootstrap
 * as completed once navigation has actually been invoked on an initialized view.
 */
export function useGeneViewerDeepLinkBootstrap({
  viewState,
  geneMeta,
  genomeIsolateName,
  jbrowseInitKey,
  setLoading,
  setSelectedFeature,
  setActiveTab,
  setShowAutoSwitchNotification,
  setWasAutoSwitched,
  manualOverrideUntilRef,
  debug = false,
}: UseGeneViewerDeepLinkBootstrapArgs) {
  const bootstrapCompletedKeyRef = useRef<string | null>(null)

  useEffect(() => {
    const locusTag = geneMeta?.locus_tag
    if (!viewState || !geneMeta || !locusTag) return

    const isolateName = geneMeta.isolate_name || genomeIsolateName || ''
    const bootstrapKey = `${isolateName}:${locusTag}:${jbrowseInitKey}`

    if (bootstrapCompletedKeyRef.current === bootstrapKey) return

    if (debug) {
      // eslint-disable-next-line no-console
      console.log('[useGeneViewerDeepLinkBootstrap] start', {
        bootstrapKey,
        locusTag,
        isolateName,
        seq_id: geneMeta.seq_id,
        start_position: geneMeta.start_position,
        end_position: geneMeta.end_position,
      })
    }

    // Ensure the Genomic Context view is shown for deep-links to a specific gene,
    // and show the same notification banner used by viewport-driven auto-switching.
    manualOverrideUntilRef.current = null
    setActiveTab('sync')
    setWasAutoSwitched(true)
    setShowAutoSwitchNotification(true)

    // Set highlight + selection for both JBrowse styling and the Genomic Context table.
    try {
      ;(window as any).selectedGeneId = locusTag
    } catch {
      // ignore
    }
    useViewportSyncStore.getState().setSelectedLocusTag(locusTag)

    // Populate Feature Details panel immediately (then enrich with protein sequence async).
    setSelectedFeature(geneMeta)
    GeneService.fetchGeneProteinSeq(locusTag)
      .then((proteinData) => {
        setSelectedFeature({
          ...geneMeta,
          protein_sequence: proteinData?.protein_sequence || '',
        })
      })
      .catch(() => {
        // keep base geneMeta
      })

    const initialView = viewState.session?.views?.[0]
    if (!initialView || typeof initialView.navToLocString !== 'function') {
      if (debug) {
        // eslint-disable-next-line no-console
        console.log('[useGeneViewerDeepLinkBootstrap] view not ready for navigation', {
          hasView: Boolean(initialView),
          navToLocStringType: typeof initialView?.navToLocString,
        })
      }
      return
    }

    let cancelled = false
    const maxRetries = 75
    const retryDelayMs = 200

    const navigateWhenReady = async () => {
      for (let i = 0; i < maxRetries; i++) {
        if (cancelled) return

        const currentView = viewState.session?.views?.[0]
        if (!currentView || typeof currentView.navToLocString !== 'function') {
          await new Promise((resolve) => setTimeout(resolve, retryDelayMs))
          continue
        }

        const initialized = Boolean((currentView as any)?.initialized)

        const geneStart = Number(geneMeta.start_position ?? 0)
        const geneEnd = Number(geneMeta.end_position ?? 0)
        const start = Math.max(0, (Number.isFinite(geneStart) ? geneStart : 0) - 500)
        const endBase = Number.isFinite(geneEnd) && geneEnd > 0 ? geneEnd : start + 1000
        const end = endBase + 500

        if (debug) {
          const displayedRefName =
            currentView.displayedRegions?.[0]?.refName ??
            currentView.volatile?.displayedRegions?.[0]?.refName ??
            null

          // eslint-disable-next-line no-console
          console.log('[useGeneViewerDeepLinkBootstrap] nav attempt', {
            attempt: i + 1,
            initialized,
            displayedRefName,
            targetSeqId: geneMeta.seq_id,
            start,
            end,
            locString: `${geneMeta.seq_id}:${start}..${end}`,
          })
        }

        // Wait until initialized; otherwise navigation can be a no-op.
        if (!initialized) {
          await new Promise((resolve) => setTimeout(resolve, retryDelayMs))
          continue
        }

        setLoading(true)
        try {
          currentView.navToLocString(`${geneMeta.seq_id}:${start}..${end}`)
          bootstrapCompletedKeyRef.current = bootstrapKey

          if (debug) {
            // eslint-disable-next-line no-console
            console.log(
              '[useGeneViewerDeepLinkBootstrap] navToLocString called',
              `${geneMeta.seq_id}:${start}..${end}`,
            )
          }

          setTimeout(() => {
            try {
              currentView.zoomTo(ZOOM_LEVELS.NAV)
              if (debug) {
                // eslint-disable-next-line no-console
                console.log('[useGeneViewerDeepLinkBootstrap] zoomTo called', { zoom: ZOOM_LEVELS.NAV })
              }
            } catch {
              // ignore
            }

            // Force track re-render to apply highlight (window.selectedGeneId).
            try {
              if (currentView.tracks) {
                currentView.tracks.forEach((track: any) => {
                  track?.displays?.forEach((display: any) => {
                    try {
                      if (display.reload) {
                        display.reload()
                      } else if (display.setError) {
                        display.setError(undefined)
                      }
                    } catch {
                      // ignore
                    }
                  })
                })
              }
            } catch {
              // ignore
            }

            setLoading(false)
          }, 200)
        } catch (e) {
          if (debug) {
            // eslint-disable-next-line no-console
            console.log('[useGeneViewerDeepLinkBootstrap] navToLocString threw', e)
          }
          setLoading(false)
          await new Promise((resolve) => setTimeout(resolve, retryDelayMs))
          continue
        }

        return
      }

      if (debug) {
        // eslint-disable-next-line no-console
        console.log('[useGeneViewerDeepLinkBootstrap] giving up after retries', { maxRetries })
      }
    }

    navigateWhenReady()

    return () => {
      cancelled = true
    }
  }, [
    viewState,
    geneMeta,
    genomeIsolateName,
    jbrowseInitKey,
    setLoading,
    setSelectedFeature,
    setActiveTab,
    setShowAutoSwitchNotification,
    setWasAutoSwitched,
    manualOverrideUntilRef,
    debug,
  ])
}

