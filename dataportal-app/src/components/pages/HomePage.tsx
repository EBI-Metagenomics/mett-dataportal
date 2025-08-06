import React, {useEffect, useRef, useState, useCallback} from 'react';
import {useLocation} from 'react-router-dom'
import GeneSearchForm from '@components/organisms/Gene/GeneSearchForm/GeneSearchForm';
import GenomeSearchForm from '@components/organisms/Genome/GenomeSearchForm/GenomeSearchForm';
import PyhmmerSearchForm from '@components/organisms/Pyhmmer/PyhmmerSearchForm/PyhmmerSearchForm';
import {useFeatureFlags} from '../../hooks/useFeatureFlags';
import styles from "@components/pages/HomePage.module.scss";
import HomePageHeadBand from "@components/organisms/HeadBand/HomePageHeadBand";


import {useFilterStore} from '../../stores/filterStore';
import {useGenomeData} from '../../hooks';
import {useTabAwareUrlSync} from '../../hooks/useTabAwareUrlSync';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import {GeneService} from '../../services/geneService';
import {DEFAULT_PER_PAGE_CNT} from '../../utils/appConstants';
import { convertFacetedFiltersToLegacy, convertFacetOperatorsToLegacy } from '../../utils/filterUtils';

interface Tab {
    id: string;
    label: string;
}

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

    const filterStore = useFilterStore();

    const genomeData = useGenomeData();
    const {isFeatureEnabled} = useFeatureFlags();

    const [activeTab, setActiveTab] = useState('genomes');
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [geneLoading, setGeneLoading] = useState(false);
    const [genePagination, setGenePagination] = useState<any>(null);
    const [genePerPage, setGenePerPage] = useState(DEFAULT_PER_PAGE_CNT);

    const hasUserSelectedTab = useRef(false);
    const hasLoadedInitialGenes = useRef(false);

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

    // Load initial gene data when genes tab is selected
    useEffect(() => {
        if (activeTab === 'genes' && !hasLoadedInitialGenes.current) {
            hasLoadedInitialGenes.current = true;
            setGeneLoading(true);

            // Load initial gene data
            GeneService.fetchGeneSearchResultsAdvanced(
                '', // empty query for initial load
                1, // page
                genePerPage, // perPage - use state instead of hardcoded 20
                'locus_tag',
                'asc',
                [], // selectedGenomes
                [], // selectedSpecies
                convertFacetedFiltersToLegacy(filterStore.facetedFilters), // Convert to legacy format
                convertFacetOperatorsToLegacy(filterStore.facetOperators)  // Convert to legacy format
            )
                .then((response: any) => {
                    setGeneResults(response.data || []);
                    setGenePagination(response.pagination || null);
                })
                .catch((error: any) => {
                    console.error('Failed to load initial gene data:', error);
                })
                .finally(() => {
                    setGeneLoading(false);
                });
        }
    }, [activeTab, genePerPage]);

    // Reload initial data when search query is cleared
    useEffect(() => {
        if (activeTab === 'genes' && filterStore.geneSearchQuery === '') {
            console.log('HomePage - Search query cleared, reloading initial data');
            setGeneLoading(true);

            // Convert faceted filters to legacy format
            const legacyFilters = convertFacetedFiltersToLegacy(filterStore.facetedFilters);
            const legacyOperators = convertFacetOperatorsToLegacy(filterStore.facetOperators);

            // Load initial gene data
            GeneService.fetchGeneSearchResultsAdvanced(
                '', // empty query for initial load
                1, // page
                genePerPage, // perPage - use state instead of hardcoded 20
                'locus_tag',
                'asc',
                [], // selectedGenomes
                [], // selectedSpecies
                legacyFilters, // Convert to legacy format
                legacyOperators  // Convert to legacy format
            )
                .then((response: any) => {
                    // console.log('HomePage - Reload API response:', response);
                    setGeneResults(response.data || []);
                    setGenePagination(response.pagination || null);
                })
                .catch((error: any) => {
                    console.error('Failed to reload initial gene data:', error);
                })
                .finally(() => {
                    setGeneLoading(false);
                });
        }
    }, [activeTab, filterStore.geneSearchQuery, genePerPage]);

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


    useTabAwareUrlSync(activeTab);

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
            // Reset search
            filterStore.setGenomeSearchQuery('');
            filterStore.setGenomeSortField('species');
            filterStore.setGenomeSortOrder('asc');
            filterStore.setGeneSearchQuery('');
            filterStore.setGeneSortField('locus_tag');
            filterStore.setGeneSortOrder('asc');
            filterStore.setFacetedFilters({});
            filterStore.setFacetOperators({});

            // Reset gene results when switching away from genes tab
            if (activeTab === 'genes' && tabId !== 'genes') {
                setGeneResults([]);
                hasLoadedInitialGenes.current = false;
            }

            if (tabId === 'proteinsearch') {
                filterStore.setSelectedSpecies([]);
                filterStore.setSelectedGenomes([]);
            } else if (tabId === 'genes') {
                filterStore.setSelectedTypeStrains([]);
            } else {
                filterStore.setSelectedTypeStrains([]);
            }

            setActiveTab(tabId);
            hasUserSelectedTab.current = true;
        }
    };

    // Callback to handle results updates from GeneSearchForm
    const handleGeneResultsUpdate = useCallback((results: any[], pagination: any) => {
        console.log('HomePage - handleGeneResultsUpdate called with:', {
            resultsCount: results.length,
            pagination
        });
        setGeneResults(results);
        setGenePagination(pagination);
    }, []);

    // Callback to handle page size changes from GeneSearchForm
    const handleGenePageSizeChange = useCallback((newPageSize: number) => {
        console.log('HomePage - handleGenePageSizeChange called with:', newPageSize);
        setGenePerPage(newPageSize);
    }, []);

    // Error handling
    const handleError = (error: Error, errorInfo: React.ErrorInfo) => {
        console.error('HomePage error:', error, errorInfo);
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

                {/* Gene loading spinner */}
                {activeTab === 'genes' && geneLoading && (
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
                                    onSearchQueryChange={(e) => {
                                        // GeneSearchForm manages its own state
                                        filterStore.setGeneSearchQuery(e.target.value);
                                    }}
                                    onSearchSubmit={() => {
                                        // GeneSearchForm manages its own search
                                    }}
                                    selectedSpecies={filterStore.selectedSpecies}
                                    selectedGenomes={filterStore.selectedGenomes}
                                    results={geneResults} // Pass actual results
                                    onSortClick={(field, order) => {
                                        filterStore.setGeneSortField(field);
                                        filterStore.setGeneSortOrder(order);
                                    }}
                                    sortField={filterStore.geneSortField}
                                    sortOrder={filterStore.geneSortOrder}
                                    linkData={geneLinkData}
                                    handleRemoveGenome={(genomeId) => {
                                        // Remove genome from selected genomes
                                        const updatedGenomes = filterStore.selectedGenomes.filter(
                                            genome => genome.isolate_name !== genomeId
                                        );
                                        filterStore.setSelectedGenomes(updatedGenomes);
                                    }}
                                    setLoading={(loading) => {
                                        // GeneSearchForm manages its own loading state
                                        console.log('GeneSearchForm loading state:', loading);
                                    }}
                                    // Add pagination props for HomePage
                                    currentPage={genePagination?.current_page || genePagination?.page_number || 1}
                                    totalPages={genePagination?.total_pages || genePagination?.num_pages || 1}
                                    hasPrevious={genePagination?.has_previous || false}
                                    hasNext={genePagination?.has_next || false}
                                    totalCount={genePagination?.total_count || genePagination?.total || 0}
                                    onResultsUpdate={handleGeneResultsUpdate}
                                    onPageSizeChange={handleGenePageSizeChange}
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
