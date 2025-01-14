import BoxRendererType from '@jbrowse/core/pluggableElementTypes/renderers/BoxRendererType'
import Plugin from '@jbrowse/core/Plugin'
import PluginManager from '@jbrowse/core/PluginManager'
import {
    configSchema as svgFeatureRendererConfigSchema,
    ReactComponent as SvgFeatureRendererReactComponent,
} from './CustomSvgFeatureRenderer'

class CustomSvgFeatureRenderer extends BoxRendererType {
    supportsSVG = true
}

export default class CustomSVGPlugin extends Plugin {
    name = 'CustomSVGPlugin'

    install(pluginManager: PluginManager) {
        pluginManager.addRendererType(
            () =>
                new CustomSvgFeatureRenderer({
                    name: 'CustomSvgFeatureRenderer',
                    ReactComponent: SvgFeatureRendererReactComponent,
                    configSchema: svgFeatureRendererConfigSchema,
                    pluginManager,
                }),
        )
    }
}

export {
    configSchema as svgFeatureRendererConfigSchema,
    ReactComponent as SvgFeatureRendererReactComponent,
} from './CustomSvgFeatureRenderer'
