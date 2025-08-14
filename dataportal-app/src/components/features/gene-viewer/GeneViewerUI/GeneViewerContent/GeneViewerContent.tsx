import React from 'react';
import {JBrowseApp} from "@jbrowse/react-app2";
import styles from './GeneViewerContent.module.scss';

interface GeneViewerContentProps {
    viewState: any;
    height: number;
    onRefreshTracks?: () => void;
    onFeatureSelect?: (feature: any) => void;
}

const GeneViewerContent: React.FC<GeneViewerContentProps> = ({
                                                                 viewState,
                                                                 height,
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

    if (!viewState) {
        return <p>Loading Genome Viewer...</p>;
    }

    return (
        <div
            style={{
                maxHeight: `${height}px`,
                overflowY: 'auto',
                overflowX: 'auto',
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