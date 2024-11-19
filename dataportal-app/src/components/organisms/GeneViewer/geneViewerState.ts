import {useEffect, useState} from 'react';
import {createViewState} from '@jbrowse/react-app'
import makeWorkerInstance from '@jbrowse/react-app/esm/makeWorkerInstance'
import {createRoot, hydrateRoot} from "react-dom/client";

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

    useEffect(() => {
        const initialize = async () => {
            try {
                console.log('Initializing JBrowse with assembly:', assembly);
                console.log('Tracks before initializing state:', tracks);
                console.log('DefaultSession before initializing state:', defaultSession);

                if (!assembly) {
                    throw new Error("Assembly configuration is missing.");
                }

                const config: any = {
                    assemblies: [assembly],
                    tracks: tracks.map((track: Track) => ({
                        ...track,
                        visible: true,
                    })),
                };

                // Conditionally add defaultSession if available
                if (defaultSession) {
                    config.defaultSession = defaultSession;
                }

                const state = createViewState({
                    config,
                    hydrateFn: hydrateRoot,
                    createRootFn: createRoot,
                    makeWorkerInstance,
                });

                const model = state.session.views[0];
                //model.activateTrackSelector(); //uncomment to show trackselector at start
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
