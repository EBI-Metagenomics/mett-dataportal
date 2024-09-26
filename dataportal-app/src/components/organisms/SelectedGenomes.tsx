import React from 'react';
import {Chip} from '@mui/material';
import styles from './SelectedGenomes.module.scss';

interface SelectedGenomesProps {
    selectedGenomes: { id: number; name: string }[];
    onRemoveGenome: (genomeId: number) => void;
}

const SelectedGenomes: React.FC<SelectedGenomesProps> = ({selectedGenomes, onRemoveGenome}) => {
    return (
        <div className={styles.selectedGenomesContainer}>
            <div style={{float: "left", width: "100%"}}>
                <h3>Selected Genomes</h3>
            </div>
            <div style={{float: "left"}}>
                {selectedGenomes.map((genome) => (
                    <Chip
                        key={genome.id}
                        label={genome.name}
                        variant="outlined"
                        onDelete={() => onRemoveGenome(genome.id)}
                        className={styles.genomeChip}
                    />
                ))}
            </div>
        </div>
    );
};

export default SelectedGenomes;
