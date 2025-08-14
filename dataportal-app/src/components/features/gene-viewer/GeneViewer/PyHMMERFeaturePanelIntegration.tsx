import React, { useState, useEffect } from 'react';
import { PyhmmerService } from '../../../../services/pyhmmerService';

interface PyHMMERFeaturePanelIntegrationProps {
    feature: any;
    onResultsUpdate?: (results: any) => void;
}

interface PyHMMERResult {
    target_name: string;
    target_description?: string;
    evalue: number;
    score: number;
    bias: number;
    is_significant: boolean;
}

const PyHMMERFeaturePanelIntegration: React.FC<PyHMMERFeaturePanelIntegrationProps> = ({ 
    feature, 
    onResultsUpdate 
}) => {
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<PyHMMERResult[]>([]);
    const [searchError, setSearchError] = useState<string | null>(null);
    const [lastSearchedSequence, setLastSearchedSequence] = useState<string | null>(null);

    // Extract protein sequence from the feature
    const proteinSequence = feature?.get?.('protein_sequence') || 
                           feature?.protein_sequence ||
                           feature?.pyhmmerSearch?.proteinSequence;

    // Check if we already have results for this sequence
    const hasResults = searchResults.length > 0 && lastSearchedSequence === proteinSequence;

    useEffect(() => {
        if (onResultsUpdate && hasResults) {
            // Inject results into the feature data for JBrowse to display
            const resultsData = {
                pyhmmerResults: searchResults,
                pyhmmerSearchStatus: 'completed',
                pyhmmerResultsCount: searchResults.length,
                pyhmmerSignificantCount: searchResults.filter(r => r.is_significant).length
            };
            onResultsUpdate(resultsData);
        }
    }, [searchResults, hasResults, onResultsUpdate]);

    if (!proteinSequence) {
        return (
            <div style={{ 
                marginTop: 12, 
                padding: 8, 
                backgroundColor: '#f3f4f6', 
                border: '1px solid #d1d5db',
                borderRadius: 4 
            }}>
                <span style={{ fontSize: 12, color: '#6b7280' }}>
                    No protein sequence available for this feature
                </span>
            </div>
        );
    }

    const proteinLength = proteinSequence.length;

    async function runPyHMMERSearch() {
        try {
            setIsSearching(true);
            setSearchError(null);
            setSearchResults([]);

            // Convert to FASTA format
            const fastaSequence = `>${feature.get?.('Name') || feature.get?.('ID') || 'protein'}\n${proteinSequence}`;
            
            const searchRequest = {
                database: 'bu_all',
                threshold: 'evalue' as const,
                threshold_value: 0.01,
                input: fastaSequence,
                E: 0.01,
                domE: 0.01,
                incE: 0.01,
                incdomE: 0.01
            };

            console.log('Starting PyHMMER search from feature panel:', searchRequest);
            const response = await PyhmmerService.search(searchRequest);

            if (response.id) {
                console.log('PyHMMER job submitted from feature panel:', response.id);
                
                // Poll for results
                const results = await pollJobStatus(response.id);
                setSearchResults(results);
                setLastSearchedSequence(proteinSequence);
                
                console.log('PyHMMER search completed with results:', results);
            } else {
                setSearchError('Failed to submit search');
            }
        } catch (e: any) {
            console.error('PyHMMER search error from feature panel:', e);
            setSearchError(`Error: ${e.message || 'Search failed'}`);
        } finally {
            setIsSearching(false);
        }
    }

    // Poll job status for results
    const pollJobStatus = async (jobId: string): Promise<PyHMMERResult[]> => {
        const maxAttempts = 30;
        let attempts = 0;

        while (attempts < maxAttempts) {
            try {
                const jobDetails = await PyhmmerService.getJobDetails(jobId);
                const status = jobDetails.status;
                console.log(`Job status (attempt ${attempts + 1}):`, status);

                if (status === 'completed') {
                    const results = jobDetails.task?.result || [];
                    console.log('PyHMMER search completed:', results);
                    
                    if (Array.isArray(results)) {
                        return results.map((result: any) => ({
                            target_name: result.target_name || result.name || 'Unknown',
                            target_description: result.target_description || result.description,
                            evalue: result.evalue || result.e_value || 0,
                            score: result.score || result.bit_score || 0,
                            bias: result.bias || 0,
                            is_significant: result.is_significant || result.significant || false
                        }));
                    }
                    return [];
                } else if (status === 'failed') {
                    throw new Error('PyHMMER search failed');
                }

                await new Promise(resolve => setTimeout(resolve, 2000));
                attempts++;
            } catch (error) {
                console.error('Error polling job status:', error);
                throw error;
            }
        }
        throw new Error('PyHMMER search timed out');
    };

    // Format E-value for display
    const formatEValue = (evalue: number): string => {
        if (evalue < 1e-100) return '< 1e-100';
        if (evalue < 0.01) return evalue.toExponential(2);
        return evalue.toFixed(6);
    };

    // Format score for display
    const formatScore = (score: number): string => {
        return score.toFixed(1);
    };

    return (
        <div style={{ 
            marginTop: 12, 
            padding: 12, 
            backgroundColor: '#f0f9ff', 
            border: '1px solid #bae6fd',
            borderRadius: 6 
        }}>
            <div style={{ marginBottom: 8 }}>
                <strong style={{ color: '#0369a1' }}>🧬 PyHMMER Protein Search</strong>
            </div>
            
            <div style={{ marginBottom: 12, fontSize: 12, color: '#6b7280' }}>
                Protein sequence: <strong>{proteinLength} amino acids</strong>
            </div>

            {!hasResults && (
                <button 
                    disabled={isSearching} 
                    onClick={runPyHMMERSearch}
                    style={{
                        backgroundColor: isSearching ? '#9ca3af' : '#3b82f6',
                        color: 'white',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 500,
                        cursor: isSearching ? 'not-allowed' : 'pointer',
                        transition: 'all 0.2s'
                    }}
                >
                    {isSearching ? '🔍 Searching...' : '🔍 Search Protein Domains'}
                </button>
            )}

            {isSearching && (
                <div style={{ marginTop: 8, fontSize: 12, color: '#059669' }}>
                    🔍 Searching... This may take a few minutes
                </div>
            )}

            {searchError && (
                <div style={{ 
                    marginTop: 8, 
                    fontSize: 12, 
                    padding: 6,
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: 4,
                    color: '#dc2626'
                }}>
                    ❌ {searchError}
                </div>
            )}

            {hasResults && (
                <div style={{ marginTop: 12 }}>
                    <div style={{ 
                        marginBottom: 8, 
                        padding: '6px 8px', 
                        backgroundColor: '#ecfdf5', 
                        border: '1px solid #bbf7d0',
                        borderRadius: 4
                    }}>
                        <strong style={{ color: '#059669' }}>
                            ✅ Search Complete: {searchResults.length} results
                        </strong>
                        <div style={{ fontSize: 11, color: '#059669', marginTop: 4 }}>
                            Significant: {searchResults.filter(r => r.is_significant).length} | 
                            Total: {searchResults.length}
                        </div>
                    </div>

                    <div style={{ maxHeight: '200px', overflow: 'auto' }}>
                        {searchResults.slice(0, 5).map((result, index) => (
                            <div key={index} style={{
                                padding: '6px 8px',
                                marginBottom: '4px',
                                backgroundColor: result.is_significant ? '#f0fdf4' : '#fffbeb',
                                border: `1px solid ${result.is_significant ? '#bbf7d0' : '#fcd34d'}`,
                                borderRadius: 3,
                                fontSize: 11
                            }}>
                                <div style={{ fontWeight: 500, color: '#374151' }}>
                                    {result.target_name}
                                </div>
                                <div style={{ fontSize: 10, color: '#6b7280', marginTop: 2 }}>
                                    E-value: {formatEValue(result.evalue)} | Score: {formatScore(result.score)}
                                    {result.is_significant && (
                                        <span style={{ color: '#059669', marginLeft: 8 }}>✓ Significant</span>
                                    )}
                                </div>
                            </div>
                        ))}
                        {searchResults.length > 5 && (
                            <div style={{ fontSize: 10, color: '#6b7280', textAlign: 'center', padding: '4px' }}>
                                ... and {searchResults.length - 5} more results
                            </div>
                        )}
                    </div>

                    <button 
                        onClick={() => {
                            setSearchResults([]);
                            setLastSearchedSequence(null);
                        }}
                        style={{
                            marginTop: 8,
                            padding: '4px 8px',
                            backgroundColor: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: 3,
                            fontSize: 10,
                            cursor: 'pointer'
                        }}
                    >
                        Clear Results
                    </button>
                </div>
            )}
        </div>
    );
};

export default PyHMMERFeaturePanelIntegration;
