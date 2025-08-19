import React, {useState} from 'react';
import {observer} from 'mobx-react';
import {PyhmmerCompactSearch} from '../../feature-panel';
import {PyhmmerCompactSearchRequest} from '../../../../../utils/pyhmmer';
import styles from './PyhmmerFeatureWidget.module.scss';
import {PYHMMER_DEFAULTS} from "../../../../../utils/pyhmmer/pyhmmerDefaults";

interface PyhmmerFeatureWidgetProps {
    model: any;
}

const PyhmmerFeatureWidget = observer(({model}: PyhmmerFeatureWidgetProps) => {
    const feature = model?.featureData;
    const [searchResult, setSearchResult] = useState<string | null>(null);

    if (!feature) return null;

    // Extract protein sequence from the feature
    const proteinSequence = feature?.get?.('protein_sequence') ||
        feature?.protein_sequence ||
        feature?.pyhmmerSearch?.proteinSequence;

    if (!proteinSequence) {
        return (
            <div className={styles.noSequenceMessage}>
                <span className={styles.noSequenceText}>
                    No protein sequence available for this feature
                </span>
            </div>
        );
    }

    // Handle search submission
    const handleSearch = (request: PyhmmerCompactSearchRequest) => {
        console.log('PyHMMER search submitted from JBrowse widget:', request);
        setSearchResult(`🔍 Search submitted successfully! Database: ${request.database}`);

        // Optional: Open a results panel or redirect to search results
        // For now, we'll just show the success message
    };

    // Handle search start
    const handleSearchStart = () => {
        setSearchResult(null);
        console.log('PyHMMER search starting from JBrowse widget');
    };

    // Handle search errors
    const handleError = (error: string) => {
        console.error('PyHMMER search error from JBrowse:', error);
        setSearchResult(`❌ Error: ${error}`);
    };

    return (
        <div className={styles.pyhmmerFeatureWidget}>
            <div className={styles.pyhmmerIntegration}>
                <PyhmmerCompactSearch
                    defaultSequence={proteinSequence}
                    defaultDatabase={PYHMMER_DEFAULTS.DATABASE}
                    onSearch={handleSearch}
                    onSearchStart={handleSearchStart}
                    onError={handleError}
                    className={styles.jbrowseWidget}
                />
            </div>

            {searchResult && (
                <div className={`${styles.searchResult} ${
                    searchResult.includes('❌') ? styles.searchResultError : styles.searchResultSuccess
                }`}>
                    {searchResult}
                </div>
            )}
        </div>
    );
});

export default PyhmmerFeatureWidget;
