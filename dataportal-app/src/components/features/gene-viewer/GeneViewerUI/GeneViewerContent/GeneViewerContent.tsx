import React from 'react';
import {JBrowseApp} from "@jbrowse/react-app2";
import styles from './GeneViewerContent.module.scss';
import {GeneService} from '../../../../../services/gene';
import {useViewportSyncStore} from '../../../../../stores/viewportSyncStore';

// Extend Window interface for selectedGeneId
declare global {
    interface Window {
        selectedGeneId?: string;
    }
}

interface GeneViewerContentProps {
    viewState: any;
    onRefreshTracks?: () => void;
    onFeatureSelect?: (feature: any) => void;
}

// Heuristic to distinguish real gene locus tags from generic JBrowse container IDs
// like "tracksContainer", "svgfeatures", "display-placeholderId", etc.
const isLikelyGeneId = (rawId: string | null): boolean => {
    if (!rawId) return false;
    const id = rawId.trim();
    if (!id) return false;

    // Ignore obvious non-gene/container IDs
    if (/(container|tracks?|svg|placeholder|display)/i.test(id)) {
        return false;
    }

    // Require at least one letter and one digit
    if (!/[A-Za-z]/.test(id) || !/\d/.test(id)) {
        return false;
    }

    // Disallow whitespace
    if (/\s/.test(id)) {
        return false;
    }

    return true;
};

