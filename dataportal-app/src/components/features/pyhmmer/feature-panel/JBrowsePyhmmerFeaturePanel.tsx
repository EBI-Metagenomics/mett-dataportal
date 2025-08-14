import React, { useState, useEffect } from 'react';
import { PyhmmerResult } from '../../../../interfaces/Pyhmmer';
import { PyhmmerFeaturePanel } from './index';
import styles from './JBrowsePyhmmerFeaturePanel.module.scss';

interface JBrowsePyhmmerFeaturePanelProps {
    // JBrowse integration props
    feature?: any; // JBrowse feature object
    session?: any; // JBrowse session
    model?: any; // JBrowse model
    
    // PyHMMER props
    defaultSequence?: string;
    defaultDatabase?: string;
    defaultThreshold?: 'evalue' | 'bitscore';
    
    // Callbacks
    onResultClick?: (result: PyhmmerResult) => void;
    onSearchComplete?: (results: PyhmmerResult[]) => void;
    onError?: (error: string) => void;
    
    // Styling
    className?: string;
}

const JBrowsePyhmmerFeaturePanel: React.FC<JBrowsePyhmmerFeaturePanelProps> = ({
    feature,
    session,
    model,
    defaultSequence = '',
    defaultDatabase = 'bu_all',
    defaultThreshold = 'evalue',
    onResultClick,
    onSearchComplete,
    onError,
    className = ''
}) => {
    // State for JBrowse integration
    const [jbrowseContext, setJbrowseContext] = useState<any>(null);
    const [extractedSequence, setExtractedSequence] = useState<string>('');
    const [isExpanded, setIsExpanded] = useState(false);

    // Extract sequence from JBrowse feature if available
    useEffect(() => {
        if (feature) {
            const sequence = extractSequenceFromFeature(feature);
            if (sequence) {
                setExtractedSequence(sequence);
            }
        }
    }, [feature]);

    // Extract sequence from JBrowse feature
    const extractSequenceFromFeature = (jbrowseFeature: any): string => {
        try {
            // Try different common sequence field names
            const sequenceFields = [
                'sequence', 'seq', 'protein_sequence', 'protein_seq',
                'aa_sequence', 'amino_acid_sequence', 'translation'
            ];

            for (const field of sequenceFields) {
                if (jbrowseFeature[field] && typeof jbrowseFeature[field] === 'string') {
                    return jbrowseFeature[field];
                }
            }

            // Try nested fields
            if (jbrowseFeature.attributes) {
                for (const field of sequenceFields) {
                    if (jbrowseFeature.attributes[field] && typeof jbrowseFeature.attributes[field] === 'string') {
                        return jbrowseFeature.attributes[field];
                    }
                }
            }

            // Try subfeatures
            if (jbrowseFeature.subfeatures && Array.isArray(jbrowseFeature.subfeatures)) {
                for (const subfeature of jbrowseFeature.subfeatures) {
                    const subSequence = extractSequenceFromFeature(subfeature);
                    if (subSequence) {
                        return subSequence;
                    }
                }
            }

            return '';
        } catch (error) {
            console.warn('Error extracting sequence from JBrowse feature:', error);
            return '';
        }
    };

    // Handle result click with JBrowse context
    const handleResultClick = (result: PyhmmerResult) => {
        // If we have JBrowse context, we could highlight the result in the browser
        if (session && model) {
            try {
                // Try to highlight the result in JBrowse
                highlightResultInJBrowse(result, session, model);
            } catch (error) {
                console.warn('Could not highlight result in JBrowse:', error);
            }
        }

        // Call the original callback
        onResultClick?.(result);
    };

    // Highlight result in JBrowse (if possible)
    const highlightResultInJBrowse = (result: PyhmmerResult, jbrowseSession: any, jbrowseModel: any) => {
        try {
            // This is a placeholder for JBrowse-specific highlighting
            // The actual implementation would depend on JBrowse version and API
            console.log('Highlighting result in JBrowse:', result);
            
            // Example: try to find and highlight the target in the browser
            if (jbrowseModel && jbrowseModel.highlightFeature) {
                jbrowseModel.highlightFeature(result.target);
            }
        } catch (error) {
            console.warn('Error highlighting in JBrowse:', error);
        }
    };

    // Handle search completion with JBrowse context
    const handleSearchComplete = (results: PyhmmerResult[]) => {
        // Log search completion for JBrowse context
        if (feature) {
            console.log(`PyHMMER search completed for JBrowse feature: ${feature.id || feature.name || 'unknown'}`);
            console.log(`Found ${results.length} results`);
        }

        // Call the original callback
        onSearchComplete?.(results);
    };

    // Handle errors with JBrowse context
    const handleError = (error: string) => {
        // Log error with JBrowse context
        if (feature) {
            console.error(`PyHMMER error for JBrowse feature: ${feature.id || feature.name || 'unknown'}`, error);
        }

        // Call the original callback
        onError?.(error);
    };

    // Toggle expanded state
    const toggleExpanded = () => {
        setIsExpanded(!isExpanded);
    };

    // Get the sequence to use (extracted from feature or default)
    const sequenceToUse = extractedSequence || defaultSequence;

    return (
        <div className={`${styles.jbrowsePyhmmerFeaturePanel} ${className}`}>
            {/* JBrowse Context Header */}
            {feature && (
                <div className={styles.jbrowseHeader}>
                    <div className={styles.featureInfo}>
                        <h4 className={styles.featureTitle}>
                            {feature.name || feature.id || 'Selected Feature'}
                        </h4>
                        {feature.type && (
                            <span className={styles.featureType}>{feature.type}</span>
                        )}
                    </div>
                    
                    {/* Expand/Collapse Toggle */}
                    <button
                        className={styles.expandToggle}
                        onClick={toggleExpanded}
                        aria-label={isExpanded ? 'Collapse' : 'Expand'}
                    >
                        {isExpanded ? '−' : '+'}
                    </button>
                </div>
            )}

            {/* PyHMMER Feature Panel */}
            <div className={styles.pyhmmerContent}>
                <PyhmmerFeaturePanel
                    defaultSequence={sequenceToUse}
                    defaultDatabase={defaultDatabase}
                    defaultThreshold={defaultThreshold}
                    onResultClick={handleResultClick}
                    onSearchComplete={handleSearchComplete}
                    onError={handleError}
                />
            </div>

            {/* JBrowse Integration Footer */}
            <div className={styles.jbrowseFooter}>
                <p className={styles.integrationInfo}>
                    🔗 Integrated with JBrowse • Feature: {feature ? (feature.name || feature.id || 'Unknown') : 'None Selected'}
                </p>
            </div>
        </div>
    );
};

export default JBrowsePyhmmerFeaturePanel;
