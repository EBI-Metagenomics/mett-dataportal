import React from 'react';
import InputField from '../atoms/InputField';
import Button from '../atoms/Button';

interface SearchFormMoleculeProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
}

const SearchFormMolecule: React.FC<SearchFormMoleculeProps> = ({
                                                                   searchQuery,
                                                                   onSearchQueryChange,
                                                                   onSearchSubmit
                                                               }) => {
    return (
        <form onSubmit={(e) => {
            e.preventDefault();
            onSearchSubmit();
        }}>
            <InputField value={searchQuery} onChange={onSearchQueryChange} placeholder="Search genome..."/>
            <Button label="Search" type="submit"/>
        </form>
    );
};

export default SearchFormMolecule;
