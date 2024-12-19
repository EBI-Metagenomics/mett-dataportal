import {useEffect, useState} from 'react';
import {createViewState} from '@jbrowse/react-app';
import makeWorkerInstance from '@jbrowse/react-app/esm/makeWorkerInstance';
import {createRoot, hydrateRoot} from 'react-dom/client';
import CustomSvgFeatureRendererPlugin from "../../../plugins/CustomSvgRenderer";
import * as CorePlugins from '@jbrowse/core/pluggableElementTypes';
import Plugin from '@jbrowse/core/Plugin';

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

type PluginConstructor = new (...args: any[]) => Plugin;

function isPluginConstructor(value: any): value is typeof Plugin {
    return value && value.prototype instanceof Plugin;
}

const useGeneViewerState = (assembly: any, tracks: Track[], defaultSession: any) => {
    const [viewState, setViewState] = useState<ReturnType<typeof createViewState> | null>(null);
    const [initializationError, setInitializationError] = useState<Error | null>(null);

    useEffect(() => {
        const initialize = async () => {
            try {
                if (!assembly) {
                    throw new Error('Assembly configuration is missing.');
                }

                // const corePluginConstructors = (Object.values(CorePlugins) as unknown[])
                //   .filter((plugin): plugin is PluginConstructor => isPluginConstructor(plugin));
                console.log('CorePlugins:', CorePlugins);
                const corePluginConstructors = (Object.values(CorePlugins) as unknown[])
                    .filter((plugin): plugin is PluginConstructor => isPluginConstructor(plugin));

                console.log('corePluginConstructors:', corePluginConstructors);
                const plugins: PluginConstructor[] = [CustomSvgFeatureRendererPlugin, ...corePluginConstructors];

                console.log('Registered Plugins:', plugins);

                const config = {
                    assemblies: [assembly],
                    tracks: tracks.map((track) => ({
                        ...track,
                        visible: true,
                    })),
                    defaultSession: defaultSession || undefined,
                };

                const state = createViewState({
                    config,
                    plugins,
                    hydrateFn: hydrateRoot,
                    createRootFn: createRoot,
                    makeWorkerInstance,
                });

                console.log('state.pluginManager:', state.pluginManager);
                console.log('Plugins:', state.pluginManager.plugins.map((p: any) => p.name))


                setViewState(state);
                state.session.views[0].tracks.forEach((track: any) => {
                    console.log(state.session.views[0])
                    console.log(`Track ${track.configuration.trackId}:`,  track.configuration.displays)
                })

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
