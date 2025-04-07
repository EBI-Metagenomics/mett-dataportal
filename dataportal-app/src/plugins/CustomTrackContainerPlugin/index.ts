import Plugin from '@jbrowse/core/Plugin'
import CustomTrackContainer from './CustomTrackContainer'

export default class CustomTrackContainerPlugin extends Plugin {
  name = 'CustomTrackContainerPlugin'

  install(pluginManager: any) {
    console.log('🧩 Installing CustomTrackContainerPlugin')

    pluginManager.addPostLoadPlugin(() => {
      const plugin = pluginManager.getPlugin('LinearGenomeViewPlugin') as any

      if (plugin?.components?.TrackContainer) {
        plugin.components.TrackContainer = CustomTrackContainer
        console.log('✅ TrackContainer successfully overridden from plugin')
      } else {
        console.warn('⚠️ Could not find TrackContainer to override')
      }
    })
  }
}
