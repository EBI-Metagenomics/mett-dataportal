import React from 'react';
import styles from './SpeciesFilter.module.scss';

export interface SpeciesOption {
    acronym: string;
    name: string;
}

export interface SpeciesShortcut {
    id: string;
    label: string;
    species: string[];
}

interface SpeciesFilterProps {
    species: SpeciesOption[];
    shortcuts: SpeciesShortcut[];
    selected: string[];
    typeOnly: boolean;
    onSelectedChange: (acronyms: string[]) => void;
    onTypeOnlyChange: (typeOnly: boolean) => void;
}

const SpeciesFilter: React.FC<SpeciesFilterProps> = ({
    species,
    shortcuts,
    selected,
    typeOnly,
    onSelectedChange,
    onTypeOnlyChange,
}) => {
    const onMultiChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const acronyms = Array.from(event.target.selectedOptions).map(option => option.value);
        onSelectedChange(acronyms);
    };

    return (
        <div className={styles.formSection}>
            <div className={styles.label}>METT proteins</div>
            <div className={styles.shortcuts}>
                {shortcuts.map(shortcut => (
                    <button
                        key={shortcut.id}
                        type="button"
                        className={styles.shortcut}
                        onClick={() => onSelectedChange(shortcut.species)}
                    >
                        {shortcut.label}
                    </button>
                ))}
            </div>
            <label className={styles.fieldLabel} htmlFor="pyhmmer-species">
                Species
            </label>
            <select
                id="pyhmmer-species"
                className={styles.speciesSelect}
                multiple
                size={Math.min(8, Math.max(species.length, 3))}
                value={selected}
                onChange={onMultiChange}
            >
                {species.map(item => (
                    <option key={item.acronym} value={item.acronym}>
                        {item.name}
                    </option>
                ))}
            </select>
            <p className={styles.hint}>No selection searches all species.</p>
            <label className={styles.typeOnly}>
                <input
                    type="checkbox"
                    checked={typeOnly}
                    onChange={event => onTypeOnlyChange(event.target.checked)}
                />
                Type strains only
            </label>
        </div>
    );
};

export default SpeciesFilter;
