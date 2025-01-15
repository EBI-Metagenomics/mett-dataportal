import {BaseFeatureDataAdapter} from '@jbrowse/core/data_adapters/BaseAdapter';
import {Observable, of} from 'rxjs';
import PluginManager from '@jbrowse/core/PluginManager'
import {getSubAdapterType} from '@jbrowse/core/data_adapters/dataAdapterCache'

export default class EssentialityAdapter extends BaseFeatureDataAdapter {
    static type = 'EssentialityAdapter';

    constructor(config: any, getSubAdapter?: getSubAdapterType, pluginManager?: PluginManager,) {
        console.log('EssentialityAdapter loading with config:', config);
        super(config, getSubAdapter, pluginManager);
        console.log('EssentialityAdapter loaded with config:', config);
    }

    async getRefNames() {
        console.log('EssentialityAdapter - getRefNames called');
        return [];
    }

    getFeatures(region: any): Observable<any> {
        console.log('EssentialityAdapter - getFeatures called', region);
        return of([]);
    }

    async freeResources() {
        console.log('EssentialityAdapter - freeResources called');
    }
}
