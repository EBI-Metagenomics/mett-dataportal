import React, {useEffect, useState, useCallback, useMemo, useRef} from 'react';
import useGeneViewerState from '@components/organisms/Gene/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/organisms/Gene/GeneSearchForm/GeneSearchForm";

// Import new hooks and utilities
import {useGeneViewerData, useGeneViewerNavigation, useGeneViewerSearch} from '../../hooks';
import {useGeneViewerUrlSync} from '../../hooks/useGeneViewerUrlSync';
import {useDebouncedLoading} from '../../hooks/useDebouncedLoading';
import {refreshStructuralAnnotationTrack, useGeneViewerConfig} from '../../utils/geneViewerConfig';
import {GeneViewerContent, GeneViewerControls, GeneViewerHeader} from '../organisms/Gene/GeneViewerUI';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import {useFilterStore} from '../../stores/filterStore';

const GeneViewerPage: React.FC = () => {
    const renderCount = useRef(0);
    renderCount.current += 1;

    // Get state from Zustand stores
    const filterStore = useFilterStore();

    // URL synchronization for gene viewer
    useGeneViewerUrlSync();

    // Local state
    const [height] = useState(450);
    const [includeEssentiality, setIncludeEssentiality] = useState(true);

    // Custom hooks for data management
    const geneViewerData = useGeneViewerData();
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

    // Memoize selected genomes to prevent unnecessary re-renders
    const selectedGenomes = useMemo(() => {
        console.log('GeneViewerPage selectedGenomes:', geneViewerConfig.selectedGenomes, 'genomeMeta:', geneViewerData.genomeMeta);
        return geneViewerConfig.selectedGenomes;
    }, [geneViewerConfig.selectedGenomes, geneViewerData.genomeMeta]);

    const linkData = useMemo(() => ({
        template: '/genome/${strain_name}',
        alias: 'Select'
    }), []);

    const handleRemoveGenome = useCallback((isolate_name: string) => {
        // if needed
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

    // Debug: Log when loading state changes
    useEffect(() => {
        if (process.env.NODE_ENV === 'development') {
            console.log('Loading state changed:', geneViewerData.loading, 'Debounced:', debouncedLoading);
        }
    }, [geneViewerData.loading, debouncedLoading]);

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
                    <div style={{height: '20px'}}></div>
                </div>
                <div className={`vf-content ${styles.vfContent}`}>
                    <span style={{display: 'none'}}><p>placeholder</p></span>
                </div>

                <section>
                    {/* Header with breadcrumbs and metadata */}
                    <GeneViewerHeader genomeMeta={geneViewerData.genomeMeta}/>

                    {/* Controls */}
                    <GeneViewerControls
                        genomeMeta={geneViewerData.genomeMeta}
                        includeEssentiality={includeEssentiality}
                        onEssentialityToggle={setIncludeEssentiality}
                    />

                    {/* Main JBrowse content */}
                    <GeneViewerContent
                        viewState={viewState}
                        height={height}
                        onRefreshTracks={handleRefreshTracks}
                    />

                    {/* Gene Search Section */}
                    <div className={styles.geneSearchContainer}>
                        <section>
                            <GeneSearchForm
                                searchQuery={filterStore.geneSearchQuery}
                                onSearchQueryChange={() => {
                                }}
                                onSearchSubmit={geneViewerSearch.handleGeneSearch}
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
                            />
                        </section>
                    </div>
                </section>
            </div>
        </ErrorBoundary>
    );
};

export default GeneViewerPage;

