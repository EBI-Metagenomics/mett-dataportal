import React, {useEffect, useRef, useState, useCallback, useMemo} from 'react';
import {useLocation} from 'react-router-dom'
import GeneSearchForm from '@components/features/gene-viewer/GeneSearchForm/GeneSearchForm';
import GenomeSearchForm from '@components/features/genome/GenomeSearchForm/GenomeSearchForm';
import PyhmmerSearchForm from '@components/features/pyhmmer/PyhmmerSearchForm/PyhmmerSearchForm';
import {useFeatureFlags} from '../../hooks/useFeatureFlags';
import styles from "@components/pages/HomePage.module.scss";
import HomePageHeadBand from "@components/organisms/HeadBand/HomePageHeadBand";
import Breadcrumb from '@components/molecules/Breadcrumb';
import HomepageFilterRail from '@components/Filters/HomepageFilterRail';
import SpeciesFilter from '@components/Filters/SpeciesFilter';
import GenomeFacetedFilter from '@components/Filters/GenomeFacetedFilter';
import ActiveFilters, {ActiveFilterItem} from '@components/Filters/ActiveFilters';
import {compareTypeStrainIsolates} from '../../utils/common/homePageConstants';


import {useFilterStore} from '../../stores/filterStore';
import {useGenomeData} from '../../hooks';
import {useTabAwareUrlSync} from '../../hooks/useTabAwareUrlSync';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import {GeneService} from '../../services/gene';
import { convertFacetedFiltersToLegacy, convertFacetOperatorsToLegacy } from '../../utils/common/filterUtils';

