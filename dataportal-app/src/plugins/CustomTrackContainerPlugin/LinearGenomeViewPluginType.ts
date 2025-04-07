import type Plugin from '@jbrowse/core/Plugin'

// Extend base Plugin type to include components for LinearGenomeViewPlugin
export interface LinearGenomeViewPluginType extends Plugin {
  components?: {
    TrackContainer?: React.FC<any>
  }
}
