import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import { ConfigurationSchema } from '@jbrowse/core/configuration';
import { types } from 'mobx-state-tree';
import React from 'react';
import { observer } from 'mobx-react';
import PyhmmerFeatureWidget from '../../components/features/pyhmmer/PyhmmerSearchForm/components/PyhmmerFeatureWidget';

// Simple widget that just shows our PyHMMER feature widget
const PyhmmerFeatureWidgetContent = observer(({ model }: { model: any }) => {
    return (
        <div style={{ padding: 8 }}>
            <PyhmmerFeatureWidget model={model} />
        </div>
    );
});

export default class PyhmmerFeaturePlugin extends Plugin {
    name = 'PyhmmerFeaturePlugin';
    
    install(pm: PluginManager) {
        pm.addWidgetType(() => ({
            name: 'PyhmmerFeatureWidget',
            displayName: 'PyHMMER Feature Widget',
            heading: 'PyHMMER Search',
            configSchema: ConfigurationSchema('PyhmmerFeatureWidget', {}),
            stateModel: types.model({}).volatile(() => ({
                featureData: undefined as any,
            })),
            ReactComponent: PyhmmerFeatureWidgetContent,
        }));
    }

    configure(pm: PluginManager) {
        // no-op
    }
}
