import React, {useEffect, useRef} from 'react';
import styles from "@components/organisms/GeneSearch/GeneSearchInput.module.scss";

interface GeneSearchInputProps {
    query: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    suggestions: { gene_id: number; strain_name: string; gene_name: string }[];
    onSuggestionClick: (suggestion: { gene_id: number; strain_name: string; gene_name: string }) => void;
    onSuggestionsClear: () => void;
}

const GeneSearchInput: React.FC<GeneSearchInputProps> = ({
                                                             query,
                                                             onInputChange,
                                                             suggestions,
                                                             onSuggestionClick,
                                                             onSuggestionsClear
                                                         }) => {
    const wrapperRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                onSuggestionsClear();
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [onSuggestionsClear]);

    return (
        <div ref={wrapperRef} className={`vf-form__item ${styles.vfFormItem}`}>
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
                            {`${suggestion.strain_name} - (${suggestion.gene_name})`}
                        </div>
                    ))}
                </div>
            )}
            <button
                type="submit"
                className="vf-button vf-button--primary vf-button--sm"
                onClick={onSuggestionsClear}
            >
                <span className="vf-button__text">Search</span>
            </button>
        </div>
    );
};

export default GeneSearchInput;
