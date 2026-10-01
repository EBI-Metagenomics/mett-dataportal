import { useEffect, useState } from 'react';
import { createViewState } from '@jbrowse/react-app2';
import makeWorkerInstance from '@jbrowse/react-app2/esm/makeWorkerInstance';
import Plugin from '@jbrowse/core/Plugin';
import EnhancedGeneFeaturePlugin from '../../../../plugins/EnhancedGeneFeaturePlugin';
import { JBROWSE_THEME } from '../../../../utils/gene-viewer/jbrowseTheme';
import { suppressJBrowseWidgets } from './suppressJBrowseWidgets';

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

const useGeneViewerState = (
  assembly: any,
  tracks: Track[],
  defaultSession: any,
  isolateName: string,
  initKey?: number
) => {
  const [viewState, setViewState] = useState<ReturnType<
    typeof createViewState
  > | null>(null);
  const [initializationError, setInitializationError] = useState<Error | null>(
    null
  );

  useEffect(() => {
    let disposeWidgetSuppress: (() => void) | undefined;

    const initialize = async () => {
      try {
        if (!assembly) {
          setViewState(null);
          setInitializationError(null);
          return;
        }

        // createViewState already registers JBrowse corePlugins; only add app plugins.
        const plugins: PluginConstructor[] = [EnhancedGeneFeaturePlugin];

        const config = {
          assemblies: [assembly],
          tracks: tracks.map(track => ({
            ...track,
            visible: true,
            isolateName,
            display: {
              ...track.display,
              type: track.display?.type || 'LinearBasicDisplay',
            },
          })),
          configuration: {
            disableAnalytics: true,
            rpc: {
              defaultDriver: 'MainThreadRpcDriver',
            },
            theme: JBROWSE_THEME,
          },
          defaultSession: defaultSession
            ? { ...defaultSession, name: 'defaultSession' }
            : undefined,
        };

        const state = createViewState({
          config,
          plugins,
          makeWorkerInstance,
        });

        try {
          // Clear FILE/ADD/TOOLS/HELP menus (AppBar is also hidden via CSS).
          if (typeof state.setMenus === 'function') {
            state.setMenus([]);
          }

          const session = state.session;
          if (session) {
            // MST actions cannot be replaced by assignment; use autorun suppress.
            disposeWidgetSuppress = suppressJBrowseWidgets(session);

            // Best-effort stubs for non-MST callers / older paths.
            try {
              session.showWidget = function () {
                return undefined;
              };
              session.addWidget = function () {
                return undefined;
              };
            } catch {
              // protected MST actions — ignore
            }

            try {
              session.removeView = function () {
                return undefined;
              };
            } catch {
              // ignore
            }
          }
        } catch (error) {
          console.warn('Failed to configure embedded JBrowse session:', error);
        }

        setViewState(state);
        setInitializationError(null);

        const assemblyManager = state.assemblyManager;
        const assemblyInstance = assemblyManager.get(assembly.name);
        if (assemblyInstance) {
          await assemblyInstance.load();
        }
      } catch (error) {
        setInitializationError(
          error instanceof Error ? error : new Error(String(error))
        );
        setViewState(null);
      }
    };

    initialize();

    return () => {
      disposeWidgetSuppress?.();
    };
  }, [assembly, tracks, defaultSession, initKey]);

  return { viewState, initializationError };
};

export default useGeneViewerState;
