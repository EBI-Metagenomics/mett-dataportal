import React from 'react';

interface GenomeSortControlsProps {
  sortField: string;
  sortOrder: 'asc' | 'desc';
  onSortChange: (field: string) => void;
}

const GenomeSortControls: React.FC<GenomeSortControlsProps> = ({ sortField, sortOrder, onSortChange }) => {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <h3>Genome Sort Controls (stub)</h3>
      <button
        onClick={() => onSortChange('species')}
        style={{ margin: '0.25rem', padding: '0.5rem 1rem' }}
      >
        Sort by Species ({sortField === 'species' ? sortOrder : 'asc'})
      </button>
      <button
        onClick={() => onSortChange('isolate_name')}
        style={{ margin: '0.25rem', padding: '0.5rem 1rem' }}
      >
        Sort by Name ({sortField === 'isolate_name' ? sortOrder : 'asc'})
      </button>
    </div>
  );
};

export default GenomeSortControls; 