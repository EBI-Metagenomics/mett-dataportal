import CustomTrackContainer from './CustomTrackContainer'

export async function overrideTrackContainer() {
  try {
    const module = await import(
      '@jbrowse/plugin-linear-genome-view/dist/LinearGenomeView/components/TracksContainer'
    )

    // Override default export (works in runtime memory, not file system)
    module.default = CustomTrackContainer

    console.log('✅ Patched TrackContainer directly via dynamic import!')
  } catch (err) {
    console.error('❌ Failed to patch TrackContainer:', err)
  }
}
