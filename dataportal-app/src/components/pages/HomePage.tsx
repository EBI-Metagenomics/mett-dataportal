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

import {useFilterStore} from '../../stores/filterStore';
import {useGenomeData} from '../../hooks';
import {useTabAwareUrlSync} from '../../hooks/useTabAwareUrlSync';
import ErrorBoundary from '../shared/ErrorBoundary/ErrorBoundary';
import {GeneService} from '../../services/gene';
import {
    buildFacetActiveFilterItems,
    compareFilterValues,
    convertFacetedFiltersToLegacy,
    convertFacetOperatorsToLegacy,
} from '../../utils/common/filterUtils';
import {
    geneQueryGenomes,
    looksLikeLocusTag,
} from '../features/gene-viewer/GeneSearchForm/utils/geneSearchHelpers';

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
    // Invalidates in-flight HomePage gene fetches when GeneSearchForm publishes newer results.
    const geneFetchGenerationRef = useRef(0);

    const beginGeneFetch = useCallback(() => {
        geneFetchGenerationRef.current += 1;
        return geneFetchGenerationRef.current;
    }, []);

    const applyGeneFetchIfCurrent = useCallback((generation: number, results: any[], pagination: any) => {
        if (generation !== geneFetchGenerationRef.current) {
            return false;
        }
        setGeneResults(results);
        setGenePagination(pagination);
        return true;
    }, []);

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

    // Load initial gene data once when genes tab is selected.
    // GeneSearchForm owns subsequent search/suggestion/clear fetches via onResultsUpdate.
    useEffect(() => {
        if (activeTab !== 'genes' || hasLoadedInitialGenes.current) {
            return;
        }
        hasLoadedInitialGenes.current = true;
        const generation = beginGeneFetch();
        setGeneLoading(true);

        GeneService.fetchGeneSearchResultsAdvanced(
            '',
            1,
            genePerPage,
            'locus_tag',
            'asc',
            geneQueryGenomes(filterStore.selectedGenomes, filterStore.selectedTypeStrains),
            filterStore.selectedSpecies,
            convertFacetedFiltersToLegacy(filterStore.facetedFilters),
            convertFacetOperatorsToLegacy(filterStore.facetOperators),
            undefined
        )
            .then((response: any) => {
                applyGeneFetchIfCurrent(generation, response.data || [], response.pagination || null);
            })
            .catch((error: any) => {
                console.error('Failed to load initial gene data:', error);
            })
            .finally(() => {
                if (generation === geneFetchGenerationRef.current) {
                    setGeneLoading(false);
                }
            });
        // Intentionally once per genes-tab entry; GeneSearchForm handles later refetches.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, genePerPage, beginGeneFetch, applyGeneFetchIfCurrent]);

    // Clean up gene-viewer deep-link state when returning home with ?locus_tag=...
    // Do not match geneSortField=locus_tag (that substring false-positive was clearing facet selections).
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        if (!params.has('locus_tag')) {
            return;
        }
        filterStore.setGeneSearchQuery('');
        filterStore.setGeneSortField('locus_tag');
        filterStore.setGeneSortOrder('asc');
        filterStore.setFacetedFilters({});
        filterStore.setFacetOperators({});
        // eslint-disable-next-line react-hooks/exhaustive-deps -- only react to deep-link locus_tag param
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

    // Species and type strains stay selected across the genome and gene tabs.
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
                filterStore.setSelectedTypeStrains([]);
            }

            setActiveTab(tabId);
            hasUserSelectedTab.current = true;
        }
    };

    // GeneSearchForm is the source of truth for search/suggestion/clear results.
    const handleGeneResultsUpdate = useCallback((results: any[], pagination: any) => {
        beginGeneFetch(); // invalidate any in-flight HomePage gene fetches
        setGeneResults(results);
        setGenePagination(pagination);
    }, [beginGeneFetch]);

    const fetchGenesForFilters = useCallback(async (
        species: string[],
        typeStrains: string[],
        genomes: { isolate_name: string; type_strain: boolean }[],
        searchQuery = filterStore.geneSearchQuery,
    ) => {
        const generation = beginGeneFetch();
        setGeneLoading(true);
        const locusTag = looksLikeLocusTag(searchQuery) ? searchQuery : undefined;
        const textQuery = locusTag ? '' : searchQuery;
        try {
            const response = await GeneService.fetchGeneSearchResultsAdvanced(
                textQuery,
                1,
                genePerPage,
                filterStore.geneSortField,
                filterStore.geneSortOrder,
                geneQueryGenomes(genomes, typeStrains),
                species,
                convertFacetedFiltersToLegacy(filterStore.facetedFilters),
                convertFacetOperatorsToLegacy(filterStore.facetOperators),
                locusTag
            );
            applyGeneFetchIfCurrent(generation, response.data || [], response.pagination || null);
        } catch (error) {
            console.error('Error fetching gene data:', error);
        } finally {
            if (generation === geneFetchGenerationRef.current) {
                setGeneLoading(false);
            }
        }
    }, [
        beginGeneFetch,
        applyGeneFetchIfCurrent,
        genePerPage,
        filterStore.geneSearchQuery,
        filterStore.geneSortField,
        filterStore.geneSortOrder,
        filterStore.facetedFilters,
        filterStore.facetOperators,
    ]);

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
            await fetchGenesForFilters(
                updatedSelectedSpecies,
                filterStore.selectedTypeStrains,
                filterStore.selectedGenomes
            );
        } else {
            await genomeData.handleSpeciesSelect(species_acronym);
        }
    };

    const handleTypeStrainToggle = async (isolateName: string): Promise<void> => {
        if (activeTab !== 'genes') {
            await genomeData.handleTypeStrainToggle(isolateName);
            return;
        }

        const updatedTypeStrains = filterStore.selectedTypeStrains.includes(isolateName)
            ? filterStore.selectedTypeStrains.filter((name) => name !== isolateName)
            : [...filterStore.selectedTypeStrains, isolateName];
        filterStore.setSelectedTypeStrains(updatedTypeStrains);
        await fetchGenesForFilters(
            filterStore.selectedSpecies,
            updatedTypeStrains,
            filterStore.selectedGenomes
        );
    };

    const orderedSpecies = useMemo(() => {
        return [...genomeData.speciesList].sort((left, right) =>
            left.scientific_name.localeCompare(right.scientific_name, undefined, {sensitivity: 'base'})
        );
    }, [genomeData.speciesList]);

    const handleResetFilters = async (): Promise<void> => {
        filterStore.setSelectedSpecies([]);
        filterStore.setSelectedTypeStrains([]);
        filterStore.setSelectedGenomes([]);
        filterStore.clearFacetedFilters();
        filterStore.setGeneSearchQuery('');

        if (activeTab === 'genes') {
            await fetchGenesForFilters([], [], [], '');
        }
    };

    const handleClearGeneSearch = useCallback(async () => {
        const species = filterStore.selectedSpecies;
        const typeStrains = filterStore.selectedTypeStrains;
        const genomes = filterStore.selectedGenomes;
        filterStore.setGeneSearchQuery('');
        if (activeTab === 'genes') {
            await fetchGenesForFilters(species, typeStrains, genomes, '');
        }
    }, [
        activeTab,
        fetchGenesForFilters,
        filterStore.selectedSpecies,
        filterStore.selectedTypeStrains,
        filterStore.selectedGenomes,
        filterStore.setGeneSearchQuery,
    ]);

    const removeFacetValue = useCallback((facetGroup: string, value: string | boolean) => {
        const current = filterStore.facetedFilters[facetGroup as keyof typeof filterStore.facetedFilters] || [];
        const next = (current as (string | boolean)[]).filter(
            (entry) => !compareFilterValues(entry, value)
        );
        filterStore.updateFacetedFilter(
            facetGroup as keyof typeof filterStore.facetedFilters,
            next
        );
    }, [filterStore]);

    const activeFilterItems: ActiveFilterItem[] = [
        ...filterStore.selectedSpecies.map((acronym) => ({
            id: `species-${acronym}`,
            label: genomeData.speciesList.find((species) => species.acronym === acronym)?.scientific_name || acronym,
            onRemove: () => {
                void handleSpeciesSelect(acronym);
            },
        })),
        ...filterStore.selectedTypeStrains.map((isolateName) => ({
            id: `strain-${isolateName}`,
            label: isolateName,
            onRemove: () => {
                void handleTypeStrainToggle(isolateName);
            },
        })),
        ...filterStore.selectedGenomes.map((genome) => ({
            id: `genome-${genome.isolate_name}`,
            label: genome.isolate_name,
            onRemove: () => filterStore.removeSelectedGenome(genome.isolate_name),
        })),
        ...(filterStore.geneSearchQuery && activeTab === 'genes'
            ? [{
                id: `gene-search-${filterStore.geneSearchQuery}`,
                label: filterStore.geneSearchQuery,
                onRemove: () => {
                    void handleClearGeneSearch();
                },
            }]
            : []),
        ...(activeTab === 'genes'
            ? buildFacetActiveFilterItems(filterStore.facetedFilters).map((item) => ({
                id: item.id,
                label: item.label,
                onRemove: () => removeFacetValue(String(item.facetGroup), item.value),
            }))
            : []),
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
                                    defaultCollapsed={activeTab === 'genes'}
                                />
                                {(activeTab === 'genomes' || activeTab === 'genes') && (
                                    <GenomeFacetedFilter
                                        typeStrains={genomeData.typeStrains}
                                        selectedTypeStrains={filterStore.selectedTypeStrains}
                                        selectedSpecies={filterStore.selectedSpecies}
                                        onTypeStrainToggle={handleTypeStrainToggle}
                                        showChrome={false}
                                        defaultCollapsed={activeTab === 'genes'}
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
                                    extraIsolates={filterStore.selectedTypeStrains}
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
                                                geneQueryGenomes(filterStore.selectedGenomes, filterStore.selectedTypeStrains),
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