const GeneViewerContent: React.FC<GeneViewerContentProps> = ({
    viewState,
    onRefreshTracks,
    onFeatureSelect,
}) => {
    // Hide the main JBrowse menu bar (FILE, ADD, TOOLS, HELP) and feature panel
    React.useEffect(() => {
        const hideMenuBarAndFeaturePanel = () => {
            // Find the "File" button which is part of the main menu bar
            const buttons = Array.from(document.querySelectorAll('button[data-testid="dropDownMenuButton"]'));
            const fileButton = buttons.find(btn => btn.textContent?.includes('File'));
            
            if (fileButton) {
                // Find the parent toolbar
                let parent = fileButton.parentElement;
                while (parent) {
                    // Look for the MuiToolbar that contains the menu buttons
                    if (parent.classList.contains('MuiToolbar-root')) {
                        // Verify this is the main menu by checking for the JBrowse logo
                        const hasSvgLogo = parent.querySelector('svg[viewBox="0 0 641 175"]');
                        if (hasSvgLogo) {
                            // Find and hide the parent AppBar
                            let appBarParent = parent.parentElement;
                            while (appBarParent) {
                                if (appBarParent.classList.contains('MuiAppBar-root')) {
                                    (appBarParent as HTMLElement).style.display = 'none';
                                    return;
                                }
                                appBarParent = appBarParent.parentElement;
                            }
                        }
                    }
                    parent = parent.parentElement;
                }
            }

            // NUCLEAR OPTION: Hide ALL possible JBrowse drawer elements
            const selectorsToHide = [
                '.MuiDrawer-root', '.MuiDrawer-modal', '.MuiDrawer-paper', '.MuiDrawer-docked',
                '[class*="MuiDrawer"]', 'div[class^="MuiDrawer"]', 'aside[class*="MuiDrawer"]',
                '[class*="BaseFeatureDetail"]', '[class*="FeatureDetails"]', '[class*="featureDetails"]',
                '[class*="DrawerWidget"]', '[class*="FeatureWidget"]',
                '.MuiBackdrop-root', '[class*="MuiBackdrop"]',
                '[role="presentation"]',
                // Target by aria labels
                '[aria-label*="drawer"]', '[aria-label*="Drawer"]',
                // Target Paper components that might contain feature details
                '[class*="MuiPaper-root"]:has([class*="BaseFeature"])',
            ];
            
            selectorsToHide.forEach(selector => {
                try {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach((el) => {
                        const element = el as HTMLElement;
                        // Use inline styles with !important to override everything
                        element.style.cssText = `
                            display: none !important;
                            visibility: hidden !important;
                            opacity: 0 !important;
                            pointer-events: none !important;
                            width: 0px !important;
                            height: 0px !important;
                            overflow: hidden !important;
                            position: fixed !important;
                            top: -9999px !important;
                            left: -9999px !important;
                        `;
                        // Also remove from DOM flow
                        element.setAttribute('aria-hidden', 'true');
                    });
                } catch (e) {
                    // Selector might not be valid, skip
                }
            });
        };

        // Run immediately
        hideMenuBarAndFeaturePanel();

        // Set up a MutationObserver to watch for the menu bar being added to the DOM
        const observer = new MutationObserver(() => {
            hideMenuBarAndFeaturePanel();
        });

        // Observe the entire document for added nodes
        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });

        // Also run after delays to catch late-rendered elements
        const timeout1 = setTimeout(hideMenuBarAndFeaturePanel, 100);
        const timeout2 = setTimeout(hideMenuBarAndFeaturePanel, 500);
        const timeout3 = setTimeout(hideMenuBarAndFeaturePanel, 1000);

        return () => {
            observer.disconnect();
            clearTimeout(timeout1);
            clearTimeout(timeout2);
            clearTimeout(timeout3);
        };
    }, [viewState]);

    // Refresh tracks when viewState changes
    React.useEffect(() => {
        if (viewState && onRefreshTracks) {
            onRefreshTracks();
        }
    }, [viewState, onRefreshTracks]);

    // Listen for feature clicks and fetch data from API
    React.useEffect(() => {
        if (!viewState || !onFeatureSelect) return;
        
        let lastClickedFeatureId: string | null = null;
        
        const handleFeatureClick = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            const featureElement = target.closest('[data-testid]') as HTMLElement;
            
            if (!featureElement) {
                return;
            }

            const featureId = featureElement.getAttribute('data-testid');
            if (!featureId) {
                return;
            }

            // If this doesn't look like a real gene ID, ignore the click entirely.
            // This avoids firing bogus API calls for container elements while
            // preserving the currently selected gene in the feature panel.
            if (!isLikelyGeneId(featureId)) {
                return;
            }

            // Prevent duplicate processing of the same feature ID
            if (featureId === lastClickedFeatureId) {
                return;
            }
            lastClickedFeatureId = featureId;
            
            // Prevent JBrowse's default drawer behavior
            event.stopPropagation();
            event.preventDefault();
            
            // Store the selected gene ID globally for JBrowse JEXL expressions
            window.selectedGeneId = featureId;
            
            // Force JBrowse to re-render the track to apply highlighting
            if (viewState) {
                try {
                    const view = viewState.session?.views?.[0];
                    if (view && view.tracks) {
                        // Force all tracks to reload/re-render
                        view.tracks.forEach((track: any) => {
                            if (track.displays) {
                                track.displays.forEach((display: any) => {
                                    try {
                                        // Trigger display re-render by reloading
                                        if (display.reload) {
                                            display.reload();
                                        } else if (display.setError) {
                                            // Alternative: clear and refresh
                                            display.setError(undefined);
                                        }
                                    } catch (e) {
                                        // Ignore individual display errors
                                    }
                                });
                            }
                        });
                        
                        // Also try to refresh the view itself
                        if (view.setWidth) {
                            view.setWidth(view.width + 0.001);
                            setTimeout(() => view.setWidth(view.width - 0.001), 10);
                        }
                    }
                } catch (err) {
                    console.warn('Could not trigger JBrowse re-render:', err);
                }
            }
            
            // Update viewport sync store with selected locus tag so:
            // - the Genomic Context table can highlight the corresponding row
            // - other components react to the selected gene
            useViewportSyncStore.getState().setSelectedLocusTag(featureId);
            
            // Fetch complete gene data from API
            Promise.all([
                GeneService.fetchGeneByLocusTag(featureId),
                GeneService.fetchGeneProteinSeq(featureId).catch(() => ({ protein_sequence: '' }))
            ])
                .then(([geneData, proteinData]) => {
                    const completeData = {
                        ...geneData,
                        protein_sequence: proteinData.protein_sequence || ''
                    };
                    onFeatureSelect(completeData);
                })
                .catch((err: any) => {
                    console.warn('Failed to fetch gene data:', err);
                    // Fallback to minimal data so the custom feature panel still opens
                    onFeatureSelect({ 
                        locus_tag: featureId,
                        id: featureId 
                    });
                });
        };

        // Handle double-click to prevent JBrowse's default feature drawer
        const handleDoubleClick = (event: MouseEvent) => {
            const target = event.target as HTMLElement;
            const featureElement = target.closest('[data-testid]') as HTMLElement;
            
            if (featureElement) {
                const featureId = featureElement.getAttribute('data-testid');
                
                // If it's a gene feature, prevent JBrowse's default drawer
                if (isLikelyGeneId(featureId)) {
                    event.stopPropagation();
                    event.preventDefault();
                    
                    // Close drawers immediately and after a short delay (in case they open asynchronously)
                    const closeDrawers = () => {
                        if (viewState?.session) {
                            try {
                                // Hide any active feature widgets
                                if (viewState.session.widgets?.has('baseFeature')) {
                                    const widget = viewState.session.activeWidgets.get('baseFeature');
                                    if (widget) {
                                        viewState.session.hideWidget(widget);
                                    }
                                }
                                
                                // Close any drawers by hiding all active widgets
                                if (viewState.session.activeWidgets) {
                                    const widgetsToHide: any[] = [];
                                    viewState.session.activeWidgets.forEach((widget: any) => {
                                        if (widget && typeof widget.hide === 'function') {
                                            widgetsToHide.push(widget);
                                        }
                                    });
                                    // Hide widgets outside the forEach to avoid iteration issues
                                    widgetsToHide.forEach((widget: any) => {
                                        try {
                                            widget.hide();
                                        } catch {
                                            // Ignore individual widget errors
                                        }
                                    });
                                }
                            } catch (err) {
                                // Ignore errors
                            }
                        }
                    };
                    
                    // Close immediately
                    closeDrawers();
                    
                    // Also close after a short delay in case drawer opens asynchronously
                    setTimeout(closeDrawers, 10);
                    setTimeout(closeDrawers, 50);
                    setTimeout(closeDrawers, 100);
                }
            }
        };

        // Add click listener with capture phase to intercept before JBrowse
        document.addEventListener('click', handleFeatureClick, true);
        
        // Add double-click listener to prevent JBrowse's default feature drawer
        document.addEventListener('dblclick', handleDoubleClick, true);

        return () => {
            document.removeEventListener('click', handleFeatureClick, true);
            document.removeEventListener('dblclick', handleDoubleClick, true);
        };
    }, [viewState, onFeatureSelect]);
    

    if (!viewState) {
        return <p>Loading Genome Viewer...</p>;
    }

    return (
        <div className={styles.jbrowseViewer}>
            <div className={styles.jbrowseContainer}>
                <JBrowseApp viewState={viewState}/>
            </div>
        </div>
    );
};

export default GeneViewerContent; 