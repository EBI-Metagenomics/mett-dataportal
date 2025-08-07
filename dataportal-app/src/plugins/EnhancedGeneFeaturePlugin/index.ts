import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import AdapterType from '@jbrowse/core/pluggableElementTypes/AdapterType';
import configSchema from "./configSchema";
import {getColorForEssentiality} from '../../utils/appConstants';

export default class EnhancedGeneFeaturePlugin extends Plugin {
    name = 'EnhancedGeneFeaturePlugin';

    install(pluginManager: PluginManager) {

        // const { jexl } = pluginManager.jexl;
        pluginManager.jexl.addFunction('getColorForEssentiality', getColorForEssentiality);

        // console.log("install called");
        pluginManager.addAdapterType(
            () =>
                new AdapterType({
                    name: 'EnhancedGeneFeatureAdapter',
                    displayName: 'Enhanced Gene Feature Adapter',
                    configSchema,
                    getAdapterClass: () =>
                        import('./EnhancedGeneFeatureAdapter').then(r => r.default),
                }),
        );
    }
}
