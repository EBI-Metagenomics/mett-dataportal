import React from 'react';
import InputField from '../../atoms/InputField';
import Button from '../../atoms/Button';

interface GeneSearchInputProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
}

const GeneSearchInput: React.FC<GeneSearchInputProps> = ({
                                                                   searchQuery,
                                                                   onSearchQueryChange
                                                               }) => {
    return (
        <form onSubmit={(e) => {
            e.preventDefault();
        }}>
            <InputField value={searchQuery} onChange={onSearchQueryChange} placeholder="Search genome..."/>
            <Button label="Search" type="submit"/>
        </form>
    );
};

export default GeneSearchInput;
