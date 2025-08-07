import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';

export default class FeaturePanelEnhancerPlugin extends Plugin {
    name = 'FeaturePanelEnhancerPlugin';

    install(pluginManager: PluginManager) {
        console.log('🔧 Installing FeaturePanelEnhancerPlugin...');
        console.log('✅ FeaturePanelEnhancerPlugin installation complete');
    }
}
