import React from 'react';
import { useFilterStore } from '../../stores/filterStore';
import { useUrlState } from '../../hooks/useUrlState';
import { LoadingSpinner } from '../../components/shared';

const TestPage: React.FC = () => {
  const filterStore = useFilterStore();
  const { updateUrl, getParam, getParams } = useUrlState();
  
  const handleSpeciesToggle = (species: string) => {
    const currentSpecies = filterStore.selectedSpecies;
    const newSpecies = currentSpecies.includes(species)
      ? currentSpecies.filter(s => s !== species)
      : [...currentSpecies, species];
    
    filterStore.setSelectedSpecies(newSpecies);
  };

  const handleSearchChange = (query: string) => {
    filterStore.setGenomeSearchQuery(query);
  };

  const handleSortChange = (field: string) => {
    const newOrder = filterStore.genomeSortOrder === 'asc' ? 'desc' : 'asc';
    filterStore.setGenomeSortField(field);
    filterStore.setGenomeSortOrder(newOrder);
  };

  const resetFilters = () => {
    filterStore.resetFilters();
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Architecture Test Page</h1>
      
      <div style={{ marginBottom: '2rem' }}>
        <h2>Current URL Parameters</h2>
        <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '4px' }}>
          <p><strong>Species:</strong> {getParams('species').join(', ') || 'None'}</p>
          <p><strong>Search:</strong> {getParam('search') || 'None'}</p>
          <p><strong>Sort Field:</strong> {getParam('sortField') || 'species'}</p>
          <p><strong>Sort Order:</strong> {getParam('sortOrder') || 'asc'}</p>
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h2>Filter Store State</h2>
        <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '4px' }}>
          <p><strong>Selected Species:</strong> {filterStore.selectedSpecies.join(', ') || 'None'}</p>
          <p><strong>Search Query:</strong> {filterStore.genomeSearchQuery || 'None'}</p>
          <p><strong>Sort Field:</strong> {filterStore.genomeSortField}</p>
          <p><strong>Sort Order:</strong> {filterStore.genomeSortOrder}</p>
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h2>Test Controls</h2>
        
        <div style={{ marginBottom: '1rem' }}>
          <h3>Species Selection</h3>
          {['BU', 'PV', 'TEST'].map(species => (
            <button
              key={species}
              onClick={() => handleSpeciesToggle(species)}
              style={{
                margin: '0.25rem',
                padding: '0.5rem 1rem',
                background: filterStore.selectedSpecies.includes(species) ? '#007bff' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              {species}
            </button>
          ))}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Search Query</h3>
          <input
            type="text"
            value={filterStore.genomeSearchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Enter search query..."
            style={{ padding: '0.5rem', width: '200px' }}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <h3>Sorting</h3>
          <button
            onClick={() => handleSortChange('species')}
            style={{
              margin: '0.25rem',
              padding: '0.5rem 1rem',
              background: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Sort by Species ({filterStore.genomeSortField === 'species' ? filterStore.genomeSortOrder : 'asc'})
          </button>
          <button
            onClick={() => handleSortChange('isolate_name')}
            style={{
              margin: '0.25rem',
              padding: '0.5rem 1rem',
              background: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Sort by Name ({filterStore.genomeSortField === 'isolate_name' ? filterStore.genomeSortOrder : 'asc'})
          </button>
        </div>

        <div>
          <button
            onClick={resetFilters}
            style={{
              padding: '0.5rem 1rem',
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Reset All Filters
          </button>
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h2>Loading Spinner Test</h2>
        <div style={{ display: 'flex', gap: '2rem' }}>
          <div>
            <h4>Small</h4>
            <LoadingSpinner size="small" message="Loading..." />
          </div>
          <div>
            <h4>Medium</h4>
            <LoadingSpinner size="medium" message="Processing..." />
          </div>
          <div>
            <h4>Large</h4>
            <LoadingSpinner size="large" message="Fetching data..." />
          </div>
        </div>
      </div>

      <div>
        <h2>Shareable URL</h2>
        <p>Copy this URL to share your current filter state:</p>
        <div style={{ 
          background: '#f8f9fa', 
          padding: '1rem', 
          borderRadius: '4px',
          wordBreak: 'break-all',
          fontFamily: 'monospace',
          fontSize: '0.9rem'
        }}>
          {window.location.href}
        </div>
      </div>
    </div>
  );
};

export default TestPage; 