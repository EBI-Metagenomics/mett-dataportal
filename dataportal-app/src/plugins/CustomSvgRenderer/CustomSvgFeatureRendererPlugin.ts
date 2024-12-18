import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import CustomSvgFeatureRenderer from './CustomSvgFeatureRenderer';
import { configSchema, ReactComponent } from '@jbrowse/plugin-svg/dist/SvgFeatureRenderer';

export default class CustomSvgFeatureRendererPlugin extends Plugin {
  name = 'CustomSvgFeatureRendererPlugin';

  install(pluginManager: PluginManager) {
    pluginManager.addRendererType(
      () =>
        new CustomSvgFeatureRenderer({
          name: 'CustomSvgFeatureRenderer',
          ReactComponent,
          configSchema,
          pluginManager,
        }),
    );
  }
}
