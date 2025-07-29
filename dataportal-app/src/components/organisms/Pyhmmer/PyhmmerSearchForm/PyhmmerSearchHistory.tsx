import React, { useState } from 'react';
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
    const [tooltip, setTooltip] = useState<{text: string, x: number, y: number} | null>(null);

    const handleMouseEnter = (e: React.MouseEvent, query: string) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setTooltip({
            text: query,
            x: rect.left,
            y: rect.top - 10
        });
    };

    const handleMouseLeave = () => {
        setTooltip(null);
    };

    return (
        <div className={styles.historyContainer}>
            <h4 className={styles.historyTitle}>Past Searches</h4>
            {history.length === 0 && (
                <div className={styles.emptyState}>
                    No past searches
                </div>
            )}
            <div className={styles.scrollContainer}>
                <ul className={styles.historyList}>
                    {history.map(item => (
                        <li
                            key={item.jobId}
                            className={`${styles.historyItem} ${item.jobId === selectedJobId ? styles.selected : ''}`}
                            onClick={() => onSelect(item.jobId)}
                        >
                            <div 
                                className={styles.queryText}
                                onMouseEnter={(e) => handleMouseEnter(e, item.query)}
                                onMouseLeave={handleMouseLeave}
                            >
                                {item.query}
                            </div>
                            <div className={styles.dateText}>{item.date}</div>
                        </li>
                    ))}
                </ul>
            </div>
            {tooltip && (
                <div 
                    className={styles.tooltip}
                    style={{
                        left: tooltip.x,
                        top: tooltip.y,
                    }}
                >
                    {tooltip.text}
                </div>
            )}
        </div>
    );
};

export default PyhmmerSearchHistory; 