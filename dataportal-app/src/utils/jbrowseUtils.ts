import { firstValueFrom } from 'rxjs'
import { filter } from 'rxjs/operators'
import SimpleFeature from '@jbrowse/core/util/simpleFeature'
import { BaseTrackModel } from '@jbrowse/core/pluggableElementTypes/models';
import {ViewModel} from "@jbrowse/react-app2/esm/createModel";


interface FeatureAdapter {
  getFeatures: (args: {
    refName: string
    start: number
    end: number
    assemblyName: string
  }) => ReturnType<typeof import('rxjs').from>
}

export const getFeatureByCoords = async (
  viewState: ViewModel,
  contig: string,
  start: number,
  end: number
): Promise<ReturnType<SimpleFeature['toJSON']> | null> => {
  const view = viewState?.session?.views?.[0]
  if (!view) return null

  const track = view.tracks.find(
    (t: BaseTrackModel) =>
      (t as any).adapter?.constructor?.name === 'EssentialityAdapter'
  ) as BaseTrackModel & { adapter?: FeatureAdapter }

  if (!track?.adapter?.getFeatures) return null

  try {
    const observable = track.adapter.getFeatures({
      refName: contig,
      start,
      end,
      assemblyName: view.assemblyNames?.[0],
    })

    const feature = await firstValueFrom(
      observable.pipe(
        filter((f): f is SimpleFeature => {
          return (
            f instanceof SimpleFeature &&
            f.get('start') === start &&
            f.get('end') === end
          )
        })
      )
    )

    return feature.toJSON()
  } catch (error) {
    console.warn('No matching feature found:', error)
    return null
  }
}