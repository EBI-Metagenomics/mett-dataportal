import React, { useState } from 'react';
import SearchFormMolecule from '../molecules/SearchFormMolecule';

interface SearchGenomeFormProps {
  speciesOptions: { value: string, label: string }[];
  selectedSpecies: string;
  onSpeciesChange: (value: string) => void;
  searchQuery: string;
  onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSearchSubmit: () => void;
  onGenomeSelect: (genome: string) => void; // New prop for handling genome selection
}

const SearchGenomeForm: React.FC<SearchGenomeFormProps> = ({
  speciesOptions,
  selectedSpecies,
  onSpeciesChange,
  searchQuery,
  onSearchQueryChange,
  onSearchSubmit,
  onGenomeSelect
}) => {
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const handleGenomeSelect = (genome: string) => {
    onGenomeSelect(genome); // Call parent handler to add the genome chip
  };

  return (
    <section id="vf-tabs__section--2">
      <h2>Search Genome</h2>
      <SearchFormMolecule
        speciesOptions={speciesOptions}
        selectedSpecies={selectedSpecies}
        onSpeciesChange={onSpeciesChange}
        searchQuery={searchQuery}
        onSearchQueryChange={onSearchQueryChange}
        onSearchSubmit={onSearchSubmit}
      />

      {/* Search Results Table */}
      <table>
        <thead>
          <tr>
            <th>Species</th>
            <th>Strain</th>
            <th>Assembly</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {searchResults.map(result => (
            <tr key={result.id}>
              <td>{result.species}</td>
              <td>{result.strain}</td>
              <td>{result.assembly}</td>
              <td>
                <button onClick={() => handleGenomeSelect(result.strain)}>Add</button> {/* Add button to select genome */}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
};

export default SearchGenomeForm;
