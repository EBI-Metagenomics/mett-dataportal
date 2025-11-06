import React, {useState} from 'react';
import {PyhmmerSearchResult, PyhmmerService} from '../../../../services/pyhmmer';
import {PyhmmerResultsDisplay} from '@components/features';
import {saveJBrowseSearchToHistory, updateJBrowseSearchWithRealJobId} from '../../../../services/pyhmmer/pyhmmerHistoryService';
import styles from './PyhmmerFeaturePanel.module.scss';

interface PyhmmerFeaturePanelProps {
    proteinSequence: string;
    tempJobId?: string;
    isolateName?: string;
    product?: string;
    onClearResults?: () => void;
}

export const PyhmmerFeaturePanel: React.FC<PyhmmerFeaturePanelProps> = ({proteinSequence, tempJobId, isolateName, product, onClearResults}) => {
    const [isSearching, setIsSearching] = useState(false);
    const [results, setResults] = useState<PyhmmerSearchResult[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [hasSearched, setHasSearched] = useState(false);

    const handleSearch = async () => {
        if (isSearching) return;

        setIsSearching(true);
        setError(null);
        setResults([]);
        setHasSearched(true);

        try {
            // Use isolate-specific database if isolate name is provided
            let database = 'bu_pv_all'; // Default database
            if (isolateName) {
                // Extract isolate name from locus tag (e.g., "BU_ATCC8492_00001" -> "BU_ATCC8492")
                const isolateMatch = isolateName.match(/^([A-Z]{2}_[A-Z0-9]+)/);
                if (isolateMatch) {
                    const extractedIsolate = isolateMatch[1];
                    // Use a custom database identifier that we'll handle in the backend
                    database = `isolate_${extractedIsolate}`;
                }
            }
            
            // Save to history BEFORE executing search
            let historyTempJobId = tempJobId;
            if (!tempJobId) {
                const searchRequest = {
                    database: database,
                    threshold: 'E-value',
                    threshold_value: '0.01',
                    input: proteinSequence
                };
                
                const historyContext = {
                    source: 'jbrowse' as const,
                    locusTag: isolateName || 'Unknown',
                    product: product || '',
                    featureType: 'protein'
                };
                console.log('Saving to history with context:', historyContext);
                historyTempJobId = saveJBrowseSearchToHistory(searchRequest, historyContext);
            }
            
            // Execute the search and get real backend job ID
            const searchResponse = await PyhmmerService.executeSearch(proteinSequence, database);
            setResults(searchResponse.results);
            
            // Update the history with the real job ID from backend
            if (historyTempJobId && searchResponse.jobId) {
                updateJBrowseSearchWithRealJobId(historyTempJobId, searchResponse.jobId);
            }
        } catch (error: any) {
            setError(error.message || 'Search failed');
        } finally {
            setIsSearching(false);
        }
    };

    const handleClear = () => {
        setResults([]);
        setError(null);
        setHasSearched(false);
        // Notify parent to hide the panel
        if (onClearResults) {
            onClearResults();
        }
    };

    // Auto-start search when component mounts (panel is opened)
    React.useEffect(() => {
        // Trigger search automatically when PyHMMER panel opens
        if (proteinSequence && proteinSequence.length > 0) {
            handleSearch();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Only run on mount

    return (
        <div className={styles.featurePanel}>
            {/* Header */}
            <div className={styles.searchHeader}>
                <div className={styles.title}>🧬 PyHMMER Protein Search</div>
            </div>

            {/* Protein Info */}
            <div className={styles.searchInfo}>
                Protein sequence: <span className={styles.sequenceLength}>{proteinSequence.length} amino acids</span>
            </div>

            {/* Results Container */}
            <div className={styles.resultsContainer}>
                {isSearching && (
                    <div className={styles.loadingMessage}>
                        🔍 Searching... This may take a few minutes
                    </div>
                )}

                {error && (
                    <div className={styles.errorMessage}>
                        ❌ Error: {error}
                    </div>
                )}

                {!isSearching && !error && hasSearched && (
                    <PyhmmerResultsDisplay
                        results={results}
                        onClear={handleClear}
                    />
                )}
            </div>
        </div>
    );
};
