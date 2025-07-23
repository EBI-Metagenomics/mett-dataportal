import React from 'react';
import styles from './PyhmmerSearchHistory.module.scss';

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

const PyhmmerSearchHistory: React.FC<PyhmmerSearchHistoryProps> = ({history, onSelect, selectedJobId}) => {
    return (
        <div className={styles.historyContainer}>
            <h4 className={styles.historyTitle}>Past Searches</h4>
            {history.length === 0 && (
                <div className={styles.emptyState}>
                    No past searches
                </div>
            )}
            <ul className={styles.historyList}>
                {history.map(item => (
                    <li
                        key={item.jobId}
                        className={`${styles.historyItem} ${item.jobId === selectedJobId ? styles.selected : ''}`}
                        onClick={() => onSelect(item.jobId)}
                        title={item.query}
                    >
                        <div className={styles.queryText}>{item.query}</div>
                        <div className={styles.dateText}>{item.date}</div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default PyhmmerSearchHistory; 