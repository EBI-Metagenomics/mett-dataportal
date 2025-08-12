import React, {useEffect, useState} from 'react';
import {PyhmmerDomain} from '../../../interfaces/Pyhmmer';
import {PyhmmerService} from '../../../services/pyhmmerService';
import AlignmentTable from '../AlignmentTable/AlignmentTable';
import LoadingSpinner from '../../shared/LoadingSpinner/LoadingSpinner';
import './AlignmentView.scss';

interface AlignmentViewProps {
    jobId: string;
    target: string;
}

export const AlignmentView: React.FC<AlignmentViewProps> = ({jobId, target}) => {
    const [domains, setDomains] = useState<PyhmmerDomain[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchDomains = async () => {
            try {
                console.log(`AlignmentView: Starting to fetch domains for jobId: ${jobId}, target: ${target}`);
                setLoading(true);
                setError(null);
                const domains = await PyhmmerService.getDomainsByTarget(jobId, target);
                console.log('AlignmentView: Received domains:', domains);
                console.log('AlignmentView: First domain identity:', domains[0]?.alignment_display?.identity);
                console.log('AlignmentView: First domain similarity:', domains[0]?.alignment_display?.similarity);
                setDomains(domains);
            } catch (err) {
                console.error('Error fetching domains:', err);
                setError(err instanceof Error ? err.message : 'Failed to load domain data');
            } finally {
                setLoading(false);
            }
        };

        if (jobId && target) {
            console.log(`AlignmentView: useEffect triggered with jobId: ${jobId}, target: ${target}`);
            fetchDomains();
        } else {
            console.log(`AlignmentView: useEffect skipped - missing jobId: ${jobId}, target: ${target}`);
        }
    }, [jobId, target]);

    if (loading) {
        return (
            <div className="alignment-view-loading">
                <LoadingSpinner size="medium" message="Loading domain details..."/>
            </div>
        );
    }

    if (error) {
        return (
            <div className="alignment-view-error">
                <div className="error-icon">⚠️</div>
                <div className="error-text">{error}</div>
            </div>
        );
    }

    if (!domains || domains.length === 0) {
        return (
            <div className="alignment-view-no-data">
                <div className="no-data-text">No domain information available for this target.</div>
            </div>
        );
    }

    return (
        <div className="alignment-view">
            <div className="alignment-view-header">
                <h4>Domain Details for {target}</h4>
                <span className="domain-count">{domains.length} domain(s) found</span>
            </div>
            <div className="alignment-view-content">
                {domains.map((domain, index) => (
                    <div key={`domain-${index}`} className="domain-section">
                        <div className="domain-header">
                            <span className="domain-number">Domain {index + 1}</span>
                            <span className="domain-score">Bit Score: {domain.bitscore.toFixed(1)}</span>
                            <span className={`domain-significance ${domain.is_significant ? 'significant' : 'insignificant'}`}>
                                {domain.is_significant ? '✓ Significant match' : '✗ Insignificant match'}
                            </span>
                        </div>
                        <AlignmentTable domain={domain}/>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AlignmentView; 