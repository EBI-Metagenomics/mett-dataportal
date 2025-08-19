import React from 'react';
import {PyhmmerSearchResult, PyhmmerService} from '../../../../services/pyhmmer';
import styles from './PyhmmerResultsDisplay.module.scss';

interface PyhmmerResultsDisplayProps {
    results: PyhmmerSearchResult[];
    onClear: () => void;
}

export const PyhmmerResultsDisplay: React.FC<PyhmmerResultsDisplayProps> = ({results, onClear}) => {
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

    // Show top 10 results
    const resultsToShow = results.slice(0, 10);

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
            {results.length > 10 && (
                <div className={styles.resultsFooter}>
                    ... and {results.length - 10} more results
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
