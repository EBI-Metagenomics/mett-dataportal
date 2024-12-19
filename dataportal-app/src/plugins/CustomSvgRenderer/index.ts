import Plugin from '@jbrowse/core/Plugin'
import PluginManager from '@jbrowse/core/PluginManager'
import CustomSvgFeatureRenderer from './CustomSvgFeatureRenderer'
import CustomSvgFeatureRendererConfigSchema from './configSchema'
import ReactComponent from './components/CustomSvgRendering'

export default class CustomSvgFeatureRendererPlugin extends Plugin {
  name = 'CustomSvgFeatureRendererPlugin'

  install(pluginManager: PluginManager) {
    console.log('Installing CustomSvgFeatureRendererPlugin')
    pluginManager.addRendererType(() => {
      console.log('Registering CustomSvgFeatureRenderer')
      return new CustomSvgFeatureRenderer({
        name: 'CustomSvgFeatureRenderer',
        displayName: 'Custom SVG Feature Renderer',
        ReactComponent,
        configSchema: CustomSvgFeatureRendererConfigSchema,
        pluginManager,
      })
    })
  }

  configure() {
    // Empty configure method to satisfy type requirements
  }
}

