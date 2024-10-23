import { useState, useEffect } from 'react';
import { createViewState } from '@jbrowse/react-linear-genome-view';
import PluginManager from '@jbrowse/core/PluginManager';
import LinearGenomeViewPlugin from '@jbrowse/plugin-linear-genome-view';
import makeWorkerInstance from '@jbrowse/react-linear-genome-view/esm/makeWorkerInstance';

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

// GenStateViewer custom hook
const useGeneViewerState = (assembly: any, tracks: Track[], defaultSession: any) => {
    const [viewState, setViewState] = useState<ReturnType<typeof createViewState> | null>(null);

    console.log('Tracks:', tracks);
    console.log('Assembly:', assembly);
    console.log("Tracks being passed: ", tracks);
    const visibleTracks = tracks.filter(track => track.visible === true);
    console.log("Visible Tracks: ", visibleTracks);

    useEffect(() => {
        const initialize = async () => {
            try {
                const pluginManager = new PluginManager([
                    new LinearGenomeViewPlugin(),
                ]);

                pluginManager.createPluggableElements();
                pluginManager.configure();

                console.log('Initializing JBrowse with assembly:', assembly);
                console.log('Tracks before initializing state:', tracks);

                const state = createViewState({
                    assembly,
                    tracks: tracks.map((track: Track) => ({
                        ...track,
                        visible: true,
                    })),
                    onChange: (patch: any) => {
                        console.log(JSON.stringify(patch));
                    },
                    defaultSession,
                    configuration: {
                        rpc: {
                            defaultDriver: 'WebWorkerRpcDriver',
                        },
                    },
                    // locationBoxLength: 0,
                    // hideControls: {
                    //     header: {
                    //         search: true,
                    //     },
                    // },
                    makeWorkerInstance,
                });

                setViewState(state);

                const assemblyManager = state.assemblyManager;
                const assemblyInstance = assemblyManager.get(assembly.name);

                if (assemblyInstance) {
                    await assemblyInstance.load();
                }
            } catch (error) {
                console.error('Error during JBrowse initialization:', error);
            }
        };

        initialize();
    }, [assembly, tracks, defaultSession]);

    return viewState;
};

export default useGeneViewerState;
