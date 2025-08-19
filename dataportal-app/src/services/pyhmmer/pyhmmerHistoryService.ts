import { formatRelativeDate } from '../../utils/pyhmmer/formatting';
import { PYHMMER_CONSTANTS } from '../../utils/pyhmmer/pyhmmerConstants';

// Import SearchHistoryItem from types
import { SearchHistoryItem } from '../../utils/pyhmmer/types';

const HISTORY_KEY = 'pyhmmer_search_history';

/**
 * Load search history from localStorage
 */
export const loadSearchHistory = (): SearchHistoryItem[] => {
    try {
        console.log('=== LOAD SEARCH HISTORY ===');
        const existingHistory = localStorage.getItem(HISTORY_KEY);
        
        if (existingHistory) {
            const history = JSON.parse(existingHistory);
            console.log('Raw history from localStorage:', history.length, 'items');
            
            // Automatically clean up old items if cleanup is enabled
            let cleanedHistory = history;
            if (PYHMMER_CONSTANTS.HISTORY.CLEANUP_DAYS > 0) {
                const cleanupThresholdMs = PYHMMER_CONSTANTS.HISTORY.CLEANUP_DAYS * 24 * 60 * 60 * 1000;
                const cutoffTime = Date.now() - cleanupThresholdMs;
                cleanedHistory = history.filter((item: any) => {
                    const itemDate = new Date(item.dateCreated).getTime();
                    return itemDate > cutoffTime;
                });
                
                // Update localStorage if items were removed
                if (cleanedHistory.length < history.length) {
                    const removedCount = history.length - cleanedHistory.length;
                    console.log(`Automatically removed ${removedCount} old search history items (older than ${PYHMMER_CONSTANTS.HISTORY.CLEANUP_DAYS} days)`);
                    localStorage.setItem(HISTORY_KEY, JSON.stringify(cleanedHistory));
                }
            }
            
            // Format dates for display
            const formattedHistory = cleanedHistory.map((item: any) => ({
                ...item,
                date: formatRelativeDate(item.dateCreated),
                query: item.input // Map input to query for backward compatibility
            }));
            
            console.log('History state set with formatted dates');
            return formattedHistory;
        } else {
            console.log('No existing history found in localStorage');
            return [];
        }
    } catch (error) {
        console.error('Error loading search history:', error);
        return [];
    }
};

/**
 * Save search to history
 */
export const saveSearchToHistory = (jobId: string, searchRequest: any): void => {
    try {
        const historyItem = {
            jobId,
            dateCreated: new Date().toISOString(),
            date: undefined, // Will be formatted when loaded
            database: searchRequest.database,
            threshold: searchRequest.threshold,
            threshold_value: searchRequest.threshold_value,
            input: searchRequest.input,
            query: searchRequest.input, // Include query field for backward compatibility
        };

        const existingHistory = localStorage.getItem(HISTORY_KEY);
        let history = existingHistory ? JSON.parse(existingHistory) : [];
        
        // Add new item to beginning
        history.unshift(historyItem);
        
        // Keep only last 50 searches
        if (history.length > 50) {
            history = history.slice(0, 50);
        }
        
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        
    } catch (error) {
        console.error('Error saving search to history:', error);
    }
};

/**
 * Remove item from history
 */
export const removeFromHistory = (jobId: string): void => {
    try {
        const existingHistory = localStorage.getItem(HISTORY_KEY);
        if (existingHistory) {
            let history = JSON.parse(existingHistory);
            history = history.filter((item: SearchHistoryItem) => item.jobId !== jobId);
            localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
        }
    } catch (error) {
        console.error('Error removing item from history:', error);
    }
};

/**
 * Clear all history
 */
export const clearHistory = (): void => {
    try {
        localStorage.removeItem(HISTORY_KEY);
    } catch (error) {
        console.error('Error clearing history:', error);
    }
};

/**
 * Get history item by job ID
 */
export const getHistoryItem = (jobId: string): SearchHistoryItem | undefined => {
    try {
        const existingHistory = localStorage.getItem(HISTORY_KEY);
        if (existingHistory) {
            const history = JSON.parse(existingHistory);
            return history.find((item: SearchHistoryItem) => item.jobId === jobId);
        }
    } catch (error) {
        console.error('Error getting history item:', error);
    }
    return undefined;
};
