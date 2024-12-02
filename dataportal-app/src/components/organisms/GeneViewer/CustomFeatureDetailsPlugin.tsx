import Plugin from '@jbrowse/core/Plugin'
import PluginManager from '@jbrowse/core/PluginManager'
import {WidgetType} from '@jbrowse/core/pluggableElementTypes'


export default class CustomFeatureDetailsPlugin extends Plugin {
    name = 'CustomFeatureDetailsPlugin'

    install(pluginManager: PluginManager) {
        console.log('Installing CustomFeatureDetailsPlugin...')

        // Use jbrequire to ensure runtime compatibility
        const {types} = pluginManager.jbrequire('mobx-state-tree')
        const React = pluginManager.jbrequire('react')
        const {ConfigurationSchema} = pluginManager.jbrequire('@jbrowse/core/configuration')
        const {ElementId} = pluginManager.jbrequire(
            '@jbrowse/core/util/types/mst',
        )

        // Define the React component
        const EnhancedFeatureDetails = (props: { featureData: any }) => {
            // eslint-disable-next-line react/prop-types
            const {featureData} = props
            return React.createElement('div', null, [
                React.createElement('h2', null, 'Enhanced Feature Details'),
                React.createElement('pre', null, JSON.stringify(featureData, null, 2)),
            ])
        }

        // Register the widget
        pluginManager.addWidgetType(() => {
            return new WidgetType({
                name: 'EnhancedFeatureDetailsWidget',
                heading: 'Enhanced Feature Details',
                configSchema: ConfigurationSchema('EnhancedFeatureDetailsWidget', {}),
                stateModel: types.model('EnhancedFeatureDetailsWidget', {
                    id: ElementId,
                    type: types.literal('EnhancedFeatureDetailsWidget'),
                    featureData: types.frozen(),
                }),
                ReactComponent: EnhancedFeatureDetails,
            })
        })
    }

    configure(pluginManager: PluginManager) {
        console.log('Configuring CustomFeatureDetailsPlugin...')
    }
}
