import React, { useState } from 'react';
import SearchInput from '../molecules/SearchInput';

interface SearchFormProps {
  onSearch: (species: string, genome: string) => void;
}

const SearchForm: React.FC<SearchFormProps> = ({ onSearch }) => {
  const [speciesQuery, setSpeciesQuery] = useState('');
  const [genomeQuery, setGenomeQuery] = useState('');

  const handleSearch = () => {
    onSearch(speciesQuery, genomeQuery);
  };

  return (
    <form className="vf-form" onSubmit={(e) => { e.preventDefault(); handleSearch(); }}>
      <SearchInput query={speciesQuery} setQuery={setSpeciesQuery} onSearch={handleSearch} />
      <SearchInput query={genomeQuery} setQuery={setGenomeQuery} onSearch={handleSearch} />
    </form>
  );
};

export default SearchForm;
