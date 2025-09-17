import React, {useState} from 'react';
import {PyhmmerSearchResult, PyhmmerService} from '../../../../services/pyhmmer';
import {PyhmmerResultsDisplay} from '@components/features';
import {updateJBrowseSearchWithRealJobId} from '../../../../services/pyhmmer/pyhmmerHistoryService';
import styles from './PyhmmerFeaturePanel.module.scss';

interface PyhmmerFeaturePanelProps {
    proteinSequence: string;
    tempJobId?: string;
    isolateName?: string;
}

export const PyhmmerFeaturePanel: React.FC<PyhmmerFeaturePanelProps> = ({proteinSequence, tempJobId, isolateName}) => {
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
            
            const searchResponse = await PyhmmerService.executeSearch(proteinSequence, database);
            setResults(searchResponse.results);
            
            // If this was a JBrowse search, update the history with the real job ID
            if (tempJobId && searchResponse.jobId) {
                updateJBrowseSearchWithRealJobId(tempJobId, searchResponse.jobId);
                console.log('Updated JBrowse search history with real job ID:', searchResponse.jobId);
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
    };

    // Clear results and auto-start search when protein sequence changes (new gene)
    React.useEffect(() => {
        // Clear previous results when navigating to a new gene
        setResults([]);
        setError(null);
        setHasSearched(false);
        
        // Start new search for the new protein sequence
        handleSearch();
    }, [proteinSequence]);

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
