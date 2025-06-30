import React from 'react';

interface SelectedGenomesChipsProps {
  selectedGenomes: { isolate_name: string }[];
  onRemove: (isolateName: string) => void;
}

const SelectedGenomesChips: React.FC<SelectedGenomesChipsProps> = ({ selectedGenomes, onRemove }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <h3>Selected Genomes (stub)</h3>
      <div>
        {selectedGenomes.map(genome => (
          <span
            key={genome.isolate_name}
            style={{
              display: 'inline-block',
              background: '#007bff',
              color: 'white',
              padding: '0.25rem 0.75rem',
              borderRadius: '16px',
              margin: '0.25rem',
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
            onClick={() => onRemove(genome.isolate_name)}
          >
            {genome.isolate_name} ×
          </span>
        ))}
      </div>
    </div>
  );
};

export default SelectedGenomesChips; 