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
            const geneSuffix = isolateName?.match(/^(.*)_\d+$/);
            const isolate = geneSuffix?.[1] || '';
            if (!isolate) {
                throw new Error('Could not determine the isolate for this protein.');
            }

            // Save to history BEFORE executing search
            let historyTempJobId = tempJobId;
            if (!tempJobId) {
                const searchRequest = {
                    database: 'mett_proteins',
                    isolate,
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
            console.log('PyhmmerFeaturePanel: Starting search execution');
            const searchResponse = await PyhmmerService.executeSearch(proteinSequence, { isolate });
            console.log('PyhmmerFeaturePanel: Search completed, results:', searchResponse);
            console.log('PyhmmerFeaturePanel: Results count:', searchResponse.results?.length || 0);
            
            if (searchResponse.results && searchResponse.results.length > 0) {
                setResults(searchResponse.results);
                console.log('PyhmmerFeaturePanel: Results set successfully');
            } else {
                console.warn('PyhmmerFeaturePanel: No results returned from search');
                setResults([]);
            }
            
            // Update the history with the real job ID from backend
            if (historyTempJobId && searchResponse.jobId) {
                updateJBrowseSearchWithRealJobId(historyTempJobId, searchResponse.jobId);
            }
        } catch (error: any) {
            console.error('PyhmmerFeaturePanel: Search error:', error);
            console.error('PyhmmerFeaturePanel: Error details:', {
                message: error?.message,
                stack: error?.stack,
                response: error?.response,
            });
            setError(error?.message || error?.toString() || 'Search failed');
            setResults([]);
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
