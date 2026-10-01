import React from 'react';
import GeneSearchInput from './GeneSearchInput';
import {GeneSuggestion} from '../../../../interfaces/Gene';
import styles from './GeneSearchForm.module.scss';

interface GeneSearchBarProps {
    searchInput: string;
    suggestions: GeneSuggestion[];
    onInputChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
    onSuggestionClick: (suggestion: GeneSuggestion) => void;
    onSuggestionsClear: () => void;
    onSearch: () => void;
    onClear: () => void;
    onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}

const GeneSearchBar: React.FC<GeneSearchBarProps> = ({
    searchInput,
    suggestions,
    onInputChange,
    onSuggestionClick,
    onSuggestionsClear,
    onSearch,
    onClear,
    onSubmit,
}) => (
    <form
        onSubmit={onSubmit}
        className="vf-form vf-form--search vf-form--search--responsive | vf-sidebar vf-sidebar--end"
    >
        <h2 className={`vf-section-header__subheading ${styles.vfGeneSubHeading}`}>Gene Search</h2>
        <div>
            <p />
        </div>
        <GeneSearchInput
            query={searchInput}
            onInputChange={onInputChange}
            suggestions={suggestions}
            onSuggestionClick={onSuggestionClick}
            onSuggestionsClear={onSuggestionsClear}
            onSearch={onSearch}
            onClear={onClear}
        />
    </form>
);

export default GeneSearchBar;
