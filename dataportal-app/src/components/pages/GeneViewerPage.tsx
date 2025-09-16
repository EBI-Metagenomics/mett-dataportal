import React, {useEffect, useState, useCallback, useMemo, useRef} from 'react';
import useGeneViewerState from '@components/features/gene-viewer/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/features/gene-viewer/GeneSearchForm/GeneSearchForm";

// Import new hooks and utilities
import {useGeneViewerData, useGeneViewerNavigation, useGeneViewerSearch} from '../../hooks';
import {useGeneViewerUrlSync} from '../../hooks/useGeneViewerUrlSync';
import {useDebouncedLoading} from '../../hooks/useDebouncedLoading';

import {refreshStructuralAnnotationTrack, useGeneViewerConfig} from '../../utils/gene-viewer';
import {GeneViewerContent, GeneViewerControls, GeneViewerHeader} from '../features/gene-viewer/GeneViewerUI';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import {useFilterStore} from '../../stores/filterStore';
import {DEFAULT_PER_PAGE_CNT} from '../../utils/common/constants';

// Import PyHMMER integration component
import { PyhmmerIntegration } from '../features/pyhmmer/feature-panel/PyhmmerIntegration';

const GeneViewerPage: React.FC = () => {
    const renderCount = useRef(0);
    renderCount.current += 1;

    // Get state from Zustand stores
    const filterStore = useFilterStore();

    // URL synchronization for gene viewer
    useGeneViewerUrlSync();

    // Local state
    const [height] = useState(450);
    const [pageSize, setPageSize] = useState(DEFAULT_PER_PAGE_CNT);

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

    // Only re-initialize JBrowse view state when genome changes
    const lastGenomeRef = React.useRef<string | null>(null);
    const [jbrowseInitKey, setJbrowseInitKey] = useState(0);

    useEffect(() => {
        if (geneViewerData.genomeMeta?.isolate_name !== lastGenomeRef.current) {
            lastGenomeRef.current = geneViewerData.genomeMeta?.isolate_name || null;
            setJbrowseInitKey((k) => k + 1); // force re-init
        }
    }, [geneViewerData.genomeMeta?.isolate_name]);

    const {viewState, initializationError} = useGeneViewerState(
        geneViewerConfig.assembly,
        geneViewerConfig.tracks,
        geneViewerConfig.sessionConfig,
        geneViewerData.genomeMeta?.isolate_name || '',
        jbrowseInitKey
    );

    const handleTrackRefresh = useCallback(() => {
        console.log('🔧 handleTrackRefresh called with:', { includeEssentiality, hasViewState: !!viewState });
        
        if (!viewState) return;
        
        const session = viewState.session;
        const view = session.views[0];
        if (!view) return;

        try {
            console.log('🔧 Hiding track: structural_annotation');
            view.hideTrack('structural_annotation');

            const newTrack = geneViewerConfig.tracks.find(
                (track: any) => track.trackId === 'structural_annotation'
            );
            console.log('🔧 Found track:', newTrack?.trackId, 'with adapter:', newTrack?.adapter?.type);
            
            if (newTrack) {
                console.log('🔧 Showing track with includeEssentiality:', includeEssentiality);
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
        console.log('🔧 Track refresh effect triggered');
        handleTrackRefresh();
    }, [handleTrackRefresh]);

    // Navigation logic
    const navigation = useGeneViewerNavigation({
        viewState,
        geneMeta: geneViewerData.geneMeta,
        loading: geneViewerData.loading,
        setLoading: geneViewerData.setLoading,
    });

    const handleRefreshTracks = useCallback(() => {
        if (viewState) {
            refreshStructuralAnnotationTrack(viewState);
        }
    }, [viewState]);

    const handleError = useCallback((error: Error, errorInfo: React.ErrorInfo) => {
        console.error('GeneViewerPage error:', error, errorInfo);
    }, []);

    const selectedGenomes = useMemo(() => geneViewerData.genomeMeta ? [{
        isolate_name: geneViewerData.genomeMeta.isolate_name,
        type_strain: geneViewerData.genomeMeta.type_strain || false
    }] : [], [geneViewerData.genomeMeta]);

    const linkData = useMemo(() => ({
        template: '/genome/${strain_name}?locus_tag=${locus_tag}',
        alias: 'Browse'
    }), []);

    const handleRemoveGenome = useCallback((isolate_name: string) => {
        // if needed
    }, []);

    // Callback to handle page size changes (same pattern as HomePage)
    const handlePageSizeChange = useCallback((newPageSize: number) => {
        console.log('GeneViewerPage - handlePageSizeChange called with:', newPageSize);
        setPageSize(newPageSize);
    }, []);

    // Memoize the loading spinner to prevent unnecessary re-renders
    const spinner = useMemo(() => {
        if (!debouncedLoading) return null;
        
        return (
            <div className={styles.spinnerOverlay}>
                <div className={styles.spinner}></div>
            </div>
        );
    }, [debouncedLoading]);

    // Memoize error message to prevent unnecessary re-renders
    const errorMessage = useMemo(() => {
        return geneViewerData.error || 
               navigation.navigationError || 
               (initializationError ? initializationError.toString() : null);
    }, [geneViewerData.error, navigation.navigationError, initializationError]);

    return (
        <ErrorBoundary onError={handleError}>
            <div>
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

                <section>
                    {/* Header with breadcrumbs and metadata */}
                    <GeneViewerHeader genomeMeta={geneViewerData.genomeMeta}/>

                    {/* Controls */}
                    <GeneViewerControls
                        genomeMeta={geneViewerData.genomeMeta}
                        includeEssentiality={includeEssentiality}
                        onEssentialityToggle={handleEssentialityToggle}
                    />

                    {/* Main JBrowse content */}
                    <GeneViewerContent
                        viewState={viewState}
                        height={height}
                        onRefreshTracks={handleRefreshTracks}
                        // Feature selection is now handled by JBrowse's built-in feature panel
                    />

                    {/* PyHMMER Integration - handles all PyHMMER functionality */}
                    <PyhmmerIntegration />

                    {/* Instructions for JBrowse Integration */}
                    <div className={styles.pyhmmerIntegration}> 
                        {/* PyHMMER search links will use CSS classes from the module */}
                    </div>

                    {/* Gene Search Section */}
                    <div className={styles.geneSearchContainer}>
                        <section>
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
                            />
                        </section>
                    </div>
                </section>
            </div>
        </ErrorBoundary>
    );
};

export default GeneViewerPage;

