import React from 'react';
import Input from '../atoms/Input';
import Button from '../atoms/Button';

interface SearchInputProps {
  query: string;
  setQuery: (query: string) => void;
  onSearch: () => void;
}

const SearchInput: React.FC<SearchInputProps> = ({ query, setQuery, onSearch }) => {
  return (
    <div className="vf-form__item">
      <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search..." />
      <Button onClick={onSearch}>Search</Button>
    </div>
  );
};

export default SearchInput;
