import React from 'react';
import { createViewState, JBrowseCircularGenomeView } from '@jbrowse/react-circular-genome-view2';
import '@fontsource/roboto';
import * as CorePlugins from '@jbrowse/core/pluggableElementTypes';
import Plugin from '@jbrowse/core/Plugin';
import EnhancedGeneFeaturePlugin from "../../../../../plugins/EnhancedGeneFeaturePlugin";
import LinearGenomeViewPlugin from '@jbrowse/plugin-linear-genome-view';
import styles from './GeneViewerContent.module.scss';

interface GeneViewerCircularContentProps {
    assembly: any;
    tracks: any[];
    height: number;
    onRefreshTracks?: () => void;
    onFeatureSelect?: (feature: any) => void;
}

type PluginConstructor = new (...args: unknown[]) => Plugin;

function isPluginConstructor(value: unknown): value is typeof Plugin {
    return typeof value === 'function' && value.prototype instanceof Plugin;
}

const GeneViewerCircularContent: React.FC<GeneViewerCircularContentProps> = ({
    assembly,
    tracks,
    height,
    onRefreshTracks,
    onFeatureSelect,
}) => {
    // Create view state specifically for circular view
    const viewState = React.useMemo(() => {
        if (!assembly) {
            return null;
        }

        console.log('🔧 Creating circular view with tracks:', tracks);

        const corePluginConstructors = (Object.values(CorePlugins) as unknown[])
            .filter((plugin): plugin is PluginConstructor => isPluginConstructor(plugin));

        const plugins: PluginConstructor[] = [
            EnhancedGeneFeaturePlugin, 
            LinearGenomeViewPlugin,
            ...corePluginConstructors
        ];

        // Configure tracks for circular view using available display types
        const circularTracks = tracks.map((track) => ({
            type: track.type,
            trackId: track.trackId,
            name: track.name,
            assemblyNames: track.assemblyNames,
            adapter: track.adapter,
            visible: true,
            displays: [
                {
                    displayId: `${track.trackId}-circular-display`,
                    type: 'ChordVariantDisplay', // Use circular-specific display type
                    renderer: {
                        color1: '#0000ff',
                        labels: {
                            name: `jexl:get(feature, 'locus_tag') || get(feature, 'gene') || get(feature, 'id')`
                        },
                        showLabels: true,
                        height: 20,
                    }
                }
            ]
        }));

        const config = {
            assembly: assembly,
            tracks: circularTracks,
            plugins: plugins
            // Let the circular view handle multiple contigs automatically
        };

        console.log('🔧 Circular view config:', config);
        console.log('🔧 Assembly contigs:', assembly.sequence.adapter.sequences);
        console.log('🔧 Number of contigs:', assembly.sequence.adapter.sequences.length);
        console.log('🔧 Circular tracks:', circularTracks);
        
        // Log what plugins and elements are available
        console.log('🔧 Available plugins:', plugins.map(p => p.name));

        const state = createViewState(config);
        
        console.log('✅ Circular view plugins loaded:', state.pluginManager.plugins.map(p => p.name));
        console.log('✅ Circular view adapter elements:', state.pluginManager.getAdapterElements().map((a: any) => a.name));
        
        // Try to get display and renderer elements with safe method calls
        try {
            const displayElements = state.pluginManager.getDisplayElements ? 
                state.pluginManager.getDisplayElements().map((d: any) => d.name) : 'Not available';
            console.log('✅ Circular view display elements:', displayElements);
        } catch (e) {
            console.log('✅ Circular view display elements: Not available');
        }
        
        try {
            const rendererTypes = state.pluginManager.getRendererTypes ? 
                state.pluginManager.getRendererTypes().map((r: any) => r.name) : 'Not available';
            console.log('✅ Circular view renderer types:', rendererTypes);
        } catch (e) {
            console.log('✅ Circular view renderer types: Not available');
        }
        
        return state;
    }, [assembly, tracks]);

    // Refresh tracks when assembly or tracks change
    React.useEffect(() => {
        if (viewState && onRefreshTracks) {
            onRefreshTracks();
        }
    }, [viewState, onRefreshTracks]);

    // Listen for feature selection events
    React.useEffect(() => {
        if (!viewState || !onFeatureSelect) return;

        const session = viewState.session;
        if (!session) return;

        // Listen for feature selection changes
        const handleFeatureSelect = (event: any) => {
            if (event.feature) {
                console.log('Feature selected in Circular JBrowse:', event.feature);
                onFeatureSelect(event.feature);
            }
        };

        // Try to find the circular genome view and listen for feature selection
        const views = session.views;
        if (views && views.length > 0) {
            const view = views[0];
            
            // Listen for feature selection events
            if (view.on) {
                view.on('featureSelect', handleFeatureSelect);
            }
            
            // Also try to listen for click events on features
            if (view.on) {
                view.on('click', (event: any) => {
                    if (event.feature) {
                        console.log('Feature clicked in Circular JBrowse:', event.feature);
                        onFeatureSelect(event.feature);
                    }
                });
            }
        }

        return () => {
            // Cleanup listeners
            if (views && views.length > 0) {
                const view = views[0];
                if (view.off) {
                    view.off('featureSelect', handleFeatureSelect);
                    view.off('click', handleFeatureSelect);
                }
            }
        };
    }, [viewState, onFeatureSelect]);

    if (!viewState) {
        return <p>Loading Circular Genome Viewer...</p>;
    }

    return (
        <div
            style={{
                maxHeight: `${height}px`,
                overflowY: 'auto',
                overflowX: 'auto',
                width: '100%',
                maxWidth: 'none',
            }}
        >
            <div className={styles.jbrowseViewer}>
                <div className={styles.jbrowseContainer}>
                    <JBrowseCircularGenomeView viewState={viewState} />
                </div>
            </div>
        </div>
    );
};

export default GeneViewerCircularContent;
