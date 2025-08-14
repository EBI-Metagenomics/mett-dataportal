import {useEffect, useState} from 'react';
import {createViewState} from '@jbrowse/react-app2';
import makeWorkerInstance from '@jbrowse/react-app2/esm/makeWorkerInstance';
import * as CorePlugins from '@jbrowse/core/pluggableElementTypes';
import Plugin from '@jbrowse/core/Plugin';
import EnhancedGeneFeaturePlugin from "../../../../plugins/EnhancedGeneFeaturePlugin";
// Temporarily disabled PyHMMERFeaturePlugin due to import issues
// TODO: Re-enable once plugin system is working


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
                // Temporarily disabled PyHMMERFeaturePlugin due to import issues
                // TODO: Re-enable once plugin system is working

                const config = {
                    assemblies: [assembly],
                    tracks: tracks.map((track) => ({
                        ...track,
                        visible: true,
                        apiUrl: apiUrl,
                        display: {
                            ...track.display,
                            type: track.display?.type || 'LinearBasicDisplay'
                            // Temporarily disabled custom feature widget
                            // TODO: Re-enable once plugin system is working
                        }
                    })),
                    defaultSession: defaultSession ? {...defaultSession, name: 'defaultSession'} : undefined
                };

                const state = createViewState({
                    config,
                    plugins,
                    makeWorkerInstance,
                });

                console.log('✅ Plugins loaded:', state.pluginManager.plugins.map(p => p.name))
                console.log('✅ getAdapterElements:', state.pluginManager.getAdapterElements())
                console.log('✅ Custom feature widget configured for tracks')

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