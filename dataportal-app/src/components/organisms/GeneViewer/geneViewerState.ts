import { useEffect, useState } from 'react';
import { createViewState } from '@jbrowse/react-app';
import makeWorkerInstance from '@jbrowse/react-app/esm/makeWorkerInstance';
import { createRoot, hydrateRoot } from 'react-dom/client';
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

        console.log('Core Plugin Constructors:', corePluginConstructors);

        // Register the CustomSvgFeatureRendererPlugin before creating the view state
        const plugins: PluginConstructor[] = [CustomSvgFeatureRendererPlugin, ...corePluginConstructors];

        console.log('Registered Plugins:', plugins);

        const config = {
          assemblies: [assembly],
          tracks: tracks.map((track) => ({
            ...track,
            visible: true,
            renderer: {
              type: 'CustomSvgFeatureRenderer',
            },
          })),
          defaultSession: defaultSession || undefined,
        };

        // Create the view state
        const state = createViewState({
          config,
          plugins,
          hydrateFn: hydrateRoot,
          createRootFn: createRoot,
          makeWorkerInstance,
        });

        console.log('State.pluginManager:', state.pluginManager);
        console.log('Loaded Plugins:', state.pluginManager.plugins.map((p: any) => p.name));

        // Log registered renderers to confirm the custom renderer is present
        const registeredRenderers = state.pluginManager.getElementTypesInGroup('renderer').map((renderer: any) => renderer.name);
        console.log('Registered Renderers:', registeredRenderers);

        // Check if the CustomSvgFeatureRenderer is registered
        if (!registeredRenderers.includes('CustomSvgFeatureRenderer')) {
          throw new Error('CustomSvgFeatureRenderer not found in registered renderers.');
        }

        setViewState(state);

        // Force refresh of tracks to ensure the renderer is applied
        state.session.views[0]?.tracks.forEach((track: any) => {
          track.displays.forEach((display: any) => {
            console.log(`Refreshing display ${display.id}`);
            // display.refresh();
          });
        });

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

  return { viewState, initializationError };
};

export default useGeneViewerState;
