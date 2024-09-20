import React from 'react';
import InputField from '../atoms/InputField';
import Button from '../atoms/Button';

interface SearchInputProps {
  query: string;
  setQuery: (value: string) => void;
  onSearch: () => void;
}

const SearchInput: React.FC<SearchInputProps> = ({ query, setQuery, onSearch }) => {
  return (
    <div className="vf-form__item">
      <InputField value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search..." />
      {/* Pass the search text using the label prop */}
      <Button label="Search" onClick={onSearch} />
    </div>
  );
};

export default SearchInput;
