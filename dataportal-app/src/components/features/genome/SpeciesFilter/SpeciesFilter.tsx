import React from 'react';

interface SpeciesFilterProps {
  selectedSpecies: string[];
  onSelect: (species: string) => void;
  speciesList: { acronym: string; scientific_name: string; common_name: string; taxonomy_id: number }[];
}

const SpeciesFilter: React.FC<SpeciesFilterProps> = ({ selectedSpecies, onSelect, speciesList }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <h3>Species Filter (stub)</h3>
      <div>
        {speciesList.map(species => (
          <button
            key={species.acronym}
            onClick={() => onSelect(species.acronym)}
            style={{
              margin: '0.25rem',
              padding: '0.5rem 1rem',
              background: selectedSpecies.includes(species.acronym) ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {species.acronym}
          </button>
        ))}
      </div>
    </div>
  );
};

export default SpeciesFilter; 