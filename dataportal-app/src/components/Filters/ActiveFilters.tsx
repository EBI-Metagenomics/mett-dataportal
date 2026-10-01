import React from 'react';
import FilterChip from './FilterChip';
import styles from './ActiveFilters.module.scss';

export interface ActiveFilterItem {
    id: string;
    label: string;
    onRemove: () => void;
}

interface ActiveFiltersProps {
    items: ActiveFilterItem[];
    onClearAll: () => void;
    title?: string;
}

const ActiveFilters: React.FC<ActiveFiltersProps> = ({
    items,
    onClearAll,
    title = 'Active filters',
}) => {
    if (items.length === 0) {
        return null;
    }

    return (
        <div className={styles.panel} aria-label={title}>
            <div className={styles.header}>
                <h3 className={styles.title}>
                    {title} ({items.length})
                </h3>
                <button type="button" className={styles.clearButton} onClick={onClearAll}>
                    Clear all
                </button>
            </div>
            <div className={styles.chips}>
                {items.map((item) => (
                    <FilterChip
                        key={item.id}
                        label={item.label}
                        onRemove={item.onRemove}
                        removeAriaLabel={`Remove ${item.label}`}
                    />
                ))}
            </div>
        </div>
    );
};

export default ActiveFilters;
