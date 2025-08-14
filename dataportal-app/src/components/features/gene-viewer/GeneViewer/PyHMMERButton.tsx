import React, { useState } from 'react';
import { observer } from 'mobx-react';
import { getSession } from '@jbrowse/core/util';
import { PyhmmerService } from '../../../../services/pyhmmerService';

interface PyHMMERButtonProps {
    model: any;
}

const PyHMMERButton = observer(({ model }: PyHMMERButtonProps) => {
    const session = getSession(model);
    const feature = model?.featureData;
    const [isSearching, setIsSearching] = useState(false);
    const [message, setMessage] = useState<string | null>(null);

    if (!feature) return null;

    // Extract protein sequence from the feature
    const proteinSequence = feature?.get?.('protein_sequence') || 
                           feature?.protein_sequence ||
                           feature?.pyhmmerSearch?.proteinSequence;

    if (!proteinSequence) {
        return (
            <div style={{ marginTop: 12, padding: 8, backgroundColor: '#f3f4f6', borderRadius: 4 }}>
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
            setMessage(null);

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

            console.log('Starting PyHMMER search from JBrowse widget:', searchRequest);
            const response = await PyhmmerService.search(searchRequest);

            if (response.id) {
                setMessage(`🔍 Search submitted successfully! Job ID: ${response.id}`);
                
                // Optional: Open a results panel or redirect to search results
                // For now, we'll just show the success message
                console.log('PyHMMER job submitted from JBrowse:', response.id);
            } else {
                setMessage('❌ Failed to submit search');
            }
        } catch (e: any) {
            console.error('PyHMMER search error from JBrowse:', e);
            setMessage(`❌ Error: ${e.message || 'Search failed'}`);
        } finally {
            setIsSearching(false);
        }
    }

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

            {message && (
                <div style={{ 
                    marginTop: 8, 
                    fontSize: 12, 
                    padding: 6,
                    backgroundColor: message.includes('❌') ? '#fef2f2' : '#f0fdf4',
                    border: `1px solid ${message.includes('❌') ? '#fecaca' : '#bbf7d0'}`,
                    borderRadius: 4,
                    color: message.includes('❌') ? '#dc2626' : '#059669'
                }}>
                    {message}
                </div>
            )}
        </div>
    );
});

export default PyHMMERButton;
