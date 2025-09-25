import React from 'react';
import {GenomeMeta} from '../../../../../interfaces/Genome';
import styles from './GeneViewerControls.module.scss';

type ViewType = 'linear' | 'circular';

interface GeneViewerControlsProps {
    genomeMeta: GenomeMeta | null;
    includeEssentiality: boolean;
    viewType: ViewType;
    onEssentialityToggle?: (include: boolean) => void;
    onViewTypeChange?: (viewType: ViewType) => void;
}

const GeneViewerControls: React.FC<GeneViewerControlsProps> = ({
                                                                   genomeMeta,
                                                                   includeEssentiality,
                                                                   viewType,
                                                                   onEssentialityToggle,
                                                                   onViewTypeChange,
                                                               }) => {
    return (
        <div className={styles.controlsContainer}>
            {/* View Type Toggle */}
            <div className={styles.viewTypeToggleContainer}>
                <label htmlFor="viewTypeSelect" className={styles.viewTypeLabel}>
                    View Type:
                </label>
                <select
                    id="viewTypeSelect"
                    value={viewType}
                    onChange={(e) => onViewTypeChange?.(e.target.value as ViewType)}
                    className={styles.viewTypeSelect}
                >
                    <option value="linear">Linear View</option>
                    <option value="circular">Circular View</option>
                </select>
            </div>

            {/* Essentiality Toggle - only show for type strains */}
            {genomeMeta?.type_strain && (
                <div className={styles.essentialityToggleContainer}>
                    <label htmlFor="toggleEssentiality" className={styles.essentialityLabel}>
                        <input
                            type="checkbox"
                            id="toggleEssentiality"
                            checked={includeEssentiality}
                            onChange={() => onEssentialityToggle?.(!includeEssentiality)}
                            className={styles.essentialityCheckbox}
                        />
                        Include Essentiality in viewer
                    </label>
                </div>
            )}
        </div>
    );
};

export default GeneViewerControls; 