import React from 'react';
import styles from '@components/pages/HomePage.module.scss';

interface Species {
    id: number;
    scientific_name: string;
}

interface SpeciesFilterProps {
    speciesList: Species[];
    selectedSpecies: number[];
    onSpeciesSelect: (speciesId: number) => void;
}

const SpeciesFilter: React.FC<SpeciesFilterProps> = ({speciesList, selectedSpecies, onSpeciesSelect}) => (
    <div className={styles.speciesSection}>
        <h3>Species</h3>
        <ul>
            {speciesList.map(species => (
                <li key={species.id}>
                    <label>
                        <input
                            type="checkbox"
                            checked={selectedSpecies.includes(species.id)}
                            onChange={() => onSpeciesSelect(species.id)}
                        />
                        <i>{species.scientific_name}</i>
                    </label>
                </li>
            ))}
        </ul>
    </div>
);

export default SpeciesFilter;
