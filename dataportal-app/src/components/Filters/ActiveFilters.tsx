import React from 'react';
import styles from './ActiveFilters.module.scss';

export interface ActiveFilterItem {
    id: string;
    label: string;
    onRemove: () => void;
}

interface ActiveFiltersProps {
    items: ActiveFilterItem[];
    onClearAll: () => void;
}

const ActiveFilters: React.FC<ActiveFiltersProps> = ({items, onClearAll}) => {
    if (items.length === 0) {
        return null;
    }

    return (
        <div className={styles.panel} aria-label="Active filters">
            <div className={styles.header}>
                <h3 className={styles.title}>Active filters ({items.length})</h3>
                <button type="button" className={styles.clearButton} onClick={onClearAll}>
                    Clear all
                </button>
            </div>
            <div className={styles.chips}>
                {items.map((item) => (
                    <span key={item.id} className={styles.chip}>
                        <span className={styles.chipLabel}>{item.label}</span>
                        <button
                            type="button"
                            className={styles.removeButton}
                            onClick={item.onRemove}
                            aria-label={`Remove ${item.label}`}
                        >
                            ×
                        </button>
                    </span>
                ))}
            </div>
        </div>
    );
};

export default ActiveFilters;
