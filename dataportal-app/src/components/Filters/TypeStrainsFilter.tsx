import React from 'react';
import styles from '@components/pages/HomePage.module.scss';
import { GenomeMeta } from '../../interfaces/Genome';

interface TypeStrainsFilterProps {
    typeStrains: GenomeMeta[];
    selectedTypeStrains: number[];
    selectedSpecies: number[];
    onTypeStrainToggle: (strainId: number) => void;
}

const TypeStrainsFilter: React.FC<TypeStrainsFilterProps> = ({ typeStrains, selectedTypeStrains, selectedSpecies, onTypeStrainToggle }) => (
    <div className={styles.typeStrains}>
        <h3>Type Strains</h3>
        <ul>
            {typeStrains.map((strain) => {
                const isStrainEnabled = selectedSpecies.length === 0 || selectedSpecies.includes(strain.species.id);

                return (
                    <li key={strain.id}>
                        <label>
                            <input
                                type="checkbox"
                                checked={selectedTypeStrains.includes(strain.id)}
                                disabled={!isStrainEnabled}
                                onChange={() => onTypeStrainToggle(strain.id)}
                            />
                            {strain.isolate_name}
                        </label>
                    </li>
                );
            })}
        </ul>
    </div>
);

export default TypeStrainsFilter;
