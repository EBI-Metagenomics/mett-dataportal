import {useEffect, useState} from 'react';
import {createViewState} from '@jbrowse/react-app';
import makeWorkerInstance from '@jbrowse/react-app/esm/makeWorkerInstance';
import {createRoot, hydrateRoot} from 'react-dom/client';
import * as CorePlugins from '@jbrowse/core/pluggableElementTypes';
import Plugin from '@jbrowse/core/Plugin';
import CustomEssentialityPlugin from "../../../plugins/CustomEssentialityPlugin";

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
    apiUrl: string
) => {
    const [viewState, setViewState] = useState<ReturnType<typeof createViewState> | null>(null);
    const [initializationError, setInitializationError] = useState<Error | null>(null);

    useEffect(() => {
        const initialize = async () => {
            try {
                if (!assembly) {
                    throw new Error('Assembly configuration is missing.');
                }

                const corePluginConstructors = (Object.values(CorePlugins) as unknown[])
                    .filter((plugin): plugin is PluginConstructor => isPluginConstructor(plugin));

                const plugins: PluginConstructor[] = [CustomEssentialityPlugin, ...corePluginConstructors];

                const config = {
                    assemblies: [assembly],
                    tracks: tracks.map((track) => ({
                        ...track,
                        visible: true,
                        apiUrl: apiUrl
                    })),
                    defaultSession: defaultSession ? {...defaultSession, name: 'defaultSession'} : undefined,
                };

                const state = createViewState({
                    config,
                    plugins,
                    hydrateFn: hydrateRoot,
                    createRootFn: createRoot,
                    makeWorkerInstance,
                });

                // console.log('✅ Plugins loaded:', state.pluginManager.plugins.map(p => p.name))
                // console.log('✅ getAdapterElements:', state.pluginManager.getAdapterElements())

                const registeredRenderers = state.pluginManager.getElementTypesInGroup('renderer').map((renderer) => renderer.name);

                setViewState(state);

                const assemblyManager = state.assemblyManager;
                const assemblyInstance = assemblyManager.get(assembly.name);
                if (assemblyInstance) {
                    await assemblyInstance.load();
                }
            } catch (error) {
                console.error('Comprehensive JBrowse initialization error:', error);
                setInitializationError(error instanceof Error ? error : new Error(String(error)));
            }
        };

        initialize();
    }, [assembly, tracks, defaultSession]);

    return {viewState, initializationError};
};

export default useGeneViewerState;