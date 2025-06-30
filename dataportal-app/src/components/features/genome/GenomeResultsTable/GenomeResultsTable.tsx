import React from 'react';

interface GenomeResultsTableProps {
  genomes: any[];
}

const GenomeResultsTable: React.FC<GenomeResultsTableProps> = ({ genomes }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <h3>Genome Results Table (stub)</h3>
      <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '4px' }}>
        <pre>{JSON.stringify(genomes, null, 2)}</pre>
      </div>
    </div>
  );
};

export default GenomeResultsTable; 