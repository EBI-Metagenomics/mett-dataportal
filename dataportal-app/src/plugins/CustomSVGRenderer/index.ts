import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import BoxRendererType from '@jbrowse/core/pluggableElementTypes/renderers/BoxRendererType';
import {
    configSchema as customRendererConfigSchema,
    ReactComponent as CustomSvgFeatureRendererReactComponent,
} from './CustomSvgFeatureRenderer';

class CustomSvgFeatureRenderer extends BoxRendererType {
    supportsSVG = true;

    constructor(args: any) {
        super(args);
    }
}

export default class CustomSVGPlugin extends Plugin {
    name = 'CustomSVGPlugin';

    install(pluginManager: PluginManager) {
        pluginManager.addRendererType(
            () =>
                new CustomSvgFeatureRenderer({
                    name: 'CustomSvgFeatureRenderer',
                    ReactComponent: CustomSvgFeatureRendererReactComponent,
                    configSchema: customRendererConfigSchema,
                    pluginManager,
                }),
        );
    }
}

export {
    configSchema as customRendererConfigSchema,
    ReactComponent as CustomSvgFeatureRendererReactComponent,
} from './CustomSvgFeatureRenderer';
