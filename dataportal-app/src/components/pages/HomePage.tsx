import React, {useEffect, useRef, useState} from 'react';
import {useLocation} from 'react-router-dom'
import GeneSearchForm from '@components/organisms/Gene/GeneSearchForm/GeneSearchForm';
import GenomeSearchForm from '@components/organisms/Genome/GenomeSearchForm/GenomeSearchForm';
import PyhmmerSearchForm from '@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchForm';
import { useFeatureFlags } from '../../hooks/useFeatureFlags';
import styles from "@components/pages/HomePage.module.scss";
import HomePageHeadBand from "@components/organisms/HeadBand/HomePageHeadBand";

// Import new hooks and stores
import {useFilterStore} from '../../stores/filterStore';
import {useGenomeData} from '../../hooks';
import {useTabAwareUrlSync} from '../../hooks/useTabAwareUrlSync';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';

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

const TabNavigation: React.FC<TabNavigationProps> = ({tabs, activeTab, onTabClick}) => (
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
    const { isFeatureEnabled } = useFeatureFlags();
    
    // Note: GeneSearchForm manages its own state, so we don't need useGeneData here

    // Local state for UI
    const [activeTab, setActiveTab] = useState('genomes');

    // console.log('🏠 HomePage render:', {
    //     activeTab: activeTab,
    //     selectedSpecies: filterStore.selectedSpecies,
    //     selectedSpeciesLength: filterStore.selectedSpecies.length
    // });
    const hasUserSelectedTab = useRef(false);

    // Only use URL to set the initial tab
    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const tabFromUrl = searchParams.get('tab');

        if (tabFromUrl && ['genomes', 'genes', 'proteinsearch'].includes(tabFromUrl) && !hasUserSelectedTab.current) {
            // If proteinsearch tab is requested but not enabled, default to genomes
            if (tabFromUrl === 'proteinsearch' && !isFeatureEnabled('pyhmmer_search')) {
                setActiveTab('genomes');
            } else {
                setActiveTab(tabFromUrl);
            }
        }
    }, [location.pathname, location.search, isFeatureEnabled]);

    // Clean up gene viewer state when returning to home page
    useEffect(() => {
        // If we have locus_tag in URL, we're coming from gene viewer
        // Clear any gene viewer specific state
        if (location.search.includes('locus_tag')) {
            filterStore.setGeneSearchQuery('');
            filterStore.setGeneSortField('locus_tag');
            filterStore.setGeneSortOrder('asc');
            filterStore.setFacetedFilters({});
            filterStore.setFacetOperators({});
        }
    }, [location.search]);

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
        {id: 'genomes', label: 'Genomes'},
        {id: 'genes', label: 'Genes'},
        ...(isFeatureEnabled('pyhmmer_search') ? [{id: 'proteinsearch', label: 'Search by Protein'}] : []),
    ];

    // Reset filters when switching tabs
    const handleTabClick = (tabId: string) => {
        if (tabId !== activeTab) {
            // Reset search queries and sorting, but preserve species selection for genes tab
            filterStore.setGenomeSearchQuery('');
            filterStore.setGenomeSortField('species');
            filterStore.setGenomeSortOrder('asc');
            filterStore.setGeneSearchQuery('');
            filterStore.setGeneSortField('locus_tag');
            filterStore.setGeneSortOrder('asc');
            filterStore.setFacetedFilters({});
            filterStore.setFacetOperators({});

            // Only clear species selection when switching to proteinsearch
            if (tabId === 'proteinsearch') {
                filterStore.setSelectedSpecies([]);
                filterStore.setSelectedGenomes([]);
            }
            // For genes tab, preserve species selection but clear type strains
            else if (tabId === 'genes') {
                filterStore.setSelectedTypeStrains([]);
            }
            // For genomes tab, preserve species selection
            else {
                filterStore.setSelectedTypeStrains([]);
            }

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
                        <TabNavigation tabs={tabs} activeTab={activeTab} onTabClick={handleTabClick}/>

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
                                    onSearchQueryChange={() => {
                                    }} // GeneSearchForm manages its own state
                                    onSearchSubmit={() => {
                                    }}
                                    selectedSpecies={filterStore.selectedSpecies}
                                    selectedGenomes={filterStore.selectedGenomes}
                                    results={[]} // GeneSearchForm manages its own results
                                    onSortClick={(field, order) => {
                                        filterStore.setGeneSortField(field);
                                        filterStore.setGeneSortOrder(order);
                                    }}
                                    sortField={filterStore.geneSortField}
                                    sortOrder={filterStore.geneSortOrder}
                                    linkData={geneLinkData}
                                    handleRemoveGenome={() => {
                                    }} // GeneSearchForm manages its own genome removal
                                    setLoading={() => {
                                    }} // GeneSearchForm manages its own loading state
                                />
                            </ErrorBoundary>
                        )}

                        {activeTab === 'proteinsearch' && isFeatureEnabled('pyhmmer_search') && (
                            <ErrorBoundary>
                                <PyhmmerSearchForm/>
                            </ErrorBoundary>
                        )}
                    </div>
                </div>
            </div>
        </ErrorBoundary>
    );
};

export default HomePage;
