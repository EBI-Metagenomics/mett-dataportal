import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import { ConfigurationSchema } from '@jbrowse/core/configuration';
import { types } from 'mobx-state-tree';
import React from 'react';
import { observer } from 'mobx-react';
import PyHMMERButton from './PyHMMERButton';

// Simple widget that just shows our PyHMMER button
const PyHMMERFeatureWidget = observer(({ model }: { model: any }) => {
    return (
        <div style={{ padding: 8 }}>
            <PyHMMERButton model={model} />
        </div>
    );
});

export default class PyHMMERFeaturePlugin extends Plugin {
    name = 'PyHMMERFeaturePlugin';
    
    install(pm: PluginManager) {
        pm.addWidgetType(() => ({
            name: 'PyHMMERFeatureWidget',
            displayName: 'PyHMMER Feature Widget',
            heading: 'PyHMMER Search',
            configSchema: ConfigurationSchema('PyHMMERFeatureWidget', {}),
            stateModel: types.model({}).volatile(() => ({
                featureData: undefined as any,
            })),
            ReactComponent: PyHMMERFeatureWidget,
        }));
    }

    configure(pm: PluginManager) {
        // no-op
    }
}
