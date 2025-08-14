import React, { useState, useEffect } from 'react';
import { PyhmmerService } from '../../../../services/pyhmmerService';
import { PyhmmerCompactSearchRequest } from '../../../../utils/pyhmmer';
import PyhmmerSearchCore from './PyhmmerSearchCore';
import PyhmmerResultsCore from './PyhmmerResultsCore';
import CollapsibleSection from './CollapsibleSection';
import styles from './PyhmmerFeaturePanel.module.scss';

interface PyhmmerFeaturePanelProps {
    // Initial values (can be pre-filled from genome browser context)
    defaultSequence?: string;
    defaultDatabase?: string;
    defaultThreshold?: 'evalue' | 'bitscore';
    
    // Configuration
    showAdvanced?: boolean;
    showDatabaseSelect?: boolean;
    showThresholdSelect?: boolean;
    maxResults?: number;
    
    // Callbacks
    onSearchStart?: () => void;
    onSearchComplete?: (results: any[]) => void;
    onError?: (error: string) => void;
    onResultClick?: (result: any) => void;
    onDownload?: (format: string) => void;
    
    // UI customization
    className?: string;
    compact?: boolean;
    
    // Section state
    defaultExpandedSections?: string[];
}

const PyhmmerFeaturePanel: React.FC<PyhmmerFeaturePanelProps> = ({
    defaultSequence = '',
    defaultDatabase = 'bu_all',
    defaultThreshold = 'evalue',
    showAdvanced = false,
    showDatabaseSelect = true,
    showThresholdSelect = true,
    maxResults = 10,
    onSearchStart,
    onSearchComplete,
    onError,
    onResultClick,
    onDownload,
    className = '',
    compact = true,
    defaultExpandedSections = ['search']
}) => {
    // State management
    const [expandedSections, setExpandedSections] = useState<Set<string>>(
        new Set(defaultExpandedSections)
    );
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | undefined>(undefined);
    const [currentJobId, setCurrentJobId] = useState<string | undefined>(undefined);
    
    // PyHMMER service instance
    const pyhmmerService = new PyhmmerService();
    
    // Handle section toggle
    const handleSectionToggle = (sectionId: string, expanded: boolean) => {
        const newExpandedSections = new Set(expandedSections);
        if (expanded) {
            newExpandedSections.add(sectionId);
        } else {
            newExpandedSections.delete(sectionId);
        }
        setExpandedSections(newExpandedSections);
    };
    
    // Handle search request
    const handleSearch = async (searchRequest: PyhmmerCompactSearchRequest) => {
        try {
            setLoading(true);
            setError(undefined);
            setSearchResults([]);
            
            // Call onSearchStart callback
            onSearchStart?.();
            
            // Start the search
            const jobId = await pyhmmerService.search(searchRequest);
            setCurrentJobId(jobId);
            
            // Poll for results
            const results = await pollForResults(jobId);
            
            // Update state
            setSearchResults(results);
            setCurrentJobId(undefined);
            
            // Call onSearchComplete callback
            onSearchComplete?.(results);
            
            // Auto-expand results section if we have results
            if (results.length > 0) {
                setExpandedSections(prev => new Set([...prev, 'results']));
            }
            
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Search failed';
            setError(errorMessage);
            onError?.(errorMessage);
        } finally {
            setLoading(false);
        }
    };
    
    // Poll for search results
    const pollForResults = async (jobId: string): Promise<any[]> => {
        const maxAttempts = 30; // 5 minutes with 10-second intervals
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const jobStatus = await pyhmmerService.getJobStatus(jobId);
                
                if (jobStatus.status === 'SUCCESS') {
                    // Get the results
                    const results = await pyhmmerService.getResults(jobId);
                    return results || [];
                } else if (jobStatus.status === 'FAILURE') {
                    throw new Error('Search job failed');
                }
                
                // Wait before next poll
                await new Promise(resolve => setTimeout(resolve, 10000));
                attempts++;
                
            } catch (error) {
                console.error('Error polling job status:', error);
                attempts++;
                
                if (attempts >= maxAttempts) {
                    throw new Error('Search timed out');
                }
            }
        }
        
        throw new Error('Search timed out');
    };
    
    // Handle result click
    const handleResultClick = (result: any) => {
        onResultClick?.(result);
    };
    
    // Handle download
    const handleDownload = (format: string) => {
        onDownload?.(format);
    };
    
    // Check if section is expanded
    const isSectionExpanded = (sectionId: string): boolean => {
        return expandedSections.has(sectionId);
    };
    
    // Render search section
    const renderSearchSection = () => (
        <CollapsibleSection
            title="PyHMMER Search"
            expanded={isSectionExpanded('search')}
            onToggle={(expanded) => handleSectionToggle('search', expanded)}
            className={compact ? styles.compact : ''}
        >
            <PyhmmerSearchCore
                defaultSequence={defaultSequence}
                defaultDatabase={defaultDatabase}
                defaultThreshold={defaultThreshold}
                showAdvanced={showAdvanced}
                showDatabaseSelect={showDatabaseSelect}
                showThresholdSelect={showThresholdSelect}
                onSearch={handleSearch}
                onSearchStart={() => setLoading(true)}
                onError={setError}
                compact={compact}
            />
        </CollapsibleSection>
    );
    
    // Render results section
    const renderResultsSection = () => {
        if (searchResults.length === 0 && !loading && !error) {
            return null; // Don't show results section if no results
        }
        
        return (
            <CollapsibleSection
                title={`Search Results ${searchResults.length > 0 ? `(${searchResults.length})` : ''}`}
                expanded={isSectionExpanded('results')}
                onToggle={(expanded) => handleSectionToggle('results', expanded)}
                className={compact ? styles.compact : ''}
            >
                <PyhmmerResultsCore
                    results={searchResults}
                    loading={loading}
                    error={error}
                    maxResults={maxResults}
                    showPagination={!compact}
                    showDownload={!compact}
                    onResultClick={handleResultClick}
                    onDownload={handleDownload}
                    compact={compact}
                />
            </CollapsibleSection>
        );
    };
    
    // Render advanced section (if enabled)
    const renderAdvancedSection = () => {
        if (!showAdvanced) return null;
        
        return (
            <CollapsibleSection
                title="Advanced Options"
                expanded={isSectionExpanded('advanced')}
                onToggle={(expanded) => handleSectionToggle('advanced', expanded)}
                className={compact ? styles.compact : ''}
            >
                <div className={styles.advancedInfo}>
                    <p>Advanced PyHMMER parameters are configured in the search form above.</p>
                    <p>You can customize E-value thresholds, bit scores, gap penalties, and matrix substitution options.</p>
                </div>
            </CollapsibleSection>
        );
    };
    
    // Render help section
    const renderHelpSection = () => (
        <CollapsibleSection
            title="Help & Information"
            expanded={isSectionExpanded('help')}
            onToggle={(expanded) => handleSectionToggle('help', expanded)}
            className={compact ? styles.compact : ''}
        >
            <div className={styles.helpContent}>
                <h4>How to use PyHMMER Search:</h4>
                <ol>
                    <li>Enter a protein sequence (FASTA format or plain text)</li>
                    <li>Select a database to search against</li>
                    <li>Choose threshold type (E-value or Bit Score)</li>
                    <li>Set your threshold value</li>
                    <li>Click "Search with PyHMMER"</li>
                </ol>
                
                <h4>Understanding Results:</h4>
                <ul>
                    <li><strong>E-value:</strong> Lower values indicate more significant matches</li>
                    <li><strong>Bit Score:</strong> Higher values indicate more significant matches</li>
                    <li><strong>Hits:</strong> Number of domains found for each gene</li>
                    <li><strong>Significant:</strong> Number of domains passing significance threshold</li>
                </ul>
                
                <h4>Tips:</h4>
                <ul>
                    <li>Use E-value &lt; 0.01 for highly significant matches</li>
                    <li>Use Bit Score &gt; 25 for reliable domain predictions</li>
                    <li>Longer sequences may take longer to process</li>
                    <li>Results are automatically saved to your search history</li>
                </ul>
            </div>
        </CollapsibleSection>
    );
    
    return (
        <div className={`${styles.pyhmmerFeaturePanel} ${compact ? styles.compact : ''} ${className}`}>
            {/* Header */}
            <div className={styles.panelHeader}>
                <h2 className={styles.panelTitle}>
                    <span className={styles.panelIcon}>🧬</span>
                    PyHMMER Protein Search
                </h2>
                {loading && (
                    <div className={styles.searchStatus}>
                        <div className={styles.statusSpinner}></div>
                        <span>Searching...</span>
                    </div>
                )}
            </div>
            
            {/* Content Sections */}
            <div className={styles.panelContent}>
                {/* Search Section */}
                {renderSearchSection()}
                
                {/* Results Section */}
                {renderResultsSection()}
                
                {/* Advanced Section */}
                {renderAdvancedSection()}
                
                {/* Help Section */}
                {renderHelpSection()}
            </div>
            
            {/* Footer */}
            <div className={styles.panelFooter}>
                <p className={styles.footerText}>
                    Powered by PyHMMER • Search protein databases for domain matches
                </p>
                {currentJobId && (
                    <p className={styles.jobInfo}>
                        Job ID: {currentJobId}
                    </p>
                )}
            </div>
        </div>
    );
};

export default PyhmmerFeaturePanel;
