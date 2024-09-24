// SelectedGenomes.tsx
import React from 'react';
import {Chip} from '@mui/material';
import styles from './SelectedGenomes.module.scss';

interface SelectedGenomesProps {
    selectedGenomes: string[];
    onRemoveGenome: (genome: string) => void;
}

const SelectedGenomes: React.FC<SelectedGenomesProps> = ({selectedGenomes, onRemoveGenome}) => {
    return (
        <div className={styles.selectedGenomesContainer}>
            <div style={{float: "left", width:"100%"}}>
                <h3>Selected Genomes</h3>
            </div>
            <div style={{float: "left"}}>
                {selectedGenomes.map((genome, index) => (
                    <Chip
                        key={index}
                        label={genome}
                        variant="outlined"
                        onDelete={() => onRemoveGenome(genome)}
                        className={styles.genomeChip}
                    />
                ))}
            </div>
        </div>
    );
};

export default SelectedGenomes;
