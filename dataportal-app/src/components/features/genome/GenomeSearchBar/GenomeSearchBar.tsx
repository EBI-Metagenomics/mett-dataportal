import React from 'react';

interface GenomeSearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

const GenomeSearchBar: React.FC<GenomeSearchBarProps> = ({ value, onChange }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <h3>Genome Search Bar (stub)</h3>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder="Search genomes..."
        style={{ padding: '0.5rem', width: '200px' }}
      />
    </div>
  );
};

export default GenomeSearchBar; 