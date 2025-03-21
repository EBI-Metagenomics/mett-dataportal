import React from 'react';
import {Chip} from '@mui/material';
import styles from './SelectedGenomes.module.scss';
import {BaseGenome} from "../../interfaces/Genome";

interface SelectedGenomesProps {
    selectedGenomes: BaseGenome[];
    onRemoveGenome: (genomeId: string) => void;
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
                        key={genome.isolate_name}
                        label={genome.isolate_name}
                        variant="outlined"
                        onDelete={() => onRemoveGenome(genome.isolate_name)}
                        className={styles.genomeChip}
                    />
                ))}
            </div>
        </div>
    );
};

export default SelectedGenomes;
