import React from 'react';

interface SelectedGenomesProps {
    selectedGenomes: string[];
    onRemoveGenome: (genome: string) => void;
}

const SelectedGenomes: React.FC<SelectedGenomesProps> = ({selectedGenomes, onRemoveGenome}) => {
    return (
        <div className="selected-genomes">
            <h3>Selected Genomes</h3>
            <ul>
                {selectedGenomes.map((genome, index) => (
                    <li key={index} className="genome-chip">
                        {genome}
                        <button onClick={() => onRemoveGenome(genome)} aria-label="Remove Genome">
                            &times;
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default SelectedGenomes;
