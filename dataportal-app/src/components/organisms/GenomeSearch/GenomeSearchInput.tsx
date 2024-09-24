import React from 'react';
import styles from "./GenomeSearchInput.module.scss";

interface GenomeSearchInputProps {
    query: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    suggestions: { strain_id: number; isolate_name: string; assembly_name: string }[];
    onSuggestionClick: (suggestion: { strain_id: number; isolate_name: string; assembly_name: string }) => void;
}

const GenomeSearchInput: React.FC<GenomeSearchInputProps> = ({
                                                                 query,
                                                                 onInputChange,
                                                                 suggestions,
                                                                 onSuggestionClick
                                                             }) => {
    return (

        <div className={`vf-form__item ${styles.vfFormItem}`}>
            <input
                type="search"
                value={query}
                onChange={onInputChange}
                placeholder="Search..."
                className="vf-form__input"
                autoComplete="off"
                aria-autocomplete="list"
                aria-controls="suggestions"
                role="combobox"
                aria-expanded={suggestions.length > 0}
            />
            {suggestions.length > 0 && (
                <div id="suggestions" className={`vf-dropdown__menu ${styles.vfDropdownMenu}`} role="listbox">
                    {suggestions.map((suggestion, index) => (
                        <div
                            key={index}
                            className={styles.suggestionItem}
                            onClick={() => onSuggestionClick(suggestion)}
                            role="option"
                        >
                            {`${suggestion.isolate_name} - (${suggestion.assembly_name})`}
                        </div>
                    ))}
                </div>
            )}
            <button type="submit" className="vf-button vf-button--primary vf-button--sm">
                <span className="vf-button__text">Search</span>
            </button>
        </div>

    );
};

export default GenomeSearchInput;
