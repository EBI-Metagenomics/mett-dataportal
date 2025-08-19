import React, {useState} from 'react';
import {PyhmmerSearchResult, PyhmmerService} from '../../../../services/pyhmmer';
import {PyhmmerResultsDisplay} from '@components/features';
import styles from './PyhmmerFeaturePanel.module.scss';

interface PyhmmerFeaturePanelProps {
    proteinSequence: string;
}

export const PyhmmerFeaturePanel: React.FC<PyhmmerFeaturePanelProps> = ({proteinSequence}) => {
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
            const searchResults = await PyhmmerService.executeSearch(proteinSequence);
            setResults(searchResults);
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

    // Auto-start search when component mounts
    React.useEffect(() => {
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
