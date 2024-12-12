import React, { useEffect, useState } from 'react';
import { GeneService } from '../../../services/geneService';
import styles from './EssentialityFilter.module.scss';

interface EssentialityFilterProps {
    essentialityFilter: string[];
    onEssentialityFilterChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
    hasTypeStrains: boolean;
}

const EssentialityFilter: React.FC<EssentialityFilterProps> = ({ essentialityFilter, onEssentialityFilterChange, hasTypeStrains }) => {
    const [essentialityTags, setEssentialityTags] = useState<string[]>([]);

    useEffect(() => {
        const fetchEssentialityTags = async () => {
            try {
                const response = await GeneService.fetchEssentialityTags();
                setEssentialityTags(response.map((tag: any) => tag.name));
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
            {essentialityTags.length === 0 && !hasTypeStrains && <p className={styles.disabledMessage}>Filters available for type strains only</p>}
            {essentialityTags.map(tag => (
                <label key={tag} className={styles.filterItem}>
                    <input
                        type="checkbox"
                        value={tag}
                        checked={essentialityFilter.includes(tag)}
                        onChange={onEssentialityFilterChange}
                        disabled={!hasTypeStrains}
                    />
                    {tag}
                </label>
            ))}
        </div>
    );
};

export default EssentialityFilter;
