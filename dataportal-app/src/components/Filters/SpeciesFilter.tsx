import React from 'react';
import styles from '@components/pages/HomePage.module.scss';

interface Species {
    acronym: string;
    scientific_name: string;
}

interface SpeciesFilterProps {
    speciesList: Species[];
    selectedSpecies: string[];
    onSpeciesSelect: (acronym: string) => void;
}

const SpeciesFilter: React.FC<SpeciesFilterProps> = ({speciesList, selectedSpecies, onSpeciesSelect}) => (
    <div className={styles.speciesSection}>
        <h3>Species</h3>
        <ul>
            {speciesList.map(species => (
                <li key={species.acronym}>
                    <label>
                        <input
                            type="checkbox"
                            checked={selectedSpecies.includes(species.acronym)}
                            onChange={() => onSpeciesSelect(species.acronym)}
                        />
                        <i>{species.scientific_name}</i>
                    </label>
                </li>
            ))}
        </ul>
    </div>
);

export default SpeciesFilter;
