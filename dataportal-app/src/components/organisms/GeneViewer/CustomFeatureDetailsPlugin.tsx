import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import React from 'react';
import externalLinksConfig from './externalLinksConfig';

export default class CustomFeatureDetailsPlugin extends Plugin {
    name = 'CustomFeatureDetailsPlugin';

    configure(pluginManager: PluginManager) {
        console.log('Configuring CustomFeatureDetailsPlugin...');

        const widgetType = pluginManager.getWidgetType('BaseFeatureWidget');
        if (widgetType) {
            console.log('Enhancing BaseFeatureWidget...');

            // Extend ReactComponent with custom links
            const OriginalReactComponent = widgetType.ReactComponent;

            const EnhancedReactComponent = (props: any) => {
                // Log all props to see what's being passed
                console.log('Full props object:', props);
                console.log('Feature prop:', props.feature);
                console.log('Model prop:', props.model);

                // If feature is not directly in props, try extracting from model
                const feature = props.feature || props.model?.featureData;

                // Generate external links with robust error handling
                const links = externalLinksConfig
                    .map(({ label, baseUrl, getValue }) => {
                        try {
                            // Add more detailed logging
                            console.log(`Processing ${label} link`);
                            console.log('Feature for link:', feature);

                            // More flexible value extraction
                            const value = feature
                                ? (getValue(feature) ?? '')
                                : '';

                            if (value) {
                                return (
                                    <a
                                        key={label}
                                        href={`${baseUrl}${value}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        style={{ display: 'block', marginBottom: '5px' }}
                                    >
                                        {`${label}: ${value}`}
                                    </a>
                                );
                            }
                        } catch (error) {
                            console.error(`Error processing ${label} link:`, error);
                        }
                        return null;
                    })
                    .filter(Boolean); // Remove nulls

                // If no feature, show a message
                if (!feature) {
                    return (
                        <div>
                            <OriginalReactComponent {...props} />
                            <p>No feature data available</p>
                        </div>
                    );
                }

                // Render original content with additional links
                return (
                    <div>
                        <OriginalReactComponent {...props} />
                        {links.length > 0 && (
                            <div style={{ marginTop: '1em' }}>
                                <h3>External Links</h3>
                                {links}
                            </div>
                        )}
                    </div>
                );
            };

            // Add displayName to the enhanced component
            EnhancedReactComponent.displayName = 'EnhancedBaseFeatureWidget';

            widgetType.ReactComponent = EnhancedReactComponent;
        } else {
            console.error('BaseFeatureWidget not found');
        }
    }
}