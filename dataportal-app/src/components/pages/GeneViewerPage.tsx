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

// Import custom feature panel
import FeaturePanel from '../features/gene-viewer/FeaturePanel/FeaturePanel';

const GeneViewerPage: React.FC = () => {
    const renderCount = useRef(0);
    renderCount.current += 1;

    // Get state from Zustand stores
    const filterStore = useFilterStore();

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

    // Only re-initialize JBrowse view state when genome changes
    const lastGenomeRef = React.useRef<string | null>(null);
    const [jbrowseInitKey, setJbrowseInitKey] = useState(0);

    useEffect(() => {
        if (geneViewerData.genomeMeta?.isolate_name !== lastGenomeRef.current) {
            lastGenomeRef.current = geneViewerData.genomeMeta?.isolate_name || null;
            setJbrowseInitKey((k) => k + 1); // force re-init
        }
    }, [geneViewerData.genomeMeta?.isolate_name]);

    const {viewState} = useGeneViewerState(
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

                            {/* Gene Search Section - Below the JBrowse viewer */}
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
                                        onPageChange={geneViewerSearch.handlePageChange}
                                        currentPage={geneViewerSearch.currentPage}
                                        totalPages={geneViewerSearch.totalPages}
                                        hasPrevious={geneViewerSearch.hasPrevious}
                                        hasNext={geneViewerSearch.hasNext}
                                        totalCount={geneViewerSearch.totalCount}
                                    />
                                </section>
                            </div>
                        </div>

                        {/* Right column: Feature Panel */}
                        <div className={styles.rightColumn}>
                            <FeaturePanel 
                                feature={selectedFeature}
                                onClose={handleCloseFeaturePanel}
                            />
                        </div>
                    </div>
                </section>
            </div>
        </ErrorBoundary>
    );
};

export default GeneViewerPage;

