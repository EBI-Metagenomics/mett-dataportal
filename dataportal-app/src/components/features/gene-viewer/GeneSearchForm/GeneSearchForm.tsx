import React from 'react';
import {createViewState} from '@jbrowse/react-app2';
import {LinkData} from '../../../../interfaces/Auxiliary';
import {BaseGenome} from '../../../../interfaces/Genome';
import styles from './GeneSearchForm.module.scss';
import GeneSearchBar from './GeneSearchBar';
import GeneSearchSidebar from './GeneSearchSidebar';
import GeneSearchResultsPanel from './GeneSearchResultsPanel';
import {useGeneSearchController} from './hooks/useGeneSearchController';

type ViewModel = ReturnType<typeof createViewState>;

export interface GeneSearchFormProps {
    searchQuery: string;
    /** Kept for call-site compatibility; search input is owned by the form controller. */
    onSearchQueryChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    /** Kept for call-site compatibility; submit is owned by the form controller. */
    onSearchSubmit?: () => void;
    selectedSpecies?: string[];
    results: any[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    sortField: string;
    sortOrder: 'asc' | 'desc';
    selectedGenomes: BaseGenome[];
    linkData: LinkData;
    viewState?: ViewModel;
    handleRemoveGenome: (genomeId: string) => void;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    currentPage?: number;
    totalPages?: number;
    hasPrevious?: boolean;
    hasNext?: boolean;
    totalCount?: number;
    onResultsUpdate?: (results: any[], pagination: any) => void;
    onPageSizeChange?: (newPageSize: number) => void;
    onPageChange?: (page: number) => void;
    onFeatureSelect?: (feature: any) => void;
    hideActionsColumn?: boolean;
    sidebarPortalId?: string;
    extraIsolates?: string[];
}

const GeneSearchForm: React.FC<GeneSearchFormProps> = ({
    selectedSpecies,
    onSortClick,
    selectedGenomes,
    linkData,
    viewState,
    sortField,
    sortOrder,
    setLoading,
    searchQuery,
    results: resultsProp,
    currentPage: currentPageProp,
    totalPages: totalPagesProp,
    hasPrevious: hasPreviousProp,
    hasNext: hasNextProp,
    onResultsUpdate,
    onPageSizeChange,
    onPageChange,
    onFeatureSelect,
    hideActionsColumn = false,
    sidebarPortalId,
    extraIsolates = [],
}) => {
    const {
        searchInput,
        suggestions,
        setSuggestions,
        facets,
        handleToggleFacet,
        handleOperatorChange,
        hasActiveFacets,
        handleClearAllFacets,
        activeSearchLabel,
        handleClearSearch,
        handleInputChange,
        handleSuggestionClick,
        handleSearch,
        handleSubmit,
        handleDownloadTSV,
        handlePageSizeChange,
        handlePageClick,
        pageSize,
        isDownloading,
        apiRequestDetails,
        displayResults,
        displayCurrentPage,
        displayTotalPages,
        displayHasPrevious,
        displayHasNext,
    } = useGeneSearchController({
        searchQuery,
        selectedSpecies,
        selectedGenomes,
        extraIsolates,
        sortField,
        sortOrder,
        setLoading,
        resultsProp,
        currentPageProp,
        totalPagesProp,
        hasPreviousProp,
        hasNextProp,
        onResultsUpdate,
        onPageSizeChange,
        onPageChange,
    });

    return (
        <section id="genes">
            <div>
                <p />
            </div>
            <GeneSearchSidebar
                sidebarPortalId={sidebarPortalId}
                activeSearchLabel={activeSearchLabel}
                onClearSearch={handleClearSearch}
                facets={facets}
                onToggleFacet={handleToggleFacet}
                onOperatorChange={handleOperatorChange}
                hasActiveFacets={hasActiveFacets}
                onClearAllFacets={handleClearAllFacets}
            />
            <div className={sidebarPortalId ? styles.rightPaneFlush : styles.rightPane}>
                <GeneSearchBar
                    searchInput={searchInput}
                    suggestions={suggestions}
                    onInputChange={handleInputChange}
                    onSuggestionClick={handleSuggestionClick}
                    onSuggestionsClear={() => setSuggestions([])}
                    onSearch={handleSearch}
                    onClear={handleClearSearch}
                    onSubmit={handleSubmit}
                />
                <div>
                    <p>&nbsp;</p>
                </div>
                <GeneSearchResultsPanel
                    results={displayResults}
                    onSortClick={onSortClick}
                    linkData={linkData}
                    viewState={viewState}
                    setLoading={setLoading}
                    isTypeStrainAvailable={
                        selectedGenomes.length
                            ? selectedGenomes.some((genome) => genome.type_strain)
                            : true
                    }
                    onDownloadTSV={handleDownloadTSV}
                    isDownloading={isDownloading}
                    sortField={sortField}
                    sortOrder={sortOrder}
                    onFeatureSelect={onFeatureSelect}
                    hideActionsColumn={hideActionsColumn}
                    pageSize={pageSize}
                    onPageSizeChange={handlePageSizeChange}
                    currentPage={displayCurrentPage}
                    totalPages={displayTotalPages}
                    hasPrevious={displayHasPrevious}
                    hasNext={displayHasNext}
                    onPageClick={handlePageClick}
                    apiRequestDetails={apiRequestDetails}
                />
            </div>
        </section>
    );
};

export default GeneSearchForm;
