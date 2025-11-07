import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import AdapterType from '@jbrowse/core/pluggableElementTypes/AdapterType';
import configSchema from "./configSchema";
import {getColorForEssentiality} from '../../utils/common/geneUtils';

export default class EnhancedGeneFeaturePlugin extends Plugin {
    name = 'EnhancedGeneFeaturePlugin';

    install(pluginManager: PluginManager) {

        // const { jexl } = pluginManager.jexl;
        pluginManager.jexl.addFunction('getColorForEssentiality', getColorForEssentiality);
        
        // Add function to get selected gene ID for highlighting
        pluginManager.jexl.addFunction('selectedGeneId', () => {
            return (typeof window !== 'undefined' && (window as typeof window & { selectedGeneId?: string }).selectedGeneId) || null;
        });
        
        // Add function to get gene color with highlighting support
        pluginManager.jexl.addFunction('getGeneColor', (feature: any) => {
            const locusTag = feature?.locus_tag || feature?.get?.('locus_tag');
            const selectedId = (typeof window !== 'undefined' && (window as typeof window & { selectedGeneId?: string }).selectedGeneId) || null;
            
            if (selectedId && locusTag === selectedId) {
                return '#aef861'; // Orange for selected gene
            }
            
            const essentiality = feature?.Essentiality || feature?.get?.('Essentiality');
            return getColorForEssentiality(essentiality);
        });

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
