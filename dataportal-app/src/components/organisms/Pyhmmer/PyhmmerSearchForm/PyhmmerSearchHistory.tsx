import React from 'react';

export interface SearchHistoryItem {
    jobId: string;
    query: string;
    date: string;
}

interface PyhmmerSearchHistoryProps {
    history: SearchHistoryItem[];
    onSelect: (jobId: string) => void;
    selectedJobId?: string;
}

const PyhmmerSearchHistory: React.FC<PyhmmerSearchHistoryProps> = ({ history, onSelect, selectedJobId }) => {
    return (
        <div style={{ width: '100%', padding: '8px 0' }}>
            <h4 style={{ margin: '0 0 12px 0', fontWeight: 600 }}>Past Searches</h4>
            {history.length === 0 && <div style={{ color: '#888', fontSize: '0.95em' }}>No past searches</div>}
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {history.map(item => (
                    <li
                        key={item.jobId}
                        style={{
                            background: item.jobId === selectedJobId ? '#e3f2fd' : 'transparent',
                            borderRadius: 4,
                            marginBottom: 4,
                            padding: '8px 10px',
                            cursor: 'pointer',
                            fontWeight: item.jobId === selectedJobId ? 600 : 400,
                        }}
                        onClick={() => onSelect(item.jobId)}
                        title={item.query}
                    >
                        <div style={{ fontSize: '0.98em', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.query}</div>
                        <div style={{ fontSize: '0.85em', color: '#888' }}>{item.date}</div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default PyhmmerSearchHistory; 