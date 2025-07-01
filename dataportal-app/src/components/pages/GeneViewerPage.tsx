import React, { useState, useEffect } from 'react';
import useGeneViewerState from '@components/organisms/Gene/GeneViewer/geneViewerState';
import styles from "./GeneViewerPage.module.scss";
import GeneSearchForm from "@components/organisms/Gene/GeneSearchForm/GeneSearchForm";

// Import new hooks and utilities
import { 
  useGeneViewerData, 
  useGeneViewerNavigation, 
  useGeneViewerSearch,
  useGeneViewerUrlSync
} from '../../hooks';
import { 
  useGeneViewerConfig, 
  refreshStructuralAnnotationTrack 
} from '../../utils/geneViewerConfig';
import { 
  GeneViewerHeader, 
  GeneViewerControls, 
  GeneViewerContent 
} from '../features/gene-viewer';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import { useFilterStore } from '../../stores/filterStore';

const GeneViewerPage: React.FC = () => {
  // Get state from Zustand stores
  const filterStore = useFilterStore();
  
  // URL synchronization for gene viewer
  useGeneViewerUrlSync();
  
  // Local state
  const [height, setHeight] = useState(450);
  const [includeEssentiality, setIncludeEssentiality] = useState(true);

  // Custom hooks for data management
  const geneViewerData = useGeneViewerData();
  const geneViewerSearch = useGeneViewerSearch({
    genomeMeta: geneViewerData.genomeMeta,
    setLoading: geneViewerData.setLoading,
  });

  // JBrowse configuration
  const geneViewerConfig = useGeneViewerConfig(
    geneViewerData.genomeMeta,
    geneViewerData.geneMeta,
    includeEssentiality
  );

  // JBrowse state management
  const { viewState, initializationError } = useGeneViewerState(
    geneViewerConfig.assembly,
    geneViewerConfig.tracks,
    geneViewerConfig.sessionConfig,
    geneViewerData.genomeMeta?.isolate_name || ''
  );

  // Navigation logic
  const navigation = useGeneViewerNavigation({
    viewState,
    geneMeta: geneViewerData.geneMeta,
    loading: geneViewerData.loading,
    setLoading: geneViewerData.setLoading,
  });

  // Wait until assembly is ready
  useEffect(() => {
    const checkAssemblyReady = setInterval(() => {
      if (geneViewerConfig.assembly) {
        clearInterval(checkAssemblyReady);
      }
    }, 100);

    return () => clearInterval(checkAssemblyReady);
  }, [geneViewerConfig.assembly]);

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

  // Link data for gene search
  const linkData = {
    template: '/genome/${strain_name}',
    alias: 'Select'
  };

  // Handle genome removal (placeholder for now)
  const handleRemoveGenome = (isolate_name: string) => {
    // This could be implemented if needed
  };

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
        
        {/* Error display */}
        {errorMessage && (
          <div className={styles.errorMessage}>
            <p>Error: {errorMessage}</p>
          </div>
        )}

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
                onSearchQueryChange={e => filterStore.setGeneSearchQuery(e.target.value)}
                onSearchSubmit={geneViewerSearch.handleGeneSearch}
                selectedSpecies={[]} // Empty for gene viewer
                selectedGenomes={geneViewerConfig.selectedGenomes}
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

