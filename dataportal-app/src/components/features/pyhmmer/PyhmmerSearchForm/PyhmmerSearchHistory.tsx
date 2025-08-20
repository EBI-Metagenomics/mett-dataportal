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
                                if (item.isJBrowseSearch) {
                                    // For JBrowse searches, just show the search details without fetching results
                                    console.log('JBrowse search selected:', item);
                                    // You could show a modal or info panel here instead
                                } else if (item.source === 'jbrowse' && !item.isJBrowseSearch) {
                                    // This was a JBrowse search that now has a real job ID - fetch results
                                    onSelect(item.jobId);
                                } else {
                                    // Regular search - fetch results
                                    onSelect(item.jobId);
                                }
                            }}
                        >
                            <div className={styles.itemContent}>
                                <div 
                                    className={styles.queryText}
                                    onMouseEnter={(e) => handleMouseEnter(e, item.query || item.input || 'Unknown')}
                                    onMouseLeave={handleMouseLeave}
                                >
                                    {item.source === 'jbrowse' && item.locusTag ? (
                                        <span className={styles.locusTagDescription}>{item.locusTag}</span>
                                    ) : (
                                        item.query || item.input || 'Unknown'
                                    )}
                                </div>
                                
                                {/* Show JBrowse context if available */}
                                {item.source === 'jbrowse' && (
                                    <div className={styles.jbrowseContext}>
                                        <span className={styles.jbrowseBadge}>JBrowse</span>
                                        {item.product && (
                                            <span className={styles.productInfo}>{item.product}</span>
                                        )}
                                        {item.geneName && item.geneName !== item.locusTag && (
                                            <span className={styles.geneName}>{item.geneName}</span>
                                        )}
                                        {item.genome && (
                                            <span className={styles.genomeInfo}>{item.genome}</span>
                                        )}
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