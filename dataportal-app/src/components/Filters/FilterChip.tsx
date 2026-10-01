import React from 'react';
import styles from './ActiveFilters.module.scss';

export interface FilterChipProps {
    label: string;
    onRemove: () => void;
    removeAriaLabel?: string;
}

const FilterChip: React.FC<FilterChipProps> = ({label, onRemove, removeAriaLabel}) => (
    <span className={styles.chip}>
        <span className={styles.chipLabel}>{label}</span>
        <button
            type="button"
            className={styles.removeButton}
            onClick={onRemove}
            aria-label={removeAriaLabel || `Remove ${label}`}
        >
            ×
        </button>
    </span>
);

export default FilterChip;
