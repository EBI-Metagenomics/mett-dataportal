import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom'
import GeneSearchForm from '@components/organisms/Gene/GeneSearchForm/GeneSearchForm';
import GenomeSearchForm from '@components/organisms/Genome/GenomeSearchForm/GenomeSearchForm';
import PyhmmerSearchForm from '@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchForm';
import styles from "@components/pages/HomePage.module.scss";
import HomePageHeadBand from "@components/organisms/HeadBand/HomePageHeadBand";

// Import new hooks and stores
import { useFilterStore } from '../../stores/filterStore';
import { useGenomeData, useGeneData } from '../../hooks';
import { useTabAwareUrlSync } from '../../hooks/useTabAwareUrlSync';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import { determineActiveTab, DEFAULT_TAB_SELECTION_CONFIG } from '../../utils/tabSelection';

// Define the type for each tab
interface Tab {
    id: string;
    label: string;
}

// Define the props for TabNavigation component
interface TabNavigationProps {
    tabs: Tab[];
    activeTab: string;
    onTabClick: (tabId: string) => void;
}

const TabNavigation: React.FC<TabNavigationProps> = ({ tabs, activeTab, onTabClick }) => (
    <div className={styles["tabs-container"]}>
        {tabs.map((tab) => (
            <button
                key={tab.id}
                onClick={() => onTabClick(tab.id)}
                className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
            >
                {tab.label}
            </button>
        ))}
    </div>
);

const HomePage: React.FC = () => {
    const location = useLocation();
    
    // Get state from Zustand stores
    const filterStore = useFilterStore();
    
    // Use custom hooks for data management
    const genomeData = useGenomeData();
    const geneData = useGeneData();
    
    // Local state for UI
    const [activeTab, setActiveTab] = useState('genomes');
    const hasUserSelectedTab = useRef(false);

    // Only use URL to set the initial tab
    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const tabFromUrl = searchParams.get('tab');
        
        if (tabFromUrl && ['genomes', 'genes', 'proteinsearch'].includes(tabFromUrl) && !hasUserSelectedTab.current) {
            setActiveTab(tabFromUrl);
        }
    }, [activeTab, location.pathname, location.search]);

    // URL sync for tab-aware state management
    useTabAwareUrlSync(activeTab);

    // Link data for components
    const geneLinkData = {
        template: '/genome/${strain_name}?locus_tag=${locus_tag}',
        alias: 'Browse'
    };

    const genomeLinkData = {
        template: '/genome/${strain_name}',
        alias: 'Browse'
    };

    // Tab labels
    const tabs: Tab[] = [
        { id: 'genomes', label: 'Genomes' },
        { id: 'genes', label: 'Genes' },
        { id: 'proteinsearch', label: 'Protein Search' },
    ];

    // Reset filters when switching tabs
    const handleTabClick = (tabId: string) => {
        if (tabId !== activeTab) {
            // Reset all store state when switching tabs
            filterStore.setGenomeSearchQuery('');
            filterStore.setGenomeSortField('species');
            filterStore.setGenomeSortOrder('asc');
            filterStore.setGeneSearchQuery('');
            filterStore.setGeneSortField('locus_tag');
            filterStore.setGeneSortOrder('asc');
            filterStore.setFacetedFilters({});
            filterStore.setFacetOperators({});
            filterStore.setSelectedGenomes([]);
            filterStore.setSelectedSpecies([]);
            filterStore.setSelectedTypeStrains([]);
            
            // Set the new active tab
            setActiveTab(tabId);
            hasUserSelectedTab.current = true;
        }
    };

    // Error handling
    const handleError = (error: Error, errorInfo: React.ErrorInfo) => {
        console.error('HomePage error:', error, errorInfo);
        // Could send to error reporting service here
    };

    return (
        <ErrorBoundary onError={handleError}>
            <div>
                {/* Loading spinner */}
                {genomeData.loading && (
                    <div className={styles.spinnerOverlay}>
                        <div className={styles.spinner}></div>
                    </div>
                )}
                
                {/* Error display */}
                {genomeData.error && (
                    <div className={styles.errorMessage}>
                        <p>Error: {genomeData.error}</p>
                    </div>
                )}
                
                <div>
                    <HomePageHeadBand
                        typeStrains={genomeData.typeStrains}
                        linkTemplate="/genome/$strain_name"
                        speciesList={genomeData.speciesList}
                        selectedSpecies={filterStore.selectedSpecies}
                        handleSpeciesSelect={genomeData.handleSpeciesSelect}
                    />
                </div>

                <div className="layout-container">
                    <div>
                        <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={handleTabClick} />
                        
                        {activeTab === 'genomes' && (
                            <ErrorBoundary>
                                <GenomeSearchForm
                                    searchQuery={filterStore.genomeSearchQuery}
                                    onSearchQueryChange={e => filterStore.setGenomeSearchQuery(e.target.value)}
                                    onSearchSubmit={genomeData.handleGenomeSearch}
                                    selectedSpecies={filterStore.selectedSpecies}
                                    selectedTypeStrains={filterStore.selectedTypeStrains}
                                    typeStrains={genomeData.typeStrains}
                                    onSortClick={genomeData.handleGenomeSortClick}
                                    sortField={filterStore.genomeSortField}
                                    sortOrder={filterStore.genomeSortOrder}
                                    results={genomeData.genomeResults}
                                    selectedGenomes={genomeData.selectedGenomes}
                                    onToggleGenomeSelect={genomeData.handleToggleGenomeSelect}
                                    handleTypeStrainToggle={genomeData.handleTypeStrainToggle}
                                    handleRemoveGenome={genomeData.handleRemoveGenome}
                                    linkData={genomeLinkData}
                                    setLoading={genomeData.setLoading}
                                />
                            </ErrorBoundary>
                        )}

                        {activeTab === 'genes' && (
                            <ErrorBoundary>
                                <GeneSearchForm
                                    searchQuery={filterStore.geneSearchQuery}
                                    onSearchQueryChange={e => filterStore.setGeneSearchQuery(e.target.value)}
                                    onSearchSubmit={geneData.handleGeneSearch}
                                    selectedSpecies={filterStore.selectedSpecies}
                                    selectedGenomes={geneData.selectedGenomes}
                                    results={geneData.geneResults}
                                    onSortClick={geneData.handleGeneSortClick}
                                    sortField={filterStore.geneSortField}
                                    sortOrder={filterStore.geneSortOrder}
                                    linkData={geneLinkData}
                                    handleRemoveGenome={geneData.handleRemoveGenome}
                                    setLoading={geneData.setLoading}
                                />
                            </ErrorBoundary>
                        )}
                        
                        {activeTab === 'proteinsearch' && (
                            <ErrorBoundary>
                                <PyhmmerSearchForm />
                            </ErrorBoundary>
                        )}
                    </div>
                </div>
            </div>
        </ErrorBoundary>
    );
};

export default HomePage;
