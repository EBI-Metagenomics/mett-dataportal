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

const sameSpecies = (left: string[], right: string[]) => {
    if (left.length !== right.length) {
        return false;
    }
    const chosen = new Set(left);
    return right.every(acronym => chosen.has(acronym));
};

const SpeciesFilter: React.FC<SpeciesFilterProps> = ({
    species,
    shortcuts,
    selected,
    typeOnly,
    onSelectedChange,
    onTypeOnlyChange,
}) => {
    const toggleSpecies = (acronym: string) => {
        if (selected.includes(acronym)) {
            onSelectedChange(selected.filter(item => item !== acronym));
            return;
        }
        onSelectedChange([...selected, acronym]);
    };

    const summary = selected.length === 0
        ? 'All species'
        : `${selected.length} selected${typeOnly ? ' · type strains' : ''}`;

    return (
        <div className={styles.formSection}>
            <div className={styles.header}>
                <span className={styles.label}>Species</span>
                <span className={styles.summary}>{summary}</span>
            </div>
            <div className={styles.toolbar}>
                <div className={styles.shortcuts}>
                    {shortcuts.map(shortcut => (
                        <button
                            key={shortcut.id}
                            type="button"
                            className={`${styles.shortcut} ${sameSpecies(selected, shortcut.species) ? styles.active : ''}`}
                            onClick={() => onSelectedChange(shortcut.species)}
                            aria-pressed={sameSpecies(selected, shortcut.species)}
                        >
                            {shortcut.label}
                        </button>
                    ))}
                </div>
                <label className={styles.typeOnly}>
                    <input
                        type="checkbox"
                        checked={typeOnly}
                        onChange={event => onTypeOnlyChange(event.target.checked)}
                    />
                    Type strains only
                </label>
            </div>
            <div className={styles.speciesList} role="group" aria-label="Species">
                {species.map(item => {
                    const checked = selected.includes(item.acronym);
                    return (
                        <label
                            key={item.acronym}
                            className={`${styles.speciesOption} ${checked ? styles.checked : ''}`}
                        >
                            <input
                                type="checkbox"
                                checked={checked}
                                onChange={() => toggleSpecies(item.acronym)}
                            />
                            <span className={styles.acronym}>{item.acronym}</span>
                            <span className={styles.speciesName} title={item.name}>{item.name}</span>
                        </label>
                    );
                })}
            </div>
        </div>
    );
};

export default SpeciesFilter;
