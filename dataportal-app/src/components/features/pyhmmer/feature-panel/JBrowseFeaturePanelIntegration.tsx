import React, { useState } from 'react';
import { JBrowsePyhmmerFeaturePanel } from './index';
import styles from './JBrowseFeaturePanelIntegration.module.scss';

// Mock JBrowse feature data
const mockJBrowseFeature = {
    id: 'BU_001',
    name: 'Hypothetical Protein BU_001',
    type: 'gene',
    start: 1000,
    end: 2000,
    strand: '+',
    sequence: 'MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWKRVMGVGDFT',
    attributes: {
        product: 'hypothetical protein',
        locus_tag: 'BU_001',
        protein_id: 'WP_123456789.1',
    },
};

const mockJBrowseSession = {
    model: {
        highlightFeature: (feature: any) => console.log('Highlighting feature:', feature),
    },
};

const mockJBrowseModel = {
    highlightFeature: (feature: any) => console.log('Highlighting feature:', feature),
};

const JBrowseFeaturePanelIntegration: React.FC = () => {
    const [selectedFeature, setSelectedFeature] = useState<any>(mockJBrowseFeature);
    const [panelWidth, setPanelWidth] = useState(400);
    const [panelPosition, setPanelPosition] = useState<'right' | 'left'>('right');
    const [showFeatureContext, setShowFeatureContext] = useState(true);

    const handleResultClick = (result: any) => {
        console.log('Result clicked:', result);
        alert(`Clicked on result: ${result.target} (Score: ${result.score})`);
    };

    const handleSearchComplete = (results: any[]) => {
        console.log('Search completed:', results);
        alert(`Search completed! Found ${results.length} results.`);
    };

    const handleError = (error: string) => {
        console.error('Search error:', error);
        alert(`Search error: ${error}`);
    };

    return (
        <div className={styles.integrationContainer}>
            {/* JBrowse Simulation Header */}
            <div className={styles.jbrowseHeader}>
                <h1>🧬 JBrowse Feature Panel Simulation</h1>
                <p>See how the PyHMMER feature panel will appear in JBrowse</p>
            </div>

            {/* JBrowse Main Content Area */}
            <div className={styles.jbrowseMain}>
                {/* Left Side - Genome Browser Simulation */}
                <div className={styles.genomeBrowser}>
                    <div className={styles.browserHeader}>
                        <h3>Genome Browser View</h3>
                        <div className={styles.browserControls}>
                            <button 
                                className={styles.featureButton}
                                onClick={() => setSelectedFeature(selectedFeature ? null : mockJBrowseFeature)}
                            >
                                {selectedFeature ? 'Hide' : 'Show'} Selected Feature
                            </button>
                        </div>
                    </div>
                    
                    <div className={styles.browserContent}>
                        <div className={styles.genomeTrack}>
                            <div className={styles.trackLabel}>Genome Assembly</div>
                            <div className={styles.trackContent}>
                                {selectedFeature && (
                                    <div className={styles.selectedFeature}>
                                        <div className={styles.featureMarker}>
                                            <span className={styles.featureName}>{selectedFeature.name}</span>
                                            <span className={styles.featureType}>{selectedFeature.type}</span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side - Feature Panel */}
                <div 
                    className={`${styles.featurePanel} ${styles[panelPosition]}`}
                    style={{ width: `${panelWidth}px` }}
                >
                    <div className={styles.panelHeader}>
                        <h3>Feature Panel</h3>
                        <div className={styles.panelControls}>
                            <select 
                                value={panelPosition} 
                                onChange={(e) => setPanelPosition(e.target.value as 'right' | 'left')}
                                className={styles.positionSelect}
                            >
                                <option value="right">Right</option>
                                <option value="left">Left</option>
                            </select>
                            <select 
                                value={panelWidth} 
                                onChange={(e) => setPanelWidth(Number(e.target.value))}
                                className={styles.widthSelect}
                            >
                                <option value={300}>300px</option>
                                <option value={400}>400px</option>
                                <option value={500}>500px</option>
                                <option value={600}>600px</option>
                            </select>
                        </div>
                    </div>

                    <div className={styles.panelContent}>
                        {showFeatureContext ? (
                            <JBrowsePyhmmerFeaturePanel
                                feature={selectedFeature}
                                session={mockJBrowseSession}
                                model={mockJBrowseModel}
                                defaultDatabase="bu_all"
                                onResultClick={handleResultClick}
                                onSearchComplete={handleSearchComplete}
                                onError={handleError}
                            />
                        ) : (
                            <div className={styles.noFeatureSelected}>
                                <p>No feature selected</p>
                                <p>Select a feature in the genome browser to see the PyHMMER panel</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Configuration Panel */}
            <div className={styles.configPanel}>
                <h3>Feature Panel Configuration</h3>
                <div className={styles.configControls}>
                    <label>
                        <input
                            type="checkbox"
                            checked={showFeatureContext}
                            onChange={(e) => setShowFeatureContext(e.target.checked)}
                        />
                        Show PyHMMER Feature Panel
                    </label>
                    
                    <div className={styles.configInfo}>
                        <p><strong>Current Settings:</strong></p>
                        <ul>
                            <li>Panel Position: {panelPosition}</li>
                            <li>Panel Width: {panelWidth}px</li>
                            <li>Feature Context: {showFeatureContext ? 'Enabled' : 'Disabled'}</li>
                            <li>Selected Feature: {selectedFeature ? selectedFeature.name : 'None'}</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Instructions */}
            <div className={styles.instructions}>
                <h3>How to Test:</h3>
                <ol>
                    <li><strong>Toggle Feature:</strong> Click "Show/Hide Selected Feature" to simulate selecting a gene in JBrowse</li>
                    <li><strong>Adjust Panel:</strong> Change position (left/right) and width to see how it adapts</li>
                    <li><strong>Test Integration:</strong> Try the PyHMMER search with the available protein sequence</li>
                    <li><strong>Responsive Test:</strong> Resize your browser window to see mobile/tablet behavior</li>
                    <li><strong>Check Console:</strong> Open browser console to see JBrowse integration logs</li>
                </ol>
            </div>
        </div>
    );
};

export default JBrowseFeaturePanelIntegration;
