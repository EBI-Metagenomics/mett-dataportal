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
        <div
            style={{
                display: 'flex',
                gap: '1.5rem',
                alignItems: 'center',
            }}
        >
            {speciesList.map((species) => (
                <label key={species.acronym} style={{display: 'flex', alignItems: 'center', gap: '0.4rem'}}>
                    <input
                        type="checkbox"
                        checked={selectedSpecies.includes(species.acronym)}
                        onChange={() => onSpeciesSelect(species.acronym)}
                        style={{
                            width: '16px',
                            height: '16px',
                            verticalAlign: 'middle',
                        }}
                    />
                    <i>{species.scientific_name}</i>
                </label>
            ))}
        </div>

    )
;

export default SpeciesFilter;
