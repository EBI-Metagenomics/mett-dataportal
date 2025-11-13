import React, {useEffect, useState, useCallback, useMemo, useRef} from 'react';
import useGeneViewerState from '@components/features/gene-viewer/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/features/gene-viewer/GeneSearchForm/GeneSearchForm";

// Import new hooks and utilities
import {useGeneViewerData, useGeneViewerSearch} from '../../hooks';
import {useGeneViewerUrlSync} from '../../hooks/useGeneViewerUrlSync';
import {useDebouncedLoading} from '../../hooks/useDebouncedLoading';

import {refreshStructuralAnnotationTrack, useGeneViewerConfig} from '../../utils/gene-viewer';
import {GeneViewerContent, GeneViewerControls, GeneViewerHeader} from '../features/gene-viewer/GeneViewerUI';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import {useFilterStore} from '../../stores/filterStore';
import {DEFAULT_PER_PAGE_CNT} from '../../utils/common/constants';
import {useFacetedFilters} from '../../hooks/useFacetedFilters';

// Import custom feature panel
import FeaturePanel from '../features/gene-viewer/FeaturePanel/FeaturePanel';
import SyncView from '../features/gene-viewer/SyncView';
import TabNavigation from '../molecules/TabNavigation';
import { useJBrowseViewportSync } from '../../hooks/useJBrowseViewportSync';
import { useViewportSyncStore } from '../../stores/viewportSyncStore';
import { VIEWPORT_SYNC_CONSTANTS } from '../../utils/gene-viewer';

