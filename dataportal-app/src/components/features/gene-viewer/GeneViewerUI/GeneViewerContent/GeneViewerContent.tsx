import React from 'react';
import {JBrowseApp} from "@jbrowse/react-app2";
import GeneViewerCircularContent from './GeneViewerCircularContent';
import styles from './GeneViewerContent.module.scss';

type ViewType = 'linear' | 'circular';

interface GeneViewerContentProps {
    viewState: any;
    height: number;
    viewType?: ViewType;
    assembly?: any;
    tracks?: any[];
    onRefreshTracks?: () => void;
    onFeatureSelect?: (feature: any) => void;
}

const GeneViewerContent: React.FC<GeneViewerContentProps> = ({
                                                                 viewState,
                                                                 height,
                                                                 viewType = 'linear',
                                                                 assembly,
                                                                 tracks,
                                                                 onRefreshTracks,
                                                                 onFeatureSelect,
                                                             }) => {
    // Refresh tracks when viewState changes
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
                console.log('Feature selected in JBrowse:', event.feature);
                onFeatureSelect(event.feature);
            }
        };

        // Try to find the linear genome view and listen for feature selection
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
                        console.log('Feature clicked in JBrowse:', event.feature);
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

    // Render circular view if requested
    if (viewType === 'circular') {
        if (!assembly) {
            return <p>Loading Circular Genome Viewer...</p>;
        }
        
        return (
            <GeneViewerCircularContent
                assembly={assembly}
                tracks={tracks || []}
                height={height}
                onRefreshTracks={onRefreshTracks}
                onFeatureSelect={onFeatureSelect}
            />
        );
    }

    // Default linear view
    if (!viewState) {
        return <p>Loading Genome Viewer...</p>;
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
                    <JBrowseApp viewState={viewState}/>
                </div>
            </div>
        </div>
    );
};

export default GeneViewerContent; 