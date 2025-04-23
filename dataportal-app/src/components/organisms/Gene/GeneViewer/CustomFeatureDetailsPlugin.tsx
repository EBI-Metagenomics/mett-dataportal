import Plugin from '@jbrowse/core/Plugin';
import PluginManager from '@jbrowse/core/PluginManager';
import React from 'react';

export default class CustomFeatureDetailsPlugin extends Plugin {
    name = 'CustomFeatureDetailsPlugin';

    configure(pluginManager: PluginManager) {
        console.log('Configuring CustomFeatureDetailsPlugin...');

        const widgetType = pluginManager.getWidgetType('BaseFeatureWidget');
        if (widgetType) {
            console.log('Enhancing BaseFeatureWidget...');

            const OriginalReactComponent = widgetType.ReactComponent;

            const EnhancedReactComponent = (props: any) => {
                const linkConfigs = {
                    InterPro: {baseUrl: 'https://www.ebi.ac.uk/interpro/protein/entry/IPR/'},
                    KEGG: {baseUrl: 'https://www.kegg.jp/kegg-bin/show_pathway?'},
                    GO: {baseUrl: 'https://quickgo.org/term/'},
                };

                const createLink = React.useCallback((type: keyof typeof linkConfigs, value: string) => {
                    console.log('333333')
                    const linkConfig = linkConfigs[type];
                    return (
                        <a
                            href={`${linkConfig.baseUrl}${value}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{color: 'blue', textDecoration: 'underline'}}
                        >
                            {value}
                        </a>
                    );
                }, []);

                const processValue = React.useCallback(
                    (value: any): any => {
                        console.log('**orig value', value);

                        // If the value is an array, process each element
                        if (Array.isArray(value)) {
                            console.log('Processing array:', value);
                            return value.map((item) => {
                                if (typeof item === 'string') {
                                    if (/^(IPR\d+)$/.test(item)) {
                                        console.log('Matched InterPro:', item);
                                        return createLink('InterPro', item);
                                    }

                                    if (/^(GO:\d+)$/.test(item)) {
                                        console.log('Matched GO:', item);
                                        return createLink('GO', item);
                                    }
                                }
                                return item; // Return non-matching items unchanged
                            });
                        }

                        // If the value is a string, process it as before
                        if (typeof value === 'string') {
                            if (/^(IPR\d+)$/.test(value)) {
                                console.log('Matched InterPro:', value);
                                return createLink('InterPro', value);
                            }

                            if (/^(GO:\d+)$/.test(value)) {
                                console.log('Matched GO:', value);
                                return createLink('GO', value);
                            }
                        }

                        // Return the original value if no processing is needed
                        console.log('**processed value returned', value);
                        return value;
                    },
                    [createLink]
                );


                const propertiesToProcess = ['interpro', 'go'];

                const processProperty = (obj: any, depth = 0, seen = new WeakSet(), processedKeys = new Set()): any => {
                    const MAX_DEPTH = 10;

                    if (depth > 10 || seen.has(obj)) {
                        console.warn('Skipping circular or deeply nested structure:', obj);
                        return null;
                    }

                    seen.add(obj);

                    // Skip React elements and DOM nodes
                    if (obj.$$typeof || obj instanceof HTMLElement) {
                        return obj;
                    }

                    // Handle mobx-state-tree nodes
                    if (obj.$treenode) {
                        console.warn('Processing mobx-state-tree node:', obj);

                        try {
                            const snapshot = obj.toJSON ? obj.toJSON() : obj.snapshot || {};
                            return processProperty(snapshot, depth + 1, seen, processedKeys);
                        } catch (error) {
                            console.error('Error processing mobx-state-tree node:', error);
                            return {}; // Return an empty object to avoid breaking the process.
                        }
                    }

                    // Track found properties
                    const processedObj: Record<string, any> = {};

                    Object.entries(obj).forEach(([key, value]) => {
                        // Skip keys that are already processed
                        if (processedKeys.has(key)) return;

                        console.log(`Processing key: ${key}, value:`, value);

                        // Mark the key as processed
                        processedKeys.add(key);

                        // Process keys listed in `propertiesToProcess`
                        if (propertiesToProcess.includes(key)) {
                            processedObj[key] = processValue(value);
                            console.log(`Processed key: ${key}`);
                            // console.log(`**** Processed value: ${processedObj[key]}`);
                        } else if (typeof value === 'object' && processedKeys.size < propertiesToProcess.length) {
                            console.log(`ELSE IF Processed key: ${key}`);
                            // Recurse into nested objects only if not all keys are processed
                            processedObj[key] = processProperty(value, depth + 1, seen, processedKeys);
                        } else {
                            console.log(`DEFAULT NOT Processed key: ${key}`);
                            // Assign non-object values directly
                            processedObj[key] = value;
                        }

                        // Stop processing if all required properties are processed
                        if (processedKeys.size === propertiesToProcess.length) {
                            console.log('All properties processed, stopping recursion.');
                            return; // Use `return` to exit `forEach`
                        }
                    });


                    seen.delete(obj); // Clean up the seen set
                    return processedObj;
                };

                const enhancedProps = React.useMemo(() => {
                    const seen = new WeakSet();
                    const newProps = {...props};

                    // Process model, session, and other properties
                    ['model', 'session', 'feature'].forEach(prop => {
                        if (newProps[prop]) {
                            try {
                                const processedKeys = new Set();
                                newProps[prop] = processProperty(newProps[prop], 0, seen, processedKeys);
                            } catch (error) {
                                console.error(`Error processing prop "${prop}":`, error);
                            }
                        }
                    });

                    // Add fallback for undefined or missing fields
                    if (!newProps.model?.formattedFields) {
                        newProps.model.formattedFields = [
                            {
                                key: 'placeholder',
                                value: 'No meaningful data was processed',
                            },
                        ];
                        console.warn('Added placeholder for "formattedFields"');
                    }

                    return newProps;
                }, [props]);

                console.log('Enhanced props:', enhancedProps);

                // Placeholder for debugging
                if (!enhancedProps.model || !enhancedProps.model.formattedFields.length) {
                    return (
                        <div style={{color: 'red', fontWeight: 'bold'}}>
                            Feature details are not available.
                        </div>
                    );
                }

                return <OriginalReactComponent {...enhancedProps} />;
            };

            EnhancedReactComponent.displayName = 'EnhancedBaseFeatureWidget';

            widgetType.ReactComponent = EnhancedReactComponent;
        } else {
            console.error('BaseFeatureWidget not found');
        }
    }
}
