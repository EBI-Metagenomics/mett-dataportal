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
    const allAcronyms = species.map(item => item.acronym);
    const allSelected = allAcronyms.length > 0 && allAcronyms.every(acronym => selected.includes(acronym));

    const toggleSpecies = (acronym: string) => {
        // From the full set, one click limits the search to that species.
        if (allSelected) {
            onSelectedChange([acronym]);
            return;
        }
        if (selected.includes(acronym)) {
            onSelectedChange(selected.filter(item => item !== acronym));
            return;
        }
        const next = [...selected, acronym];
        onSelectedChange(allAcronyms.every(item => next.includes(item)) ? allAcronyms : next);
    };

    const chooseShortcut = (shortcut: SpeciesShortcut) => {
        onSelectedChange(shortcut.species.length === 0 ? allAcronyms : shortcut.species);
    };

    const shortcutActive = (shortcut: SpeciesShortcut) => {
        if (shortcut.species.length === 0) {
            return allSelected;
        }
        return sameSpecies(selected, shortcut.species);
    };

    const summary = allSelected
        ? `All ${allAcronyms.length} species${typeOnly ? ' · type strains' : ''}`
        : selected.length === 0
            ? 'None selected'
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
                            className={`${styles.shortcut} ${shortcutActive(shortcut) ? styles.active : ''}`}
                            onClick={() => chooseShortcut(shortcut)}
                            aria-pressed={shortcutActive(shortcut)}
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
            {allSelected && (
                <p className={styles.hint}>Every species is included. Choose a shortcut, or a species, to limit the search.</p>
            )}
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
