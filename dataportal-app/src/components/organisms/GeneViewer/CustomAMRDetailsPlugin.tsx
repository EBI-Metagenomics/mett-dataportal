import Plugin from '@jbrowse/core/Plugin'
import PluginManager from '@jbrowse/core/PluginManager'
import {WidgetType} from '@jbrowse/core/pluggableElementTypes'


export default class CustomAMRDetailsPlugin extends Plugin {
    name = 'CustomAMRDetailsPlugin'

    install(pluginManager: PluginManager) {
        console.log('Installing CustomAMRDetailsPlugin...')

        // Use jbrequire to ensure runtime compatibility
        const {types} = pluginManager.jbrequire('mobx-state-tree')
        const React = pluginManager.jbrequire('react')
        const {ConfigurationSchema} = pluginManager.jbrequire('@jbrowse/core/configuration')
        const {ElementId} = pluginManager.jbrequire(
            '@jbrowse/core/util/types/mst',
        )

        // Define the React component
        const amrFeatureDetails = (props: { featureData: any }) => {
            // eslint-disable-next-line react/prop-types
            const {featureData} = props
            return React.createElement('div', null, [
                React.createElement('h2', null, 'AMR Feature Details'),
                React.createElement('pre', null, JSON.stringify(featureData, null, 2)),
            ])
        }

        // Register the widget
        pluginManager.addWidgetType(() => {
            return new WidgetType({
                name: 'AMRDetailsWidget',
                heading: 'AMR Feature Details',
                configSchema: ConfigurationSchema('AMRDetailsWidget', {}),
                stateModel: types.model('AMRDetailsWidget', {
                    id: ElementId,
                    type: types.literal('AMRDetailsWidget'),
                    featureData: types.frozen(),
                }),
                ReactComponent: amrFeatureDetails,
            })
        })
    }

    configure(pluginManager: PluginManager) {
        console.log('Configuring CustomAMRDetailsPlugin...')
    }
}
