import React from 'react';
import Dropdown from '../atoms/Dropdown';
import InputField from '../atoms/InputField';
import Button from '../atoms/Button';

interface SearchFormMoleculeProps {
  speciesOptions: { value: string, label: string }[];
  selectedSpecies: string;
  onSpeciesChange: (value: string) => void;
  searchQuery: string;
  onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSearchSubmit: () => void;
}

const SearchFormMolecule: React.FC<SearchFormMoleculeProps> = ({
  speciesOptions,
  selectedSpecies,
  onSpeciesChange,
  searchQuery,
  onSearchQueryChange,
  onSearchSubmit
}) => {
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSearchSubmit(); }}>
      <Dropdown options={speciesOptions} selectedValue={selectedSpecies} onChange={onSpeciesChange} />
      <InputField value={searchQuery} onChange={onSearchQueryChange} placeholder="Search genome..." />
      <Button label="Search" type="submit" />
    </form>
  );
};

export default SearchFormMolecule;