const GeneViewerPage: React.FC = () => {
    const renderCount = useRef(0);
    renderCount.current += 1;

    // Get state from Zustand stores
    const filterStore = useFilterStore();
    const { viewportChanged, setViewportChanged } = useViewportSyncStore();
    
    // Tab state for Search View / Genomic Context
    const [activeTab, setActiveTab] = useState<'search' | 'sync'>('search');
    const [showAutoSwitchNotification, setShowAutoSwitchNotification] = useState(false);
    const [wasAutoSwitched, setWasAutoSwitched] = useState(false);

    // URL synchronization for gene viewer
    useGeneViewerUrlSync();

    // Local state
    const [pageSize, setPageSize] = useState(DEFAULT_PER_PAGE_CNT);
    const [selectedFeature, setSelectedFeature] = useState<any | null>(null);

    // Custom hooks for data management
    const geneViewerData = useGeneViewerData();
    
    // State for essentiality toggle - only available for type strains
    const [includeEssentiality, setIncludeEssentiality] = useState(() => {
        if (!geneViewerData.genomeMeta) return false;
        return geneViewerData.genomeMeta.type_strain === true;
    });

    // Update essentiality state when genome changes
    useEffect(() => {
        if (geneViewerData.genomeMeta) {
            setIncludeEssentiality(geneViewerData.genomeMeta.type_strain === true);
        }
    }, [geneViewerData.genomeMeta]);

    // Toggle handler for essentiality
    const handleEssentialityToggle = useCallback((include: boolean) => {
        setIncludeEssentiality(include);
    }, []);
    const geneViewerSearch = useGeneViewerSearch({
        genomeMeta: geneViewerData.genomeMeta,
        setLoading: geneViewerData.setLoading,
        pageSize: pageSize,
    });

    const debouncedLoading = useDebouncedLoading({
        loading: geneViewerData.loading,
        delay: 300,
        minLoadingTime: 500
    });

    // Call the hook directly - it's already optimized internally
    const geneViewerConfig = useGeneViewerConfig(
        geneViewerData.genomeMeta,
        geneViewerData.geneMeta,
        includeEssentiality
    );

    const lastGenomeRef = React.useRef<string | null>(null);
    const [jbrowseInitKey, setJbrowseInitKey] = useState(0);

    useEffect(() => {
        if (geneViewerData.genomeMeta?.isolate_name !== lastGenomeRef.current) {
            lastGenomeRef.current = geneViewerData.genomeMeta?.isolate_name || null;
            setJbrowseInitKey((k) => k + 1);
            useViewportSyncStore.getState().setViewportInitialized(false);
        }
    }, [geneViewerData.genomeMeta?.isolate_name]);

    const {viewState} = useGeneViewerState(
        geneViewerConfig.assembly,
        geneViewerConfig.tracks,
        geneViewerConfig.sessionConfig,
        geneViewerData.genomeMeta?.isolate_name || '',
        jbrowseInitKey
    );

    useJBrowseViewportSync({
        viewState,
        isolateName: geneViewerData.genomeMeta?.isolate_name || null,
        debounceMs: VIEWPORT_SYNC_CONSTANTS.VIEWPORT_DEBOUNCE_MS,
        enabled: true,
    });

    useEffect(() => {
        if (viewportChanged && activeTab === 'search') {
            const { lastTableNavigationTime } = useViewportSyncStore.getState();
            const isInCooldown = lastTableNavigationTime !== null &&
                (Date.now() - lastTableNavigationTime) < VIEWPORT_SYNC_CONSTANTS.TABLE_NAVIGATION_COOLDOWN_MS;
            
            if (!isInCooldown) {
                setActiveTab('sync');
                setWasAutoSwitched(true);
                setShowAutoSwitchNotification(true);
            }
            setViewportChanged(false);
        }
    }, [viewportChanged, activeTab, setViewportChanged]);

    const handleSwitchToSearch = useCallback(() => {
        setActiveTab('search');
        setShowAutoSwitchNotification(false);
        setWasAutoSwitched(false);
    }, []);

    const handleDismissNotification = useCallback(() => {
        setShowAutoSwitchNotification(false);
    }, []);

    const handleTrackRefresh = useCallback(() => {
        if (!viewState) return;
        
        const session = viewState.session;
        const view = session.views[0];
        if (!view) return;

        try {
            view.hideTrack('structural_annotation');

            const newTrack = geneViewerConfig.tracks.find(
                (track: any) => track.trackId === 'structural_annotation'
            );
            
            if (newTrack) {
                view.showTrack('structural_annotation', {
                    ...newTrack,
                    adapter: {
                        ...newTrack.adapter,
                        includeEssentiality,
                    },
                });
            }
        } catch (error) {
            console.warn('Error refreshing structural annotation track:', error);
        }
    }, [viewState, geneViewerConfig.tracks, includeEssentiality]);

    useEffect(() => {
        handleTrackRefresh();
    }, [handleTrackRefresh]);

    const handleRefreshTracks = useCallback(() => {
        if (viewState) {
            refreshStructuralAnnotationTrack(viewState);
        }
    }, [viewState]);

    // Handle feature selection from JBrowse
    const handleFeatureSelect = useCallback((feature: any) => {
        setSelectedFeature(feature);
    }, []);

    // Handle closing the feature panel
    const handleCloseFeaturePanel = useCallback(() => {
        setSelectedFeature(null);
    }, []);

    const handleError = useCallback((error: Error, errorInfo: React.ErrorInfo) => {
        console.error('GeneViewerPage error:', error, errorInfo);
    }, []);

    const selectedGenomes = useMemo(() => geneViewerData.genomeMeta ? [{
        isolate_name: geneViewerData.genomeMeta.isolate_name,
        type_strain: geneViewerData.genomeMeta.type_strain || false
    }] : [], [geneViewerData.genomeMeta]);

    // Create shared handleToggleFacet for FeaturePanel to use the same mechanism as facet checkboxes
    const selectedSpeciesFromStore = useFilterStore(state => state.selectedSpecies);
    const geneSearchQuery = useFilterStore(state => state.geneSearchQuery);
    const { handleToggleFacet, facets } = useFacetedFilters({
        selectedSpecies: selectedSpeciesFromStore,
        selectedGenomes,
        searchQuery: geneSearchQuery,
    });

    const linkData = useMemo(() => ({
        template: '/genome/${strain_name}?locus_tag=${locus_tag}',
        alias: 'Browse'
    }), []);

    const handleRemoveGenome = useCallback(() => {
        // Not used in single genome view
    }, []);

    // Callback to handle page size changes
    const handlePageSizeChange = useCallback((newPageSize: number) => {
        setPageSize(newPageSize);
        if (geneViewerData.genomeMeta) {
            geneViewerSearch.handleGeneSearch(newPageSize);
        }
    }, [geneViewerData.genomeMeta, geneViewerSearch]);

    // Memoize the loading spinner to prevent unnecessary re-renders
    const spinner = useMemo(() => {
        if (!debouncedLoading) return null;
        
        return (
            <div className={styles.spinnerOverlay}>
                <div className={styles.spinner}></div>
            </div>
        );
    }, [debouncedLoading]);

    return (
        <ErrorBoundary onError={handleError}>
            <div className={styles.geneViewerPage}>
                {spinner}

                {/* Error display - commented out to hide error messages */}
                {/* {errorMessage && (
                  <div className={styles.errorMessage}>
                    <p>Error: {errorMessage}</p>
                  </div>
                )} */}

                <div className={`vf-content ${styles.vfContent}`}>
                    <div className={styles.spacer}></div>
                </div>
                <div className={`vf-content ${styles.vfContent}`}>
                    <span className={styles.hidden}><p>placeholder</p></span>
                </div>

                <section className={styles.geneViewerMain}>
                    {/* Header with breadcrumbs and metadata */}
                    <GeneViewerHeader genomeMeta={geneViewerData.genomeMeta}/>

                    {/* Controls */}
                    <GeneViewerControls
                        genomeMeta={geneViewerData.genomeMeta}
                        includeEssentiality={includeEssentiality}
                        onEssentialityToggle={handleEssentialityToggle}
                    />

                    {/* Main content grid: JBrowse/Search on left, Feature Panel on right */}
                    <div className={styles.mainContentGrid}>
                        {/* Left column: JBrowse viewer and search/facets */}
                        <div className={styles.leftColumn}>
                            {/* JBrowse Viewer Container */}
                            <div className={styles.jbrowseSection}>
                                <GeneViewerContent
                                    viewState={viewState}
                                    onRefreshTracks={handleRefreshTracks}
                                    onFeatureSelect={handleFeatureSelect}
                                />
                            </div>
                            
                            {/* Auto-Switch Notification Bar - positioned below JBrowse */}
                            {showAutoSwitchNotification && activeTab === 'sync' && wasAutoSwitched && (
                                <div className={styles.syncNotificationBar}>
                                    <div className={styles.syncNotificationContent}>
                                        <span className={styles.syncNotificationIcon}>🔄</span>
                                        <span className={styles.syncNotificationText}>
                                            View automatically switched to <strong>Genomic Context</strong> to show genes in the current viewport.
                                        </span>
                                        <div className={styles.syncNotificationActions}>
                                            <button 
                                                className={styles.syncNotificationButton}
                                                onClick={handleSwitchToSearch}
                                            >
                                                Switch back to Search View
                                            </button>
                                            <button 
                                                className={styles.syncNotificationDismiss}
                                                onClick={handleDismissNotification}
                                                aria-label="Dismiss notification"
                                            >
                                                ×
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Gene Search Section - Below the JBrowse viewer */}
                            <div className={styles.geneSearchContainer}>
                                <section>
                                    {/* Tab Navigation */}
                                    <TabNavigation
                                        tabs={[
                                            { id: 'search', label: 'Search View' },
                                            { id: 'sync', label: 'Genomic Context' },
                                        ]}
                                        activeTab={activeTab}
                                        onTabClick={(tabId) => {
                                            const newTab = tabId as 'search' | 'sync';
                                            setActiveTab(newTab);
                                            // Reset notification when manually switching tabs
                                            if (newTab === 'search') {
                                                setShowAutoSwitchNotification(false);
                                                setWasAutoSwitched(false);
                                            }
                                        }}
                                    />
                                    
                                    {/* Tab Content */}
                                    {activeTab === 'search' ? (
                                        <GeneSearchForm
                                            searchQuery={filterStore.geneSearchQuery}
                                            onSearchQueryChange={() => {
                                            }}
                                            onSearchSubmit={() => {
                                                // GeneSearchForm handles search internally
                                            }}
                                            selectedSpecies={[]}
                                            selectedGenomes={selectedGenomes}
                                            results={geneViewerSearch.geneResults}
                                            onSortClick={geneViewerSearch.handleGeneSortClick}
                                            sortField={filterStore.geneSortField}
                                            sortOrder={filterStore.geneSortOrder}
                                            linkData={linkData}
                                            viewState={viewState || undefined}
                                            setLoading={geneViewerData.setLoading}
                                            handleRemoveGenome={handleRemoveGenome}
                                            onPageSizeChange={handlePageSizeChange}
                                            onPageChange={geneViewerSearch.handlePageChange}
                                            currentPage={geneViewerSearch.currentPage}
                                            totalPages={geneViewerSearch.totalPages}
                                            hasPrevious={geneViewerSearch.hasPrevious}
                                            hasNext={geneViewerSearch.hasNext}
                                            totalCount={geneViewerSearch.totalCount}
                                            onFeatureSelect={handleFeatureSelect}
                                            hideActionsColumn={true}
                                        />
                                    ) : (
                                        <SyncView
                                            viewState={viewState || undefined}
                                            selectedGenomes={selectedGenomes}
                                            setLoading={geneViewerData.setLoading}
                                            onFeatureSelect={handleFeatureSelect}
                                            linkData={linkData}
                                        />
                                    )}
                                </section>
                            </div>
                        </div>

                        {/* Right column: Feature Panel */}
                        <div className={styles.rightColumn}>
                            <FeaturePanel 
                                feature={selectedFeature}
                                onClose={handleCloseFeaturePanel}
                                viewState={viewState || undefined}
                                setLoading={geneViewerData.setLoading}
                                activeTab={activeTab}
                                onSwitchToSearch={() => setActiveTab('search')}
                                onToggleFacet={handleToggleFacet}
                                facets={facets}
                            />
                        </div>
                    </div>
                </section>
            </div>
        </ErrorBoundary>
    );
};

export default GeneViewerPage;

