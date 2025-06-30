import React from 'react';

interface TypeStrainFilterProps {
  selectedTypeStrains: string[];
  onToggle: (isolateName: string) => void;
  typeStrainList: { isolate_name: string; species_acronym: string }[];
}

const TypeStrainFilter: React.FC<TypeStrainFilterProps> = ({ selectedTypeStrains, onToggle, typeStrainList }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <h3>Type Strain Filter (stub)</h3>
      <div>
        {typeStrainList.map(strain => (
          <button
            key={strain.isolate_name}
            onClick={() => onToggle(strain.isolate_name)}
            style={{
              margin: '0.25rem',
              padding: '0.5rem 1rem',
              background: selectedTypeStrains.includes(strain.isolate_name) ? '#28a745' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            {strain.isolate_name}
          </button>
        ))}
      </div>
    </div>
  );
};

export default TypeStrainFilter; 