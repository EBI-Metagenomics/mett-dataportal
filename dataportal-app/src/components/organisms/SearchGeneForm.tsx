import React from 'react';
import SearchFormMolecule from '../molecules/SearchFormMolecule';

interface SearchGeneFormProps {
  speciesOptions: { value: string, label: string }[];
  selectedSpecies: string;
  onSpeciesChange: (value: string) => void;
  searchQuery: string;
  onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSearchSubmit: () => void;
}

const SearchGeneForm: React.FC<SearchGeneFormProps> = ({
  speciesOptions,
  selectedSpecies,
  onSpeciesChange,
  searchQuery,
  onSearchQueryChange,
  onSearchSubmit
}) => {
  return (
    <section id="vf-tabs__section--1">
      <h2>Search Gene</h2>
      <SearchFormMolecule
        speciesOptions={speciesOptions}
        selectedSpecies={selectedSpecies}
        onSpeciesChange={onSpeciesChange}
        searchQuery={searchQuery}
        onSearchQueryChange={onSearchQueryChange}
        onSearchSubmit={onSearchSubmit}
      />
    </section>
  );
};

export default SearchGeneForm;
