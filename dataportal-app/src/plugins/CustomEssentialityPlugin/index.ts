import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import AdapterType from '@jbrowse/core/pluggableElementTypes/AdapterType';
import configSchema from "./configSchema";

export default class CustomEssentialityPlugin extends Plugin {
    name = 'CustomEssentialityPlugin';

    install(pluginManager: PluginManager) {
        // console.log("install called");
        pluginManager.addAdapterType(
            () =>
                new AdapterType({
                    name: 'EssentialityAdapter',
                    displayName: 'Essentiality Adapter',
                    configSchema,
                    getAdapterClass: () =>
                        import('./EssentialityAdapter').then(r => r.default),
                }),
        );
    }
}
