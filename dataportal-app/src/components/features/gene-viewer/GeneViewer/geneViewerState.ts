import {useEffect, useState} from 'react';
import {createViewState} from '@jbrowse/react-app2';
import makeWorkerInstance from '@jbrowse/react-app2/esm/makeWorkerInstance';
import * as CorePlugins from '@jbrowse/core/pluggableElementTypes';
import Plugin from '@jbrowse/core/Plugin';
import EnhancedGeneFeaturePlugin from "../../../../plugins/EnhancedGeneFeaturePlugin";


interface Track {
    type: string;
    trackId: string;
    name: string;
    assemblyNames: string[];
    adapter: {
        type: string;
        [key: string]: any;
    };

    [key: string]: any;
}

type PluginConstructor = new (...args: unknown[]) => Plugin;

function isPluginConstructor(value: unknown): value is typeof Plugin {
    return typeof value === 'function' && value.prototype instanceof Plugin;
}

const useGeneViewerState = (
    assembly: any,
    tracks: Track[],
    defaultSession: any,
    apiUrl: string,
    initKey?: number
) => {
    const [viewState, setViewState] = useState<ReturnType<typeof createViewState> | null>(null);
    const [initializationError, setInitializationError] = useState<Error | null>(null);

    useEffect(() => {
        const initialize = async () => {
            try {
                // Don't treat missing assembly as an error - it's just loading
                if (!assembly) {
                    setViewState(null);
                    setInitializationError(null);
                    return;
                }

                const corePluginConstructors = (Object.values(CorePlugins) as unknown[])
                    .filter((plugin): plugin is PluginConstructor => isPluginConstructor(plugin));

                const plugins: PluginConstructor[] = [EnhancedGeneFeaturePlugin, ...corePluginConstructors];

                const config = {
                    assemblies: [assembly],
                    tracks: tracks.map((track) => ({
                        ...track,
                        visible: true,
                        apiUrl: apiUrl,
                        display: {
                            ...track.display,
                            type: track.display?.type || 'LinearBasicDisplay'
                        }
                    })),
                    configuration: {
                        disableAnalytics: true,
                        rpc: {
                            defaultDriver: 'MainThreadRpcDriver',
                        },
                        theme: {
                            palette: {
                                primary: {
                                    main: '#0D233F',
                                },
                                secondary: {
                                    main: '#721E63',
                                },
                            },
                        },
                    },
                    defaultSession: defaultSession ? {...defaultSession, name: 'defaultSession'} : undefined
                };

                const state = createViewState({
                    config,
                    plugins,
                    makeWorkerInstance,
                });

                // Override session's showWidget and addWidget to prevent feature drawer from opening
                try {
                    const session = state.session;
                    if (session) {
                        // Override widget methods to block JBrowse's built-in feature panel
                        session.showWidget = function() {
                            return undefined;
                        };
                        
                        session.addWidget = function() {
                            return undefined;
                        };
                    }
                } catch (error) {
                    console.warn('Failed to override widget methods:', error);
                }

                setViewState(state);
                setInitializationError(null); // Clear any previous errors

                const assemblyManager = state.assemblyManager;
                const assemblyInstance = assemblyManager.get(assembly.name);
                if (assemblyInstance) {
                    await assemblyInstance.load();
                }
            } catch (error) {
                setInitializationError(error instanceof Error ? error : new Error(String(error)));
                setViewState(null);
            }
        };

        initialize();
    }, [assembly, tracks, defaultSession, initKey]);

    return {viewState, initializationError};
};

export default useGeneViewerState;