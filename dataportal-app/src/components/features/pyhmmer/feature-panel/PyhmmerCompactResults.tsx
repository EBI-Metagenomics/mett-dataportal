
import React from 'react';
import { PyhmmerResult } from '../../../../interfaces/Pyhmmer';
import { formatEValue, formatBitScore } from '../../../../utils/pyhmmer';
import styles from './PyhmmerCompactResults.module.scss';

interface PyhmmerCompactResultsProps {
    results: PyhmmerResult[];
    loading: boolean;
    error?: string;
    onResultClick?: (result: PyhmmerResult) => void;
    className?: string;
}

const PyhmmerCompactResults: React.FC<PyhmmerCompactResultsProps> = ({
    results = [],
    loading = false,
    error,
    onResultClick,
    className = ''
}) => {
    // Render loading state
    if (loading) {
        return (
            <div className={`${styles.pyhmmerCompactResults} ${className}`}>
                <div className={styles.loadingState}>
                    <div className={styles.spinner}></div>
                    <p>Searching...</p>
                </div>
            </div>
        );
    }

    // Render error state
    if (error) {
        return (
            <div className={`${styles.pyhmmerCompactResults} ${className}`}>
                <div className={styles.errorState}>
                    <div className={styles.errorIcon}>⚠️</div>
                    <h4>Search Error</h4>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    // Render no results state
    if (results.length === 0) {
        return (
            <div className={`${styles.pyhmmerCompactResults} ${className}`}>
                <div className={styles.noResultsState}>
                    <div className={styles.noResultsIcon}>🔍</div>
                    <h4>No Results</h4>
                    <p>Try adjusting your search parameters.</p>
                </div>
            </div>
        );
    }

    // Calculate summary statistics
    const totalGenes = results.length;
    const totalDomains = results.reduce((sum, result) => sum + (result.num_hits || 0), 0);
    const significantDomains = results.reduce((sum, result) => sum + (result.num_significant || 0), 0);

    // Render results summary
    const renderResultsSummary = () => (
        <div className={styles.resultsSummary}>
            <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Genes:</span>
                <span className={styles.summaryValue}>{totalGenes}</span>
            </div>
            <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Domains:</span>
                <span className={styles.summaryValue}>{totalDomains}</span>
            </div>
            <div className={styles.summaryItem}>
                <span className={styles.summaryLabel}>Significant:</span>
                <span className={styles.summaryValue}>{significantDomains}</span>
            </div>
        </div>
    );

    // Render individual result item
    const renderResultItem = (result: PyhmmerResult, index: number) => {
        const isSignificant = result.is_significant;
        const hasDomains = result.domains && result.domains.length > 0;

        return (
            <div
                key={`${result.target}-${index}`}
                className={`${styles.resultItem} ${isSignificant ? styles.significant : styles.notSignificant}`}
                onClick={() => onResultClick?.(result)}
            >
                {/* Target header */}
                <div className={styles.resultHeader}>
                    <h5 className={styles.targetName}>{result.target}</h5>
                    <div className={styles.significanceIndicator}>
                        {isSignificant ? '🟢' : '🟡'}
                    </div>
                </div>

                {/* Key statistics */}
                <div className={styles.resultStats}>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>E-value:</span>
                        <span className={styles.statValue}>{formatEValue(parseFloat(result.evalue))}</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>Score:</span>
                        <span className={styles.statValue}>{formatBitScore(parseFloat(result.score))}</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>Hits:</span>
                        <span className={styles.statValue}>{result.num_hits || 0}</span>
                    </div>
                    <div className={styles.statItem}>
                        <span className={styles.statLabel}>Sig:</span>
                        <span className={styles.statValue}>{result.num_significant || 0}</span>
                    </div>
                </div>

                {/* Description (if available) */}
                {result.description && result.description !== '-' && (
                    <div className={styles.description}>
                        {result.description}
                    </div>
                )}

                {/* Domain preview (if available) */}
                {hasDomains && (
                    <div className={styles.domainsPreview}>
                        <span className={styles.domainsLabel}>Domains:</span>
                        <div className={styles.domainsList}>
                            {result.domains?.slice(0, 2).map((domain, domainIndex) => (
                                <span key={domainIndex} className={styles.domainItem}>
                                    {domain.env_from}-{domain.env_to}
                                    <span className={styles.domainScore}>
                                        ({domain.bitscore?.toFixed(1)})
                                    </span>
                                </span>
                            ))}
                            {result.domains && Array.isArray(result.domains) && result.domains.length > 2 && (
                                <span className={styles.moreDomains}>
                                    +{result.domains.length - 2} more
                                </span>
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className={`${styles.pyhmmerCompactResults} ${className}`}>
            {/* Results Summary */}
            {renderResultsSummary()}

            {/* Results List */}
            <div className={styles.resultsList}>
                {results.map((result, index) => renderResultItem(result, index))}
            </div>

            {/* Results Info */}
            <div className={styles.resultsInfo}>
                <p>Showing {results.length} results</p>
            </div>
        </div>
    );
};

export default PyhmmerCompactResults;
