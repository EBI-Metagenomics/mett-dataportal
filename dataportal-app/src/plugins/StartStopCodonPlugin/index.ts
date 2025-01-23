import BoxRendererType from '@jbrowse/core/pluggableElementTypes/renderers/BoxRendererType'
import Plugin from '@jbrowse/core/Plugin'
import PluginManager from '@jbrowse/core/PluginManager'
import {
    configSchema as StartStopCodonRendererConfigSchema,
    ReactComponent as StartStopCodonRendererReactComponent,
} from './StartStopCodonRenderer'

class StartStopCodonRenderer extends BoxRendererType {
    supportsSVG = true
}

export default class StartStopCodonPlugin extends Plugin {
    name = 'StartStopCodonPlugin'

    install(pluginManager: PluginManager) {
        pluginManager.addRendererType(
            () =>
                new StartStopCodonRenderer({
                    name: 'StartStopCodonRenderer',
                    ReactComponent: StartStopCodonRendererReactComponent,
                    configSchema: StartStopCodonRendererConfigSchema,
                    pluginManager,
                }),
        )
    }
}

export {
    configSchema as StartStopCodonRendererConfigSchema,
    ReactComponent as StartStopCodonRendererReactComponent,
} from './StartStopCodonRenderer'
