import React, {useEffect, useState} from 'react';
import {GeneService} from '../../services/geneService';
import styles from './EssentialityFilter.module.scss';
import {GeneEssentialityTag} from '../../interfaces/Gene';
import {getIconForEssentiality} from '../../utils/appConstants';

interface EssentialityFilterProps {
    essentialityFilter: string[];
    onEssentialityFilterChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
    hasTypeStrains: boolean;
}

const EssentialityFilter: React.FC<EssentialityFilterProps> = ({
                                                                   essentialityFilter,
                                                                   onEssentialityFilterChange,
                                                                   hasTypeStrains,
                                                               }) => {
    const [essentialityTags, setEssentialityTags] = useState<GeneEssentialityTag[]>([]);

    useEffect(() => {
        const fetchEssentialityTags = async () => {
            try {
                const response = await GeneService.fetchEssentialityTags();
                setEssentialityTags(response);
            } catch (error) {
                console.error('Error fetching essentiality tags:', error);
            }
        };

        if (hasTypeStrains) {
            fetchEssentialityTags();
        }
    }, [hasTypeStrains]);

    return (
        <div className={styles.container}>
            <h3>Essentiality</h3>
            {essentialityTags.length === 0 && !hasTypeStrains && (
                <p className={styles.disabledMessage}>Filters available for type strains only</p>
            )}
            {essentialityTags.map((tag) => (
                <label key={tag.name} className={styles.filterItem}>
                    <input
                        type="checkbox"
                        value={tag.name}
                        checked={essentialityFilter.includes(tag.name)}
                        onChange={onEssentialityFilterChange}
                        disabled={!hasTypeStrains}
                    />
                    <span className={styles.icon}>{getIconForEssentiality(tag.name)}</span>
                    <span className={styles.label}>{tag.label}</span>
                </label>
            ))}
        </div>
    );
};

export default EssentialityFilter;
