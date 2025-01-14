import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import AdapterType from '@jbrowse/core/pluggableElementTypes/AdapterType';
import essentialityAdapterConfigSchema from './EssentialityAdapter/configSchema';

export default class CustomEssentialityPlugin extends Plugin {
  name = 'CustomEssentialityPlugin';

  install(pluginManager: PluginManager) {
    pluginManager.addAdapterType(
      () =>
        new AdapterType({
          name: 'EssentialityAdapter',
          configSchema: essentialityAdapterConfigSchema,
          getAdapterClass: () =>
            import('./EssentialityAdapter/EssentialityAdapter').then((module) => module.default),
        }),
    );
  }
}
