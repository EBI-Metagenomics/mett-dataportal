import React, { useState, useEffect } from 'react';
import useGeneViewerState from '@components/organisms/Gene/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/organisms/Gene/GeneSearchForm/GeneSearchForm";

// Import new hooks and utilities
import { 
  useGeneViewerData, 
  useGeneViewerNavigation, 
  useGeneViewerSearch
} from '../../hooks';
import { useGeneViewerUrlSync } from '../../hooks/useGeneViewerUrlSync';
import { 
  useGeneViewerConfig, 
  refreshStructuralAnnotationTrack 
} from '../../utils/geneViewerConfig';
import { 
  GeneViewerHeader, 
  GeneViewerControls, 
  GeneViewerContent 
} from '../organisms/Gene/GeneViewerUI';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import { useFilterStore } from '../../stores/filterStore';

const GeneViewerPage: React.FC = () => {
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

  // At the top level, call the hook as usual (no useMemo)
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

  const { viewState, initializationError } = useGeneViewerState(
    geneViewerConfig.assembly,
    geneViewerConfig.tracks,
    geneViewerConfig.sessionConfig,
    geneViewerData.genomeMeta?.isolate_name || '',
    jbrowseInitKey
  );

  // When includeEssentiality changes, update the track in the existing view state
  useEffect(() => {
    if (!viewState) return;
    const session = viewState.session;
    const view = session.views[0];
    if (!view) return;

    // Hide the track
    view.hideTrack('structural_annotation');

    // Find the new config for the track
    const newTrack = geneViewerConfig.tracks.find(
      (track: any) => track.trackId === 'structural_annotation'
    );
    if (newTrack) {
      // Show the track with the new config (forces refresh)
      view.showTrack('structural_annotation', {
        ...newTrack,
        adapter: {
          ...newTrack.adapter,
          includeEssentiality,
        },
      });
    }
  }, [includeEssentiality, viewState, geneViewerConfig.tracks]);

  // Navigation logic
  const navigation = useGeneViewerNavigation({
    viewState,
    geneMeta: geneViewerData.geneMeta,
    loading: geneViewerData.loading,
    setLoading: geneViewerData.setLoading,
  });

  // Handle track refresh
  const handleRefreshTracks = () => {
    if (viewState) {
      refreshStructuralAnnotationTrack(viewState);
    }
  };

  // Error handling
  const handleError = (error: Error, errorInfo: React.ErrorInfo) => {
    console.error('GeneViewerPage error:', error, errorInfo);
  };

  // Memoize props to prevent unnecessary re-renders and API calls
  const selectedGenomes = React.useMemo(
    () => {
      console.log('GeneViewerPage selectedGenomes:', geneViewerConfig.selectedGenomes, 'genomeMeta:', geneViewerData.genomeMeta);
      return geneViewerConfig.selectedGenomes;
    },
    [geneViewerConfig.selectedGenomes, geneViewerData.genomeMeta]
  );

  const linkData = React.useMemo(() => ({
    template: '/genome/${strain_name}',
    alias: 'Select'
  }), []);

  // Handle genome removal (placeholder for now)
  const handleRemoveGenome = React.useCallback((isolate_name: string) => {
    // This could be implemented if needed
  }, []);

  // Loading spinner
  const spinner = geneViewerData.loading && (
    <div className={styles.spinnerOverlay}>
      <div className={styles.spinner}></div>
    </div>
  );

  // Get error message
  const errorMessage = geneViewerData.error || navigation.navigationError || (initializationError ? initializationError.toString() : null);

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
          <GeneViewerHeader genomeMeta={geneViewerData.genomeMeta} />

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
                onSearchQueryChange={() => {}} // GeneSearchForm manages its own state
                onSearchSubmit={geneViewerSearch.handleGeneSearch}
                selectedSpecies={[]} // Empty for gene viewer
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

