import React, {useState} from 'react';
import {PyhmmerSearchResult, PyhmmerService} from '../../../../services/pyhmmer';
import styles from './PyhmmerResultsDisplay.module.scss';

interface PyhmmerResultsDisplayProps {
    results: PyhmmerSearchResult[];
    onClear: () => void;
}

export const PyhmmerResultsDisplay: React.FC<PyhmmerResultsDisplayProps> = ({results, onClear}) => {
    const [visibleCount, setVisibleCount] = useState(10);
    const RESULTS_PER_PAGE = 10;

    if (!Array.isArray(results) || results.length === 0) {
        return (
            <div className={styles.noResultsMessage}>
                No results found
            </div>
        );
    }

    // Count significant results
    const significantCount = results.filter(result =>
        PyhmmerService.isResultSignificant(result)
    ).length;

    // Show results based on current visible count
    const resultsToShow = results.slice(0, visibleCount);
    
    const handleShowMore = () => {
        setVisibleCount((prev: number) => Math.min(prev + RESULTS_PER_PAGE, results.length));
    };
    
    const hasMoreResults = visibleCount < results.length;

    return (
        <div className={styles.resultsContainer}>
            {/* Header section */}
            <div className={styles.resultsHeader}>
                <div className={styles.title}>
                    ✅ Search Complete: {results.length} results
                </div>
                <div className={styles.summary}>
                    Significant: {significantCount} | Total: {results.length}
                </div>
            </div>

            {/* Results list */}
            <div className={styles.resultsList}>
                {resultsToShow.map((result, index) => {
                    const isSignificant = PyhmmerService.isResultSignificant(result);
                    const targetName = PyhmmerService.getTargetName(result);
                    const evalueFormatted = PyhmmerService.formatEvalue(result.evalue);
                    const scoreFormatted = PyhmmerService.formatScore(result.score);
                    const genomeViewerUrl = PyhmmerService.generateGenomeViewerUrl(targetName);

                    const resultClass = isSignificant ? styles.resultItem : `${styles.resultItem} ${styles.notSignificant}`;

                    return (
                        <div key={index} className={resultClass}>
                            <div className={styles.targetName}>
                                <a
                                    href={genomeViewerUrl}
                                    target="_blank"
                                    rel="noreferrer"
                                    className={styles.genomeViewerLink}
                                >
                                    {targetName}
                                </a>
                            </div>
                            <div className={styles.resultDetails}>
                                E-value: {evalueFormatted} |
                                Score: {scoreFormatted}
                                {isSignificant && (
                                    <span className={styles.significant}>✓ Significant</span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Footer section */}
            {hasMoreResults && (
                <div className={styles.resultsFooter}>
                    <span className={styles.resultsCount}>
                        Showing {visibleCount} of {results.length} results
                    </span>
                    <button
                        onClick={handleShowMore}
                        className={styles.showMoreButton}
                    >
                        Show More...
                        {/* Show More ({Math.min(RESULTS_PER_PAGE, results.length - visibleCount)}) */}
                    </button>
                </div>
            )}
            
            {!hasMoreResults && results.length > 10 && (
                <div className={styles.resultsFooter}>
                    <span className={styles.resultsCount}>
                        Showing all {results.length} results
                    </span>
                </div>
            )}

            {/* Clear button */}
            <button
                onClick={onClear}
                className={styles.clearButton}
            >
                Clear Results
            </button>
        </div>
    );
};
