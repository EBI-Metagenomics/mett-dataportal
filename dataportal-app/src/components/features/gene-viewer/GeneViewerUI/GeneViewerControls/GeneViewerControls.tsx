import React from 'react';
import {GenomeMeta} from '../../../../../interfaces/Genome';
import styles from './GeneViewerControls.module.scss';

interface GeneViewerControlsProps {
    genomeMeta: GenomeMeta | null;
    includeEssentiality: boolean;
    onEssentialityToggle: (include: boolean) => void;
}

const GeneViewerControls: React.FC<GeneViewerControlsProps> = ({
                                                                   genomeMeta,
                                                                   includeEssentiality,
                                                                   onEssentialityToggle,
                                                               }) => {
    if (!genomeMeta?.type_strain) {
        return null;
    }

    return (
        <div className={styles.essentialityToggleContainer}>
            <label htmlFor="toggleEssentiality" className={styles.essentialityLabel}>
                <input
                    type="checkbox"
                    id="toggleEssentiality"
                    checked={includeEssentiality}
                    onChange={() => onEssentialityToggle(!includeEssentiality)}
                    className={styles.essentialityCheckbox}
                />
                Include Essentiality in viewer
            </label>
        </div>
    );
};

export default GeneViewerControls; 