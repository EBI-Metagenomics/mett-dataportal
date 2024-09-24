import React from 'react';
import GeneSearchInput from './GeneSearchInput';

interface GeneSearchFormProps {
    searchQuery: string;
    onSearchQueryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSearchSubmit: () => void;
}

const GeneSearchForm: React.FC<GeneSearchFormProps> = ({
                                                           searchQuery,
                                                           onSearchQueryChange,
                                                           onSearchSubmit
                                                       }) => {
    return (
        <section id="vf-tabs__section--1">
            <h2>Search Gene</h2>
            <GeneSearchInput
                searchQuery={searchQuery}
                onSearchQueryChange={onSearchQueryChange}
                onSearchSubmit={onSearchSubmit}
            />
        </section>
    );
};

export default GeneSearchForm;
