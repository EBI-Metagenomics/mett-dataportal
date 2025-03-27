import React from 'react';
import styles from '@components/pages/HomePage.module.scss';
import { GenomeMeta } from '../../interfaces/Genome';

interface TypeStrainsFilterProps {
    typeStrains: GenomeMeta[];
    selectedTypeStrains: string[];
    selectedSpecies: string[];
    onTypeStrainToggle: (isolate_name: string) => void;
}

const TypeStrainsFilter: React.FC<TypeStrainsFilterProps> = ({ typeStrains, selectedTypeStrains, selectedSpecies, onTypeStrainToggle }) => (
    <div className={styles.typeStrains}>
        {/*<h3>Type Strains</h3>*/}
        <h3 className={`vf-section-header__subheading ${styles.vfGeneSubHeading}`}>Type Strains</h3>
        <ul>
            {typeStrains.map((strain) => {
                const isStrainEnabled = selectedSpecies.length === 0 || selectedSpecies.includes(strain.species_acronym);

                return (
                    <li key={strain.isolate_name}>
                        <label>
                            <input
                                type="checkbox"
                                checked={selectedTypeStrains.includes(strain.isolate_name)}
                                disabled={!isStrainEnabled}
                                onChange={() => onTypeStrainToggle(strain.isolate_name)}
                            />
                            {strain.isolate_name}
                        </label>
                    </li>
                );
            })}
        </ul>
        <p>&nbsp;</p>
    </div>
);

export default TypeStrainsFilter;