const GENE_FILTER_SLOT_ID = 'homepage-gene-filters';

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
    const {isFeatureEnabled, loading: featuresLoading} = useFeatureFlags();

    const [activeTab, setActiveTab] = useState(() => {
        const tab = new URLSearchParams(window.location.search).get('tab');
        return tab === 'genes' || tab === 'proteinsearch' || tab === 'genomes' ? tab : 'genomes';
    });
    const [geneResults, setGeneResults] = useState<any[]>([]);
    const [geneLoading, setGeneLoading] = useState(false);
    const [genePagination, setGenePagination] = useState<any>(null);
    const [genePerPage, setGenePerPage] = useState(10); 

    const hasUserSelectedTab = useRef(false);
    const hasLoadedInitialGenes = useRef(false);

    // Only use URL to set the initial tab
    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const tabFromUrl = searchParams.get('tab');

        if (tabFromUrl && ['genomes', 'genes', 'proteinsearch'].includes(tabFromUrl) && !hasUserSelectedTab.current) {
            if (tabFromUrl === 'proteinsearch' && featuresLoading) {
                return;
            }
            // If proteinsearch tab is requested but not enabled, default to genomes
            if (tabFromUrl === 'proteinsearch' && !isFeatureEnabled('pyhmmer_search')) {
                setActiveTab('genomes');
            } else {
                setActiveTab(tabFromUrl);
            }
        }
    }, [location.pathname, location.search, isFeatureEnabled, featuresLoading]);

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
                filterStore.selectedGenomes,
                filterStore.selectedSpecies,
                convertFacetedFiltersToLegacy(filterStore.facetedFilters),
                convertFacetOperatorsToLegacy(filterStore.facetOperators),
                undefined // No locus_tag for initial load
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
                filterStore.selectedGenomes,
                filterStore.selectedSpecies,
                legacyFilters,
                legacyOperators,
                undefined // No locus_tag for reload
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

    // Species is shared by the genome and gene tabs.
    // Type strains apply only to the genome table.
    // Genomes added for gene search stay selected across those two tabs.
    // The gene viewer does not read this homepage selection; it passes its own genome.
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

    // Context-aware species selection handler
    const handleSpeciesSelect = async (species_acronym: string): Promise<void> => {
        if (activeTab === 'genes') {
            const updatedSelectedSpecies = filterStore.selectedSpecies.includes(species_acronym)
                ? filterStore.selectedSpecies.filter((acronym) => acronym !== species_acronym)
                : [...filterStore.selectedSpecies, species_acronym];
            
            filterStore.setSelectedSpecies(updatedSelectedSpecies);

            setGeneLoading(true);
            try {
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    filterStore.geneSearchQuery,
                    1,
                    genePerPage,
                    filterStore.geneSortField,
                    filterStore.geneSortOrder,
                    filterStore.selectedGenomes,
                    updatedSelectedSpecies,
                    convertFacetedFiltersToLegacy(filterStore.facetedFilters),
                    convertFacetOperatorsToLegacy(filterStore.facetOperators)
                );
                setGeneResults(response.data || []);
                setGenePagination(response.pagination || null);

            } catch (error) {
                console.error('Error fetching gene data after species selection:', error);
            } finally {
                setGeneLoading(false);
            }
        } else {
            await genomeData.handleSpeciesSelect(species_acronym);
        }
    };

    const orderedSpecies = useMemo(() => {
        const leadIsolate = (acronym: string) => {
            const isolates = genomeData.typeStrains
                .filter((strain) => strain.species_acronym === acronym)
                .map((strain) => strain.isolate_name)
                .sort(compareTypeStrainIsolates);
            return isolates[0];
        };

        return [...genomeData.speciesList].sort((left, right) => {
            const leftIsolate = leadIsolate(left.acronym);
            const rightIsolate = leadIsolate(right.acronym);
            if (leftIsolate && rightIsolate) {
                const byStrain = compareTypeStrainIsolates(leftIsolate, rightIsolate);
                if (byStrain !== 0) {
                    return byStrain;
                }
            } else if (leftIsolate) {
                return -1;
            } else if (rightIsolate) {
                return 1;
            }
            return left.scientific_name.localeCompare(right.scientific_name);
        });
    }, [genomeData.speciesList, genomeData.typeStrains]);

    const handleResetFilters = async (): Promise<void> => {
        filterStore.setSelectedSpecies([]);
        filterStore.setSelectedTypeStrains([]);
        filterStore.setSelectedGenomes([]);
        filterStore.clearFacetedFilters();

        if (activeTab === 'genes') {
            setGeneLoading(true);
            try {
                const response = await GeneService.fetchGeneSearchResultsAdvanced(
                    filterStore.geneSearchQuery,
                    1,
                    genePerPage,
                    filterStore.geneSortField,
                    filterStore.geneSortOrder,
                    [],
                    [],
                    {},
                    {}
                );
                setGeneResults(response.data || []);
                setGenePagination(response.pagination || null);
            } catch (error) {
                console.error('Error fetching gene data after resetting filters:', error);
            } finally {
                setGeneLoading(false);
            }
        }
    };

    const activeFilterItems: ActiveFilterItem[] = [
        ...filterStore.selectedSpecies.map((acronym) => ({
            id: `species-${acronym}`,
            label: genomeData.speciesList.find((species) => species.acronym === acronym)?.scientific_name || acronym,
            onRemove: () => {
                void handleSpeciesSelect(acronym);
            },
        })),
        ...(activeTab === 'genomes'
            ? filterStore.selectedTypeStrains.map((isolateName) => ({
                id: `strain-${isolateName}`,
                label: isolateName,
                onRemove: () => genomeData.handleTypeStrainToggle(isolateName),
            }))
            : []),
        ...filterStore.selectedGenomes.map((genome) => ({
            id: `genome-${genome.isolate_name}`,
            label: genome.isolate_name,
            onRemove: () => filterStore.removeSelectedGenome(genome.isolate_name),
        })),
    ];

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

                {/* Breadcrumb Navigation */}
                <Breadcrumb currentPage="home" />

                <div>
                    <HomePageHeadBand
                        typeStrains={genomeData.typeStrains}
                        linkTemplate="/genome/$strain_name"
                        speciesList={genomeData.speciesList}
                    />
                </div>

                <div className="layout-container">
                    <div className={activeTab === 'proteinsearch' ? undefined : styles.browseLayout}>
                        {activeTab !== 'proteinsearch' && (
                            <HomepageFilterRail
                                title={activeTab === 'genes' ? 'Filter genes' : 'Filter genomes'}
                            >
                                <ActiveFilters items={activeFilterItems} onClearAll={handleResetFilters} />
                                <SpeciesFilter
                                    speciesList={orderedSpecies}
                                    selectedSpecies={filterStore.selectedSpecies}
                                    onSpeciesSelect={handleSpeciesSelect}
                                />
                                {activeTab === 'genomes' && (
                                    <GenomeFacetedFilter
                                        typeStrains={genomeData.typeStrains}
                                        selectedTypeStrains={filterStore.selectedTypeStrains}
                                        selectedSpecies={filterStore.selectedSpecies}
                                        onTypeStrainToggle={genomeData.handleTypeStrainToggle}
                                        showChrome={false}
                                    />
                                )}
                                {activeTab === 'genes' && <div id={GENE_FILTER_SLOT_ID} />}
                            </HomepageFilterRail>
                        )}
                        <div className={activeTab === 'proteinsearch' ? undefined : styles.browseMain}>
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
                                    hideSidebar
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
                                    onSortClick={async (field, order) => {
                                        console.log('HomePage - Sort clicked:', { field, order });
                                        filterStore.setGeneSortField(field);
                                        filterStore.setGeneSortOrder(order);
                                        
                                        // Trigger a new search with updated sort parameters
                                        setGeneLoading(true);
                                        try {
                                            console.log('HomePage - Making API call with sort params:', {
                                                query: filterStore.geneSearchQuery,
                                                field,
                                                order,
                                                genomes: filterStore.selectedGenomes.length,
                                                species: filterStore.selectedSpecies.length
                                            });
                                            
                                            const response = await GeneService.fetchGeneSearchResultsAdvanced(
                                                filterStore.geneSearchQuery,
                                                1, // Reset to page 1 when sorting
                                                genePerPage,
                                                field,
                                                order,
                                                filterStore.selectedGenomes,
                                                filterStore.selectedSpecies,
                                                convertFacetedFiltersToLegacy(filterStore.facetedFilters),
                                                convertFacetOperatorsToLegacy(filterStore.facetOperators)
                                            );
                                            
                                            console.log('HomePage - Sort API response:', {
                                                dataLength: response.data?.length || 0,
                                                pagination: response.pagination
                                            });
                                            
                                            setGeneResults(response.data || []);
                                            setGenePagination(response.pagination || null);
                                        } catch (error) {
                                            console.error('Error fetching gene data after sort:', error);
                                        } finally {
                                            setGeneLoading(false);
                                        }
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
                                        // Use the same full-page spinner for all gene tab activity,
                                        // including faceted filter loading triggered inside GeneSearchForm.
                                        setGeneLoading(loading);
                                    }}
                                    // Add pagination props for HomePage
                                    currentPage={genePagination?.current_page || genePagination?.page_number || 1}
                                    totalPages={genePagination?.total_pages || genePagination?.num_pages || 1}
                                    hasPrevious={genePagination?.has_previous || false}
                                    hasNext={genePagination?.has_next || false}
                                    totalCount={genePagination?.total_count || genePagination?.total || 0}
                                    onResultsUpdate={handleGeneResultsUpdate}
                                    onPageSizeChange={handleGenePageSizeChange}
                                    sidebarPortalId={GENE_FILTER_SLOT_ID}
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
            </div>
        </ErrorBoundary>
    );
};

export default HomePage;
