import React, { useState } from 'react';
import { 
    formatEValue, 
    formatBitScore, 
    formatSequence,
    PYHMMER_CONFIG,
    PYHMMER_ERROR_MESSAGES
} from '../../../../utils/pyhmmer';
import { PyhmmerCompactResultsProps } from '../../../../utils/pyhmmer';
import styles from './PyhmmerResultsCore.module.scss';

const PyhmmerResultsCore: React.FC<PyhmmerCompactResultsProps> = ({
    results = [],
    loading = false,
    error,
    maxResults = PYHMMER_CONFIG.MAX_RESULTS_DISPLAY,
    showPagination = true,
    showDownload = true,
    onResultClick,
    onDownload,
    compact = false,
    className = ''
}) => {
    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const [resultsPerPage] = useState(compact ? 5 : 20);
    
    // Calculate pagination
    const totalPages = Math.ceil(results.length / resultsPerPage);
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = startIndex + resultsPerPage;
    const currentResults = results.slice(startIndex, endIndex);
    
    // Handle page change
    const handlePageChange = (page: number) => {
        setCurrentPage(page);
    };
    
    // Handle result click
    const handleResultClick = (result: any) => {
        onResultClick?.(result);
    };
    
    // Handle download
    const handleDownload = (format: string) => {
        onDownload?.(format);
    };
    
    // Render loading state
    if (loading) {
        return (
            <div className={`${styles.pyhmmerResultsCore} ${compact ? styles.compact : ''} ${className}`}>
                <div className={styles.loadingState}>
                    <div className={styles.spinner}></div>
                    <p>Loading results...</p>
                </div>
            </div>
        );
    }
    
    // Render error state
    if (error) {
        return (
            <div className={`${styles.pyhmmerResultsCore} ${compact ? styles.compact : ''} ${className}`}>
                <div className={styles.errorState}>
                    <div className={styles.errorIcon}>⚠️</div>
                    <h3>Error Loading Results</h3>
                    <p>{error}</p>
                </div>
            </div>
        );
    }
    
    // Render no results state
    if (results.length === 0) {
        return (
            <div className={`${styles.pyhmmerResultsCore} ${compact ? styles.compact : ''} ${className}`}>
                <div className={styles.noResultsState}>
                    <div className={styles.noResultsIcon}>🔍</div>
                    <h3>No Results Found</h3>
                    <p>Try adjusting your search parameters or using a different sequence.</p>
                </div>
            </div>
        );
    }
    
    // Render results summary
    const renderResultsSummary = () => {
        const totalGenes = results.length;
        const totalDomains = results.reduce((sum, result) => sum + (result.num_hits || 0), 0);
        const significantDomains = results.reduce((sum, result) => sum + (result.num_significant || 0), 0);
        
        return (
            <div className={styles.resultsSummary}>
                <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Total Genes:</span>
                    <span className={styles.summaryValue}>{totalGenes}</span>
                </div>
                <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Total Domains:</span>
                    <span className={styles.summaryValue}>{totalDomains}</span>
                </div>
                <div className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>Significant Domains:</span>
                    <span className={styles.summaryValue}>{significantDomains}</span>
                </div>
            </div>
        );
    };
    
    // Render individual result row
    const renderResultRow = (result: any, index: number) => {
        const isSignificant = result.is_significant;
        const hasDomains = result.domains && result.domains.length > 0;
        
        return (
            <div 
                key={`${result.target}-${index}`}
                className={`${styles.resultRow} ${isSignificant ? styles.significant : styles.notSignificant}`}
                onClick={() => handleResultClick?.(result)}
            >
                <div className={styles.resultHeader}>
                    <div className={styles.targetInfo}>
                        <h4 className={styles.targetName}>{result.target}</h4>
                        {result.description && (
                            <p className={styles.targetDescription}>{result.description}</p>
                        )}
                    </div>
                    <div className={styles.resultStats}>
                        <div className={styles.statItem}>
                            <span className={styles.statLabel}>E-value:</span>
                            <span className={styles.statValue}>{result.evalue}</span>
                        </div>
                        <div className={styles.statItem}>
                            <span className={styles.statLabel}>Score:</span>
                            <span className={styles.statValue}>{result.score}</span>
                        </div>
                        <div className={styles.statItem}>
                            <span className={styles.statLabel}>Hits:</span>
                            <span className={styles.statValue}>{result.num_hits || 0}</span>
                        </div>
                        <div className={styles.statItem}>
                            <span className={styles.statLabel}>Significant:</span>
                            <span className={styles.statValue}>{result.num_significant || 0}</span>
                        </div>
                    </div>
                </div>
                
                {/* Show first few domains if available */}
                {hasDomains && !compact && (
                    <div className={styles.domainsPreview}>
                        <h5>Domains:</h5>
                        <div className={styles.domainsList}>
                            {result.domains.slice(0, 3).map((domain: any, domainIndex: number) => (
                                <div key={domainIndex} className={styles.domainItem}>
                                    <span className={styles.domainRange}>
                                        {domain.env_from}-{domain.env_to}
                                    </span>
                                    <span className={styles.domainScore}>
                                        {domain.bitscore?.toFixed(2) || 'N/A'}
                                    </span>
                                    <span className={styles.domainEvalue}>
                                        {domain.ievalue ? formatEValue(domain.ievalue) : 'N/A'}
                                    </span>
                                    <span className={`${styles.domainSignificance} ${domain.is_significant ? styles.significant : styles.notSignificant}`}>
                                        {domain.is_significant ? '✓' : '✗'}
                                    </span>
                                </div>
                            ))}
                            {result.domains.length > 3 && (
                                <div className={styles.moreDomains}>
                                    +{result.domains.length - 3} more domains
                                </div>
                            )}
                        </div>
                    </div>
                )}
                
                {/* Compact mode: just show key info */}
                {compact && (
                    <div className={styles.compactInfo}>
                        <span className={styles.compactEvalue}>E: {result.evalue}</span>
                        <span className={styles.compactScore}>Score: {result.score}</span>
                        <span className={styles.compactHits}>Hits: {result.num_hits || 0}</span>
                    </div>
                )}
            </div>
        );
    };
    
    // Render pagination
    const renderPagination = () => {
        if (!showPagination || totalPages <= 1) return null;
        
        const pageNumbers = [];
        const maxVisiblePages = compact ? 3 : 5;
        
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            pageNumbers.push(i);
        }
        
        return (
            <div className={styles.pagination}>
                <button
                    className={styles.pageButton}
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                >
                    ← Previous
                </button>
                
                {startPage > 1 && (
                    <>
                        <button
                            className={styles.pageButton}
                            onClick={() => handlePageChange(1)}
                        >
                            1
                        </button>
                        {startPage > 2 && <span className={styles.pageEllipsis}>...</span>}
                    </>
                )}
                
                {pageNumbers.map(pageNum => (
                    <button
                        key={pageNum}
                        className={`${styles.pageButton} ${pageNum === currentPage ? styles.active : ''}`}
                        onClick={() => handlePageChange(pageNum)}
                    >
                        {pageNum}
                    </button>
                ))}
                
                {endPage < totalPages && (
                    <>
                        {endPage < totalPages - 1 && <span className={styles.pageEllipsis}>...</span>}
                        <button
                            className={styles.pageButton}
                            onClick={() => handlePageChange(totalPages)}
                        >
                            {totalPages}
                        </button>
                    </>
                )}
                
                <button
                    className={styles.pageButton}
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                >
                    Next →
                </button>
            </div>
        );
    };
    
    // Render download section
    const renderDownloadSection = () => {
        if (!showDownload) return null;
        
        return (
            <div className={styles.downloadSection}>
                <h4>Download Results</h4>
                <div className={styles.downloadButtons}>
                    <button
                        className={styles.downloadButton}
                        onClick={() => handleDownload('csv')}
                    >
                        Download CSV
                    </button>
                    <button
                        className={styles.downloadButton}
                        onClick={() => handleDownload('json')}
                    >
                        Download JSON
                    </button>
                </div>
            </div>
        );
    };
    
    return (
        <div className={`${styles.pyhmmerResultsCore} ${compact ? styles.compact : ''} ${className}`}>
            {/* Results Summary */}
            {renderResultsSummary()}
            
            {/* Results List */}
            <div className={styles.resultsList}>
                {currentResults.map((result, index) => 
                    renderResultRow(result, startIndex + index)
                )}
            </div>
            
            {/* Pagination */}
            {renderPagination()}
            
            {/* Download Section */}
            {renderDownloadSection()}
            
            {/* Results Info */}
            <div className={styles.resultsInfo}>
                <p>
                    Showing {startIndex + 1}-{Math.min(endIndex, results.length)} of {results.length} results
                    {compact && ` (compact view)`}
                </p>
            </div>
        </div>
    );
};

export default PyhmmerResultsCore;
