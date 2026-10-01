import React from 'react';
import GeneResultsTable from '../GeneResultsHandler/GeneResultsTable';
import Pagination from '@components/molecules/Pagination';
import {createViewState} from '@jbrowse/react-app2';
import {GeneMeta} from '../../../../interfaces/Gene';
import {LinkData} from '../../../../interfaces/Auxiliary';
import {DEFAULT_PER_PAGE_CNT} from '../../../../utils/common/constants';
import {copyToClipboard, generateCurlRequest, generateHttpRequest} from '../../../../utils/api';
import styles from './GeneSearchForm.module.scss';

type ViewModel = ReturnType<typeof createViewState>;

interface GeneSearchResultsPanelProps {
    results: GeneMeta[];
    onSortClick: (sortField: string, sortOrder: 'asc' | 'desc') => void;
    linkData: LinkData;
    viewState?: ViewModel;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
    isTypeStrainAvailable: boolean;
    onDownloadTSV: () => void;
    isDownloading: boolean;
    sortField: string;
    sortOrder: 'asc' | 'desc';
    onFeatureSelect?: (feature: any) => void;
    hideActionsColumn?: boolean;
    pageSize: number;
    onPageSizeChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
    currentPage: number;
    totalPages: number;
    hasPrevious: boolean;
    hasNext: boolean;
    onPageClick: (page: number) => void;
    apiRequestDetails: {
        url: string;
        method: string;
        headers: Record<string, string>;
        params?: Record<string, string>;
        body?: unknown;
    } | null;
}

const GeneSearchResultsPanel: React.FC<GeneSearchResultsPanelProps> = ({
    results,
    onSortClick,
    linkData,
    viewState,
    setLoading,
    isTypeStrainAvailable,
    onDownloadTSV,
    isDownloading,
    sortField,
    sortOrder,
    onFeatureSelect,
    hideActionsColumn = false,
    pageSize,
    onPageSizeChange,
    currentPage,
    totalPages,
    hasPrevious,
    hasNext,
    onPageClick,
    apiRequestDetails,
}) => {
    const showPagination =
        results.length > 0 && (totalPages > 1 || hasNext || hasPrevious);

    return (
        <>
            <div
                className="vf-grid__col--span-3"
                id="results-table"
                style={{display: results.length > 0 ? 'block' : 'none'}}
            >
                <GeneResultsTable
                    results={results}
                    onSortClick={onSortClick}
                    linkData={linkData}
                    viewState={viewState}
                    setLoading={setLoading}
                    isTypeStrainAvailable={isTypeStrainAvailable}
                    onDownloadTSV={onDownloadTSV}
                    isLoading={isDownloading}
                    sortField={sortField}
                    sortOrder={sortOrder}
                    onFeatureSelect={onFeatureSelect}
                    tableSource="search-table"
                    hideActionsColumn={hideActionsColumn}
                />
                <div className={styles.paginationContainer}>
                    <div className={styles.pageSizeDropdown}>
                        <label htmlFor="pageSize">Page Size: </label>
                        <select
                            id="pageSize"
                            value={pageSize}
                            onChange={onPageSizeChange}
                            className={styles.pageSizeSelect}
                        >
                            <option value={DEFAULT_PER_PAGE_CNT}>Show 10</option>
                            <option value={20}>Show 20</option>
                            <option value={50}>Show 50</option>
                        </select>
                    </div>
                    <div className={styles.paginationBar}>
                        {showPagination && (
                            <Pagination
                                currentPage={currentPage}
                                totalPages={totalPages}
                                hasPrevious={hasPrevious}
                                hasNext={hasNext}
                                onPageClick={onPageClick}
                            />
                        )}
                    </div>
                </div>
            </div>
            <div>
                <p />
            </div>
            <div className={styles.rightPaneButtons}>
                <button
                    className="vf-button vf-button--primary vf-button--sm"
                    onClick={() => copyToClipboard(generateCurlRequest(apiRequestDetails))}
                >
                    Copy cURL Request
                </button>
                <button
                    className="vf-button vf-button--primary vf-button--sm"
                    onClick={() => copyToClipboard(generateHttpRequest(apiRequestDetails))}
                >
                    Copy HTTP Request
                </button>
            </div>
            <div>
                <p />
            </div>
            <div>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
                <p>&nbsp;</p>
            </div>
        </>
    );
};

export default GeneSearchResultsPanel;
