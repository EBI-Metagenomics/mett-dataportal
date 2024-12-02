import {useEffect, useState} from 'react';
import {createViewState} from '@jbrowse/react-app';
import makeWorkerInstance from '@jbrowse/react-app/esm/makeWorkerInstance';
import {createRoot, hydrateRoot} from 'react-dom/client';
import CustomAMRDetailsPlugin from '@components/organisms/GeneViewer/CustomAMRDetailsPlugin';
import CustomFeatureDetailsPlugin from "@components/organisms/GeneViewer/CustomFeatureDetailsPlugin";
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


// Custom hook for initializing JBrowse state
const useGeneViewerState = (assembly: any, tracks: Track[], defaultSession: any) => {
    const [viewState, setViewState] = useState<ReturnType<typeof createViewState> | null>(null);
    const [initializationError, setInitializationError] = useState<Error | null>(null);

    useEffect(() => {
        const initialize = async () => {
            try {
                if (!assembly) {
                    throw new Error('Assembly configuration is missing.');
                }

                const config = {
                    assemblies: [assembly],
                    tracks: tracks.map((track) => ({
                        ...track,
                        visible: true,
                    })),
                    defaultSession: defaultSession || undefined,
                };

                const corePluginConstructors = (Object.values(CorePlugins) as unknown[])
                    .filter((plugin): plugin is PluginConstructor => isPluginConstructor(plugin));

                const state = createViewState({
                    config,
                    plugins: [CustomFeatureDetailsPlugin, CustomAMRDetailsPlugin, ...corePluginConstructors],
                    hydrateFn: hydrateRoot,
                    createRootFn: createRoot,
                    makeWorkerInstance,
                    onChange: (patch, reversePatch) => {
                        console.log('State changed', patch);
                    }
                });

                setViewState(state);

                const session = state.session;

                // Add the widget manually for testing //todo important implementation for new widget plugin
                // const testWidget = session.addWidget('AMRDetailsWidget', 'amrDetailsWidget', {
                //     featureData: {testKey: 'testValue'},
                // });
                // session.showWidget(testWidget);

                // Assembly loading
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
