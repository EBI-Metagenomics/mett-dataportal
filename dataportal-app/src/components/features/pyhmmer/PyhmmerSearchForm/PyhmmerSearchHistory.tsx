import React, { useState } from 'react';
import styles from './PyhmmerSearchHistory.module.scss';
import { SearchHistoryItem } from '../../../../utils/pyhmmer/types';

interface PyhmmerSearchHistoryProps {
    history: SearchHistoryItem[];
    onSelect: (jobId: string) => void;
    onDelete: (jobId: string) => void;
    selectedJobId?: string;
}

const PyhmmerSearchHistory: React.FC<PyhmmerSearchHistoryProps> = ({history, onSelect, onDelete, selectedJobId}) => {
    const [tooltip, setTooltip] = useState<{text: string, x: number, y: number} | null>(null);

    const handleMouseEnter = (e: React.MouseEvent, query: string) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setTooltip({
            text: query || 'Unknown',
            x: rect.left,
            y: rect.top - 10
        });
    };

    const handleMouseLeave = () => {
        setTooltip(null);
    };

    const handleDelete = (e: React.MouseEvent, jobId: string) => {
        e.stopPropagation(); 
        onDelete(jobId);
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
                            className={`${styles.historyItem} ${item.jobId === selectedJobId ? styles.selected : ''} ${item.isJBrowseSearch ? styles.jbrowseItem : ''}`}
                            onClick={() => {
                                // Always fetch results - all searches should have valid job IDs
                                onSelect(item.jobId);
                            }}
                        >
                            <div className={styles.itemContent}>
                                {/* Format: >locusTag pro... (truncated in display, full in tooltip) */}
                                {item.source === 'jbrowse' && item.locusTag ? (
                                    <div 
                                        className={styles.queryHeader}
                                        onMouseEnter={(e) => {
                                            // Show full details in tooltip: >locusTag product + sequence
                                            const fullText = `>${item.locusTag} ${item.product || ''}\n${item.input || ''}`;
                                            handleMouseEnter(e, fullText);
                                        }}
                                        onMouseLeave={handleMouseLeave}
                                    >
                                        {'>'}{item.locusTag} {item.product ? `${item.product.substring(0, 3)}...` : ''}
                                    </div>
                                ) : (
                                    <div 
                                        className={styles.queryText}
                                        onMouseEnter={(e) => handleMouseEnter(e, item.query || item.input || 'Unknown')}
                                        onMouseLeave={handleMouseLeave}
                                    >
                                        {item.query || item.input || 'Unknown'}
                                    </div>
                                )}
                                
                                <div className={styles.dateText}>{item.date}</div>
                            </div>
                            <button
                                className={styles.deleteButton}
                                onClick={(e) => handleDelete(e, item.jobId)}
                                title="Delete this search from history"
                                aria-label="Delete search"
                            >
                                ×
                            </button>
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