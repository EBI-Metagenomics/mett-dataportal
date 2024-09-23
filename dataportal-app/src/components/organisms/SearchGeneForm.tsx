import React from 'react';
import SearchFormMolecule from '../molecules/SearchFormMolecule';

interface SearchGeneFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
}

const SearchGeneForm: React.FC<SearchGeneFormProps> = ({
                                                           searchQuery,
                                                           onSearchQueryChange,
                                                           onSearchSubmit
                                                       }) => {
    return (
        <section id="vf-tabs__section--1">
            <h2>Search Gene</h2>
            <SearchFormMolecule
                searchQuery={searchQuery}
                onSearchQueryChange={onSearchQueryChange}
                onSearchSubmit={onSearchSubmit}
            />
        </section>
    );
};

export default SearchGeneForm;
